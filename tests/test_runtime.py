import threading
import time
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from src.api.server import app
from src.core.events import EventLog, RuntimeEvent
from src.runtime.executor import TaskExecutor
from src.runtime.session import SessionState
from src.security.policy import Decision, PolicyEngine
from src.tools import SystemControlTools, action_sink
from src.tools.system import SystemToolError


class PolicyTests(unittest.TestCase):
    def test_mvp_policy_defaults(self):
        policy = PolicyEngine()
        self.assertEqual(policy.decide("browser.navigate").decision, Decision.ALLOW)
        self.assertEqual(policy.decide("file.read").decision, Decision.ALLOW)
        self.assertEqual(policy.decide("app.launch").decision, Decision.ALLOW)
        self.assertEqual(policy.decide("media.control").decision, Decision.ALLOW)
        self.assertEqual(policy.decide("terminal.execute").decision, Decision.ASK)
        self.assertEqual(policy.decide("file.write").decision, Decision.ASK)
        self.assertEqual(policy.decide("file.delete").decision, Decision.DENY)
        self.assertEqual(policy.decide("new.tool").decision, Decision.ASK)


class SystemToolTests(unittest.TestCase):
    def setUp(self):
        self.tools = SystemControlTools()
        self.calls = []
        patcher = mock.patch("src.tools.system._run", side_effect=lambda args: self.calls.append(args) or "")
        self.addCleanup(patcher.stop)
        patcher.start()
        platform = mock.patch("src.tools.system.sys.platform", "darwin")
        self.addCleanup(platform.stop)
        platform.start()

    def test_agent_can_actually_open_a_site_and_an_app(self):
        self.assertIn("Opened github.com", self.tools.open_website("github.com"))
        self.assertIn("Opened Safari", self.tools.open_application("Safari"))
        self.assertEqual(self.calls[0], ["open", "https://github.com"])
        self.assertEqual(self.calls[1], ["open", "-a", "Safari"])

    def test_agent_can_lock_the_screen(self):
        self.assertIn("Locked the screen", self.tools.lock_screen())
        self.assertEqual(self.calls[-1][0], "osascript")

    def test_lock_without_accessibility_does_not_claim_a_lock(self):
        with mock.patch("src.tools.system._osascript", side_effect=SystemToolError("denied")):
            result = self.tools.lock_screen()
        self.assertNotIn("Locked the screen", result)
        self.assertIn("display to sleep", result)
        self.assertEqual(self.calls[-1], ["pmset", "displaysleepnow"])

    def test_memory_report_groups_helpers_under_their_app(self):
        ps_output = "4000000 /Applications/Code.app/Contents/MacOS/Code Helper (Plugin)\n2000000 /Applications/Code.app/Contents/MacOS/Code\n1000 /usr/sbin/tiny\n"
        with mock.patch("src.tools.system._run", return_value=ps_output):
            result = self.tools.report_memory_usage(2)
        self.assertIn("Code 5.7 gigabytes", result)
        self.assertNotIn("Helper", result)

    def test_unsafe_input_is_rejected_without_running_a_command(self):
        self.assertTrue(self.tools.open_website("file:///etc/passwd").startswith("Failed"))
        self.assertTrue(self.tools.open_application("evil; rm -rf /").startswith("Failed"))
        self.assertTrue(self.tools.set_system_volume(500).startswith("Failed"))
        self.assertEqual(self.calls, [])

    def test_denied_actions_are_blocked_by_policy(self):
        tools = SystemControlTools(PolicyEngine({"browser.navigate": Decision.DENY}))
        self.assertIn("Blocked by policy", tools.open_website("github.com"))
        self.assertEqual(self.calls, [])

    def test_tool_results_are_reported_to_the_session(self):
        seen = []
        token = action_sink.set(lambda action, message, data: seen.append((action, data["ok"])))
        self.addCleanup(action_sink.reset, token)
        self.tools.open_website("github.com")
        self.assertEqual(seen, [("browser.navigate", True)])


class RuntimeTests(unittest.TestCase):
    def test_event_log_broadcasts_to_subscribers(self):
        log = EventLog()
        subscriber = log.subscribe()
        event = RuntimeEvent("session-1", "TASK_STARTED", "Started")
        log.append(event)
        self.assertIs(subscriber.get(timeout=0.1), event)

    def test_task_can_be_cancelled_at_checkpoint(self):
        executor = TaskExecutor()
        reached_checkpoint = threading.Event()

        def task(session):
            reached_checkpoint.set()
            session.checkpoint()

        session = executor.submit("cancel me", task)
        self.assertTrue(reached_checkpoint.wait(0.2))
        session.cancel()
        for _ in range(20):
            if session.state == SessionState.CANCELLED:
                break
            time.sleep(0.01)
        self.assertEqual(session.state, SessionState.CANCELLED)

    def test_approval_can_be_rejected(self):
        executor = TaskExecutor()
        waiting = threading.Event()

        def task(session):
            waiting.set()
            self.assertFalse(session.request_approval("terminal.execute", "Run tests"))

        session = executor.submit("approval", task)
        self.assertTrue(waiting.wait(0.2))
        for _ in range(20):
            if session.state == SessionState.WAITING_APPROVAL:
                break
            time.sleep(0.01)
        session.reject()
        for _ in range(20):
            if session.state == SessionState.COMPLETED:
                break
            time.sleep(0.01)
        self.assertEqual(session.state, SessionState.COMPLETED)


class ToolArgumentCompatibilityTests(unittest.TestCase):
    def test_tool_calls_without_arguments_do_not_crash(self):
        import src.assistant  # noqa: F401  (applies the compatibility shim)
        from phi.model.anthropic import Claude
        from phi.model.message import Message

        message = Message(
            role="assistant",
            content="",
            tool_calls=[{"id": "t1", "type": "function", "function": {"name": "lock_screen"}}],
        )
        Claude(id="test", api_key="test").format_messages([message])
        self.assertEqual(message.tool_calls[0]["function"]["arguments"], "{}")


class ApiTests(unittest.TestCase):
    def test_health_and_missing_task(self):
        with TestClient(app) as client:
            self.assertEqual(client.get("/health").json(), {"status": "ok"})
            self.assertEqual(client.get("/tasks/missing").status_code, 404)
            self.assertEqual(client.get("/policy/file/delete").json()["decision"], "DENY")