const policies = [
  {
    decision: "allow",
    action: "Browser navigation",
    detail: "The agent can open and read web pages without asking.",
  },
  {
    decision: "allow",
    action: "Read file",
    detail: "The agent can inspect local files within the workspace.",
  },
  {
    decision: "ask",
    action: "Terminal command",
    detail: "Requires your explicit approval before each run.",
  },
  {
    decision: "ask",
    action: "Write file",
    detail: "Requires your explicit approval before saving changes.",
  },
  {
    decision: "deny",
    action: "Delete file",
    detail: "Blocked by default — the agent can never delete files.",
  },
];

export default function PoliciesPage() {
  return (
    <div className="content">
      <div className="page-head">
        <h1>Policies</h1>
        <p>Default guardrails · fail closed. Every sensitive action is gated.</p>
      </div>

      <div className="policy-grid">
        {policies.map((policy) => (
          <div className="policy-row" key={policy.action}>
            <span className={`policy-badge ${policy.decision}`}>
              {policy.decision.toUpperCase()}
            </span>
            <div>
              <strong>{policy.action}</strong>
              <p>{policy.detail}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
