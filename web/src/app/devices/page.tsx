"use client";

import { useAgent } from "@/lib/agent-context";

export default function DevicesPage() {
  const { connected } = useAgent();

  return (
    <div className="content">
      <div className="page-head">
        <h1>Devices</h1>
        <p>Local runtimes connected to your Benris control plane.</p>
      </div>

      <div className="device-card">
        <span className="device-glyph">▣</span>
        <div>
          <h3>Kaif&apos;s MacBook</h3>
          <p>Local daemon · private network</p>
        </div>
        <span className={`device-state ${connected ? "online" : ""}`}>
          <i />
          {connected ? "Online" : "Offline"}
        </span>
      </div>

      <div className="spec-grid">
        <div className="spec">
          <small>Runtime</small>
          <strong>Local MacBook</strong>
        </div>
        <div className="spec">
          <small>Control plane</small>
          <strong>127.0.0.1:8000</strong>
        </div>
        <div className="spec">
          <small>Agent</small>
          <strong>Computer Agent</strong>
        </div>
        <div className="spec">
          <small>Connection</small>
          <strong>{connected ? "Healthy" : "Unreachable"}</strong>
        </div>
      </div>
    </div>
  );
}
