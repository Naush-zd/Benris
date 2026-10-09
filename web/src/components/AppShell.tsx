"use client";

import { useState, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/Sidebar";
import { useAgent } from "@/lib/agent-context";

const titles: Record<string, string> = {
  "/": "Console",
  "/activity": "Activity",
  "/policies": "Policies",
  "/devices": "Devices",
  "/settings": "Settings",
};

export function AppShell({ children }: { children: ReactNode }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const pathname = usePathname();
  const { connected } = useAgent();
  const title = titles[pathname] ?? "Console";

  return (
    <div className={`app ${menuOpen ? "menu-open" : ""}`}>
      <div className="scrim" onClick={() => setMenuOpen(false)} />
      <Sidebar onNavigate={() => setMenuOpen(false)} />

      <div className="main">
        <header className="topbar">
          <button
            className="menu-button"
            aria-label="Toggle navigation"
            onClick={() => setMenuOpen((open) => !open)}
          >
            ☰
          </button>
          <div className="topbar-title">{title}</div>
          <div className={`connection ${connected ? "is-online" : ""}`}>
            <span />
            {connected ? "Daemon online" : "Daemon offline"}
          </div>
        </header>
        <div className="page">{children}</div>
      </div>
    </div>
  );
}
