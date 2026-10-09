export interface VoiceSettings {
  voiceName: string;
  rate: number;
  pitch: number;
  volume: number;
  autoSpeak: boolean;
  autoListen: boolean;
  inputLanguage: string;
  wakeWordEnabled: boolean;
  wakeWord: string;
}

export const defaultVoiceSettings: VoiceSettings = {
  voiceName: "auto",
  rate: 0.95,
  pitch: 1,
  volume: 1,
  autoSpeak: true,
  autoListen: true,
  inputLanguage: "en-US",
  wakeWordEnabled: false,
  wakeWord: "benris",
};

const STORAGE_KEY = "benris-voice-settings";
export const VOICE_SETTINGS_EVENT = "benris-voice-settings-changed";

export function loadVoiceSettings(): VoiceSettings {
  if (typeof window === "undefined") return defaultVoiceSettings;
  try {
    const stored = JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? "null") as Partial<VoiceSettings> | null;
    return { ...defaultVoiceSettings, ...stored };
  } catch {
    return defaultVoiceSettings;
  }
}

export function saveVoiceSettings(settings: VoiceSettings): void {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  window.dispatchEvent(new Event(VOICE_SETTINGS_EVENT));
}

export function pickNaturalVoice(voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice | null {
  const preferred = [
    "Samantha",
    "Ava",
    "Siri",
    "Google US English",
    "Microsoft Aria Online (Natural)",
    "Microsoft Jenny Online (Natural)",
    "Microsoft Guy Online (Natural)",
  ];
  const score = (voice: SpeechSynthesisVoice) => {
    const name = voice.name.toLowerCase();
    const index = preferred.findIndex((candidate) => voice.name === candidate || name.includes(candidate.toLowerCase()));
    let value = index >= 0 ? 100 - index : 0;
    if (/natural|neural|enhanced|premium/.test(name)) value += 40;
    if (name.includes("google")) value += 20;
    if (voice.lang.toLowerCase().startsWith("en-us")) value += 10;
    else if (voice.lang.toLowerCase().startsWith("en")) value += 5;
    if (voice.localService) value += 3;
    return value;
  };
  const english = voices.filter((voice) => voice.lang.toLowerCase().startsWith("en"));
  const pool = english.length ? english : voices;
  if (!pool.length) return null;
  return pool.reduce((best, voice) => (score(voice) > score(best) ? voice : best));
}

export function findVoice(voices: SpeechSynthesisVoice[], voiceName: string): SpeechSynthesisVoice | null {
  if (voiceName === "auto") return pickNaturalVoice(voices);
  return voices.find((voice) => voice.voiceURI === voiceName || voice.name === voiceName) ?? pickNaturalVoice(voices);
}

/** Returns the command after the wake word, or null when it was not spoken. */
export function matchWakeWord(transcript: string, wakeWord: string): string | null {
  const word = wakeWord.trim().toLowerCase();
  if (!word) return null;
  const spoken = transcript.trim().toLowerCase();
  const index = spoken.indexOf(word);
  if (index === -1) return null;
  return transcript
    .trim()
    .slice(index + word.length)
    .replace(/^[\s,.!?:;-]+/, "")
    .trim();
}