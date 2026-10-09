from dataclasses import dataclass
from enum import StrEnum


class Decision(StrEnum):
    ALLOW = "ALLOW"
    ASK = "ASK"
    DENY = "DENY"


@dataclass(frozen=True)
class PolicyDecision:
    action: str
    decision: Decision
    reason: str


class PolicyEngine:
    """Small, explicit MVP policy table.

    Unknown actions default to ASK so a new tool cannot silently gain access.
    """

    def __init__(self, rules: dict[str, Decision] | None = None) -> None:
        self._rules = rules or {
            "browser.navigate": Decision.ALLOW,
            "file.read": Decision.ALLOW,
            "app.launch": Decision.ALLOW,
            "app.quit": Decision.ALLOW,
            "app.list": Decision.ALLOW,
            "system.processes": Decision.ALLOW,
            "media.control": Decision.ALLOW,
            "system.volume": Decision.ALLOW,
            "system.lock": Decision.ALLOW,
            "terminal.execute": Decision.ASK,
            "file.write": Decision.ASK,
            "file.delete": Decision.DENY,
        }

    def decide(self, action: str) -> PolicyDecision:
        decision = self._rules.get(action, Decision.ASK)
        reasons = {
            Decision.ALLOW: "Allowed by the MVP policy.",
            Decision.ASK: "Human approval is required for this action.",
            Decision.DENY: "This action is denied by the MVP policy.",
        }
        return PolicyDecision(action, decision, reasons[decision])