"use client";

import {
  FormEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { useAgent, terminalStates } from "@/lib/agent-context";
import {
  findVoice,
  loadVoiceSettings,
  matchWakeWord,
  VOICE_SETTINGS_EVENT,
  type VoiceSettings,
} from "@/lib/voice-settings";

type Phase = "idle" | "listening" | "thinking" | "speaking" | "error";

interface SpeechRecognitionAlternativeLike {
  transcript: string;
}
interface SpeechRecognitionResultLike {
  0: SpeechRecognitionAlternativeLike;
  isFinal: boolean;
  length: number;
}
interface SpeechRecognitionEventLike {
  resultIndex: number;
  results: ArrayLike<SpeechRecognitionResultLike>;
}
interface SpeechRecognitionLike {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
}
type SpeechRecognitionCtor = new () => SpeechRecognitionLike;

function getRecognitionCtor(): SpeechRecognitionCtor | null {
  if (typeof window === "undefined") return null;
  const win = window as unknown as {
    SpeechRecognition?: SpeechRecognitionCtor;
    webkitSpeechRecognition?: SpeechRecognitionCtor;
  };
  return win.SpeechRecognition ?? win.webkitSpeechRecognition ?? null;
}

const phaseLabels: Record<Phase, string> = {
  idle: "Tap the mic to talk",
  listening: "Listening…",
  thinking: "Thinking…",
  speaking: "Speaking…",
  error: "Voice input unavailable",
};

const orbLabels: Record<Phase, string> = {
  idle: "Start listening",
  listening: "Stop listening",
  thinking: "Thinking, please wait",
  speaking: "Interrupt response",
  error: "Try voice input again",
};

// Split into sentence-sized chunks so the engine applies natural intonation.
function splitIntoChunks(text: string): string[] {
  return text
    .replace(/\s+/g, " ")
    .match(/[^.!?]+[.!?]*/g)
    ?.map((part) => part.trim())
    .filter(Boolean) ?? [text.trim()];
}

export function VoiceMode({ onClose }: { onClose: () => void }) {
  const { submitTask, turns } = useAgent();
  const [phase, setPhase] = useState<Phase>("idle");
  const [transcript, setTranscript] = useState("");
  const [caption, setCaption] = useState("");
  const [supported, setSupported] = useState(true);
  const [typed, setTyped] = useState("");
  const [voiceSettings, setVoiceSettings] = useState<VoiceSettings>(loadVoiceSettings);

  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const orbRef = useRef<HTMLButtonElement>(null);
  const activeRef = useRef(true);
  const submittedIdRef = useRef<string | null>(null);
  const spokenIdRef = useRef<string | null>(null);
  const voiceRef = useRef<SpeechSynthesisVoice | null>(null);
  // True once the wake word was heard, so the next sentence runs as a command.
  const armedRef = useRef(false);
  const startListeningRef = useRef<() => void>(() => {});

  const stopRecognition = useCallback(() => {
    const recognition = recognitionRef.current;
    if (recognition) {
      recognition.onresult = null;
      recognition.onerror = null;
      recognition.onend = null;
      try {
        recognition.abort();
      } catch {
        /* ignore */
      }
      recognitionRef.current = null;
    }
  }, []);

  const speak = useCallback(
    (text: string) => {
      if (typeof window === "undefined" || !window.speechSynthesis) return;
      const synth = window.speechSynthesis;
      synth.cancel();
      const voice = voiceRef.current ?? findVoice(synth.getVoices(), voiceSettings.voiceName);
      const chunks = splitIntoChunks(text);
      setPhase("speaking");
      chunks.forEach((chunk, index) => {
        const utterance = new SpeechSynthesisUtterance(chunk);
        if (voice) {
          utterance.voice = voice;
          utterance.lang = voice.lang;
        }
        // Preserve the voice's native pitch and use a conversational cadence.
        utterance.rate = voiceSettings.rate;
        utterance.pitch = voiceSettings.pitch;
        utterance.volume = voiceSettings.volume;
        if (index === chunks.length - 1) {
          utterance.onend = () => {
            if (activeRef.current) setPhase("idle");
          };
          utterance.onerror = () => {
            if (activeRef.current) setPhase("idle");
          };
        }
        synth.speak(utterance);
      });
    },
    [voiceSettings],
  );

  const handleUtterance = useCallback(
    async (text: string) => {
      const value = text.trim();
      if (!value) return;
      armedRef.current = false;
      stopRecognition();
      setTranscript(value);
      setCaption("");
      setPhase("thinking");
      spokenIdRef.current = null;
      const id = await submitTask(value);
      submittedIdRef.current = id;
      if (!id) {
        setCaption("Could not reach the Benris daemon.");
        setPhase("error");
      }
    },
    [stopRecognition, submitTask],
  );

  const startListening = useCallback(() => {
    const Ctor = getRecognitionCtor();
    if (!Ctor) {
      setSupported(false);
      setPhase("idle");
      return;
    }
    stopRecognition();
    const recognition = new Ctor();
    const awaitingWakeWord = voiceSettings.wakeWordEnabled && !armedRef.current;
    recognition.lang = voiceSettings.inputLanguage;
    recognition.interimResults = true;
    recognition.continuous = awaitingWakeWord;
    recognition.onresult = (event) => {
      let interim = "";
      let final = "";
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const result = event.results[i];
        const text = result[0].transcript;
        if (result.isFinal) final += text;
        else interim += text;
      }
      setTranscript((final || interim).trim());
      if (!final.trim()) return;
      if (!voiceSettings.wakeWordEnabled || armedRef.current) {
        void handleUtterance(final);
        return;
      }
      const command = matchWakeWord(final, voiceSettings.wakeWord);
      if (command === null) return;
      if (command) {
        void handleUtterance(command);
      } else {
        armedRef.current = true;
        setCaption("Yes?");
      }
    };
    recognition.onerror = (event) => {
      if (event.error === "no-speech" || event.error === "aborted") return;
      setSupported(event.error !== "not-allowed" && event.error !== "service-not-allowed");
      setPhase("idle");
    };
    recognition.onend = () => {
      if (!activeRef.current || recognitionRef.current !== recognition) return;
      if (voiceSettings.wakeWordEnabled) {
        window.setTimeout(() => {
          if (activeRef.current && recognitionRef.current === recognition) {
            startListeningRef.current();
          }
        }, 250);
        return;
      }
      setPhase((current) => (current === "listening" ? "idle" : current));
    };
    recognitionRef.current = recognition;
    try {
      recognition.start();
      setTranscript("");
      setPhase("listening");
    } catch {
      setPhase("idle");
    }
  }, [handleUtterance, stopRecognition, voiceSettings.inputLanguage, voiceSettings.wakeWord, voiceSettings.wakeWordEnabled]);

  useEffect(() => {
    startListeningRef.current = startListening;
  }, [startListening]);

  // Re-arm wake-word listening once the agent has finished replying.
  useEffect(() => {
    if (!voiceSettings.wakeWordEnabled || phase !== "idle") return;
    const timer = window.setTimeout(() => startListeningRef.current(), 400);
    return () => window.clearTimeout(timer);
  }, [phase, voiceSettings.wakeWordEnabled]);

  // Watch the submitted turn and speak its response once ready.
  useEffect(() => {
    const id = submittedIdRef.current;
    if (!id || phase !== "thinking") return;
    const turn = turns.find((item) => item.id === id);
    if (!turn) return;
    if (turn.response) {
      setCaption(turn.response);
      if (spokenIdRef.current !== id) {
        spokenIdRef.current = id;
        if (voiceSettings.autoSpeak) speak(turn.response);
        else setPhase("idle");
      }
    } else if (terminalStates.has(turn.state)) {
      const message =
        turn.state === "cancelled"
          ? "The task was stopped."
          : "The agent could not complete that.";
      setCaption(message);
      if (spokenIdRef.current !== id) {
        spokenIdRef.current = id;
        if (voiceSettings.autoSpeak) speak(message);
        else setPhase("idle");
      }
    }
  }, [turns, phase, speak, voiceSettings.autoSpeak]);

  useEffect(() => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    const synth = window.speechSynthesis;
    const selectVoice = () => {
      voiceRef.current = findVoice(synth.getVoices(), voiceSettings.voiceName);
    };
    selectVoice();
    synth.addEventListener("voiceschanged", selectVoice);
    return () => synth.removeEventListener("voiceschanged", selectVoice);
  }, [voiceSettings.voiceName]);

  useEffect(() => {
    const syncSettings = () => setVoiceSettings(loadVoiceSettings());
    window.addEventListener("storage", syncSettings);
    window.addEventListener(VOICE_SETTINGS_EVENT, syncSettings);
    return () => {
      window.removeEventListener("storage", syncSettings);
      window.removeEventListener(VOICE_SETTINGS_EVENT, syncSettings);
    };
  }, []);

  // Start the session on mount; tear everything down on unmount.
  useEffect(() => {
    activeRef.current = true;
    orbRef.current?.focus();
    const timer = voiceSettings.autoListen
      ? window.setTimeout(() => startListening(), 0)
      : undefined;
    return () => {
      activeRef.current = false;
      if (timer) window.clearTimeout(timer);
      stopRecognition();
      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, [startListening, stopRecognition, voiceSettings.autoListen]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const toggleMic = useCallback(() => {
    if (phase === "listening") {
      stopRecognition();
      setPhase("idle");
    } else if (phase === "speaking") {
      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
      setPhase("idle");
    } else {
      startListening();
    }
  }, [phase, startListening, stopRecognition]);

  function onTypedSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = typed;
    setTyped("");
    void handleUtterance(value);
  }

  return (
    <div className="voice-overlay" role="dialog" aria-modal="true" aria-label="Voice mode">
      <div className="voice-top">
        <span className="voice-brand">
          <span className="voice-brand-mark">B</span> Voice mode
        </span>
        <button className="voice-close" onClick={onClose} aria-label="Close voice mode">
          ✕
        </button>
      </div>

      <div className="voice-stage">
        <p className="voice-transcript">{transcript || "\u00a0"}</p>

        <button
          ref={orbRef}
          className={`voice-orb ${phase}`}
          onClick={toggleMic}
          aria-label={orbLabels[phase]}
        >
          <span className="orb-core" />
          <span className="orb-ring r1" />
          <span className="orb-ring r2" />
          <span className="orb-ring r3" />
        </button>

        <p className="voice-phase" aria-live="polite">
          {!supported
            ? "Voice input isn’t available here — type below."
            : voiceSettings.wakeWordEnabled && phase === "listening"
              ? `Say “${voiceSettings.wakeWord}” then your request`
              : phaseLabels[phase]}
        </p>
        {caption && <p className="voice-caption" aria-live="polite">{caption}</p>}
      </div>

      <div className="voice-bottom">
        <form className="voice-type" onSubmit={onTypedSubmit}>
          <input
            value={typed}
            onChange={(event) => setTyped(event.target.value)}
            placeholder="Or type a message…"
            aria-label="Type a message"
          />
          <button type="submit" disabled={!typed.trim()} aria-label="Send">
            ↑
          </button>
        </form>
        <button
          className={`voice-mic ${phase === "listening" ? "active" : ""}`}
          onClick={toggleMic}
          aria-label="Toggle microphone"
        >
          {phase === "listening" ? "Stop" : phase === "speaking" ? "Interrupt" : "Talk"}
        </button>
      </div>
    </div>
  );
}
