"use client";

import { useEffect, useState } from "react";
import {
  defaultVoiceSettings,
  findVoice,
  loadVoiceSettings,
  saveVoiceSettings,
  type VoiceSettings,
} from "@/lib/voice-settings";

export default function SettingsPage() {
  const [settings, setSettings] = useState<VoiceSettings>(defaultVoiceSettings);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [previewing, setPreviewing] = useState(false);
  const selectedVoice = findVoice(voices, settings.voiceName);

  useEffect(() => {
    const syncSettings = () => setSettings(loadVoiceSettings());
    const timer = window.setTimeout(syncSettings, 0);
    if (!window.speechSynthesis) {
      return () => window.clearTimeout(timer);
    }
    const updateVoices = () => setVoices(window.speechSynthesis.getVoices());
    updateVoices();
    window.speechSynthesis.addEventListener("voiceschanged", updateVoices);
    return () => {
      window.clearTimeout(timer);
      window.speechSynthesis.cancel();
      window.speechSynthesis.removeEventListener("voiceschanged", updateVoices);
    };
  }, []);

  function update(next: Partial<VoiceSettings>) {
    const value = { ...settings, ...next };
    setSettings(value);
    saveVoiceSettings(value);
  }

  function previewVoice() {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const voice = findVoice(voices, settings.voiceName);
    const utterance = new SpeechSynthesisUtterance(
      "Hi, I’m Benris. I’ll keep the conversation clear and natural.",
    );
    if (voice) {
      utterance.voice = voice;
      utterance.lang = voice.lang;
    }
    utterance.rate = settings.rate;
    utterance.pitch = settings.pitch;
    utterance.volume = settings.volume;
    utterance.onstart = () => setPreviewing(true);
    utterance.onend = () => setPreviewing(false);
    utterance.onerror = () => setPreviewing(false);
    window.speechSynthesis.speak(utterance);
  }

  function resetVoice() {
    setSettings(defaultVoiceSettings);
    saveVoiceSettings(defaultVoiceSettings);
  }

  return (
    <div className="content settings-page">
      <div className="page-head">
        <h1>Settings</h1>
        <p>Shape how Benris sounds, listens, and responds.</p>
      </div>

      <section className="settings-section">
        <div className="settings-section-head">
          <div>
            <span className="section-kicker">Voice</span>
            <h2>Make it sound like you</h2>
            <p>These preferences apply to voice mode on this browser.</p>
          </div>
          <button className="preview-btn" onClick={previewVoice} disabled={previewing || !voices.length}>
            {previewing ? "Playing…" : "▶ Preview"}
          </button>
        </div>

        <div className="settings-fields">
          <label className="settings-field voice-select-field">
            <span>Voice</span>
            <select
              value={settings.voiceName === "auto" ? "auto" : selectedVoice?.voiceURI ?? "auto"}
              onChange={(event) => update({ voiceName: event.target.value })}
            >
              <option value="auto">Automatic · best available</option>
              {voices
                .filter((voice) => voice.lang.toLowerCase().startsWith("en"))
                .map((voice) => (
                  <option value={voice.voiceURI} key={voice.voiceURI}>
                    {voice.name} · {voice.lang}
                  </option>
                ))}
            </select>
            <small>
              {voices.length
                ? `${voices.length} voices available`
                : "Voices appear when your browser finishes loading them"}
            </small>
          </label>

          <label className="settings-field">
            <span>Microphone language</span>
            <select value={settings.inputLanguage} onChange={(event) => update({ inputLanguage: event.target.value })}>
              <option value="en-US">English · United States</option>
              <option value="en-GB">English · United Kingdom</option>
              <option value="en-IN">English · India</option>
              <option value="en-AU">English · Australia</option>
            </select>
            <small>Improves recognition for your accent and vocabulary.</small>
          </label>

          <label className="settings-field">
            <span className="range-label"><span>Speaking pace</span><output>{settings.rate.toFixed(2)}×</output></span>
            <input type="range" min="0.7" max="1.2" step="0.05" value={settings.rate} onChange={(event) => update({ rate: Number(event.target.value) })} />
            <small>Slower pacing leaves more room for natural pauses.</small>
          </label>

          <label className="settings-field">
            <span className="range-label"><span>Pitch</span><output>{settings.pitch.toFixed(1)}</output></span>
            <input type="range" min="0.7" max="1.3" step="0.05" value={settings.pitch} onChange={(event) => update({ pitch: Number(event.target.value) })} />
            <small>Keep this near 1.0 for the voice’s native character.</small>
          </label>

          <label className="settings-field">
            <span className="range-label"><span>Volume</span><output>{Math.round(settings.volume * 100)}%</output></span>
            <input type="range" min="0.2" max="1" step="0.05" value={settings.volume} onChange={(event) => update({ volume: Number(event.target.value) })} />
          </label>
        </div>
      </section>

      <section className="settings-section">
        <div className="settings-section-head compact">
          <div>
            <span className="section-kicker">Behavior</span>
            <h2>Conversation defaults</h2>
          </div>
        </div>
        <label className="toggle-row">
          <span>
            <strong>Speak agent replies</strong>
            <small>Read each completed response aloud in voice mode.</small>
          </span>
          <input type="checkbox" checked={settings.autoSpeak} onChange={(event) => update({ autoSpeak: event.target.checked })} />
        </label>
        <label className="toggle-row">
          <span>
            <strong>Listen when voice mode opens</strong>
            <small>Start the microphone without waiting for another tap.</small>
          </span>
          <input type="checkbox" checked={settings.autoListen} onChange={(event) => update({ autoListen: event.target.checked })} />
        </label>
        <label className="toggle-row">
          <span>
            <strong>Require an action word</strong>
            <small>Keep listening quietly and only act after you say the trigger phrase.</small>
          </span>
          <input type="checkbox" checked={settings.wakeWordEnabled} onChange={(event) => update({ wakeWordEnabled: event.target.checked })} />
        </label>
        {settings.wakeWordEnabled && (
          <label className="settings-field wake-word-field">
            <span>Action word</span>
            <input
              type="text"
              value={settings.wakeWord}
              maxLength={32}
              placeholder="benris"
              onChange={(event) => update({ wakeWord: event.target.value })}
            />
            <small>
              Say “{settings.wakeWord.trim() || "benris"}, play some music”, or say it alone and
              Benris will wait for your request.
            </small>
          </label>
        )}
      </section>

      <div className="settings-footer">
        <span>Saved automatically on this device.</span>
        <button className="text-btn" onClick={resetVoice}>Reset voice settings</button>
      </div>
    </div>
  );
}