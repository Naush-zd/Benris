"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAgent, statusLabels } from "@/lib/agent-context";

const navItems = [
  { href: "/", label: "Console", icon: "◈" },
  { href: "/activity", label: "Activity", icon: "⌁" },
  { href: "/policies", label: "Policies", icon: "◇" },
  { href: "/devices", label: "Devices", icon: "▣" },
  { href: "/settings", label: "Settings", icon: "⚙" },
];

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const { turns, reset, connected } = useAgent();
  const recent = [...turns].reverse().slice(0, 8);

  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        <Link href="/" className="brand" onClick={onNavigate}>
          <span className="brand-mark">B</span>
          <span className="brand-name">Benris</span>
        </Link>

        <Link href="/" className="new-task" onClick={() => { reset(); onNavigate?.(); }}>
          <span>+</span> New task
        </Link>

        <nav className="nav" aria-label="Primary navigation">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onNavigate}
                className={`nav-item ${active ? "active" : ""}`}
              >
                <span className="nav-icon">{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="recent">
          <p className="recent-title">Recent</p>
          {recent.length ? (
            <ul className="recent-list">
              {recent.map((turn) => (
                <li key={turn.id}>
                  <Link href="/" onClick={onNavigate} className="recent-item">
                    <span className={`recent-dot ${turn.state}`} />
                    <span className="recent-text">{turn.prompt}</span>
                    <small>{statusLabels[turn.state]}</small>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="recent-empty">No sessions yet</p>
          )}
        </div>
      </div>

      <div className="sidebar-bottom">
        <div className="device-mini">
          <span className={`device-dot ${connected ? "online" : ""}`} />
          <span>
            <strong>Kaif&apos;s MacBook</strong>
            <small>{connected ? "Daemon online" : "Daemon offline"}</small>
          </span>
        </div>
        <div className="profile">
          <span className="avatar">K</span>
          <span>
            <strong>Kaif</strong>
            <small>Personal workspace</small>
          </span>
        </div>
      </div>
    </aside>
  );
}
