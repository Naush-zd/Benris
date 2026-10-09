"""Tools that let the agent actually act on the local machine.

Every call goes through the policy engine first, runs as an argument list
(never a shell string), and reports back to the active task session so the
control plane can show what really happened.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from contextvars import ContextVar
from urllib.parse import quote_plus, urlparse

from phi.tools import Toolkit

from ..security.policy import Decision, PolicyEngine

# Set by the task runtime so tool calls can be streamed to the UI.
action_sink: ContextVar[Callable[[str, str, dict], None] | None] = ContextVar(
    "benris_action_sink", default=None
)

_APP_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._+-]{0,49}$")
_HOSTNAME = re.compile(r"^(localhost|(\d{1,3}\.){3}\d{1,3}|[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+)$")
_MEDIA_ACTIONS = {
    "play": "play",
    "resume": "play",
    "pause": "pause",
    "playpause": "playpause",
    "toggle": "playpause",
    "stop": "pause",
    "next": "next track",
    "skip": "next track",
    "previous": "previous track",
    "back": "previous track",
}
_PLAYERS = ("Spotify", "Music")
_APP_FOLDERS = ("/Applications", "/Applications/Utilities", "/System/Applications", "/System/Applications/Utilities")
_LOCK_KEYSTROKE = (
    'tell application "System Events" to keystroke "q" using {control down, command down}'
)
_TIMEOUT = 20


class SystemToolError(RuntimeError):
    """Raised when a system action cannot be carried out."""


def _report(action: str, message: str, **data: object) -> None:
    sink = action_sink.get()
    if sink is not None:
        sink(action, message, dict(data))


def _applescript_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _run(args: list[str]) -> str:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=_TIMEOUT)
    except FileNotFoundError as error:
        raise SystemToolError(f"Required command is unavailable: {args[0]}") from error
    except subprocess.TimeoutExpired as error:
        raise SystemToolError("The system action timed out.") from error
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()
        raise SystemToolError(detail[-1] if detail else "The system action failed.")
    return result.stdout.strip()


def _osascript(script: str) -> str:
    return _run(["osascript", "-e", script])


def _is_running(app: str) -> bool:
    script = (
        'tell application "System Events" to return (exists '
        f'(processes whose name is "{_applescript_string(app)}"))'
    )
    try:
        return _osascript(script) == "true"
    except SystemToolError:
        return False


def _active_player() -> str | None:
    return next((player for player in _PLAYERS if _is_running(player)), None)


class SystemControlTools(Toolkit):
    """Browser, application, and media control for the local desktop."""

    def __init__(self, policy: PolicyEngine | None = None) -> None:
        super().__init__(name="system_control")
        self.policy = policy or PolicyEngine()
        self.register(self.open_website)
        self.register(self.search_the_web)
        self.register(self.open_application)
        self.register(self.quit_application)
        self.register(self.list_running_applications)
        self.register(self.list_installed_applications)
        self.register(self.report_memory_usage)
        self.register(self.play_music)
        self.register(self.control_media)
        self.register(self.set_system_volume)
        self.register(self.lock_screen)

    def _authorize(self, action: str) -> None:
        decision = self.policy.decide(action)
        if decision.decision is Decision.DENY:
            raise SystemToolError(f"Blocked by policy: {decision.reason}")

    def _require_macos(self) -> None:
        if sys.platform != "darwin":
            raise SystemToolError("Desktop control is only supported on macOS right now.")

    def _act(self, action: str, run: Callable[[], str]) -> str:
        try:
            self._authorize(action)
            self._require_macos()
            message = run()
        except SystemToolError as error:
            _report(action, str(error), ok=False)
            return f"Failed: {error}"
        _report(action, message, ok=True)
        return message

    def open_website(self, url: str) -> str:
        """Open a web page in the user's default browser.

        Args:
            url: The address to open, for example "github.com" or "https://news.ycombinator.com".

        Returns:
            Confirmation that the page was opened.
        """

        def run() -> str:
            candidate = url.strip()
            if not candidate:
                raise SystemToolError("No URL was provided.")
            if "://" not in candidate:
                candidate = f"https://{candidate}"
            parsed = urlparse(candidate)
            if parsed.scheme not in {"http", "https"}:
                raise SystemToolError("Only http and https links can be opened.")
            host = parsed.hostname or ""
            if not _HOSTNAME.match(host):
                raise SystemToolError(f"'{url}' is not a valid web address.")
            _run(["open", parsed.geturl()])
            return f"Opened {host} in the browser."

        return self._act("browser.navigate", run)

    def search_the_web(self, query: str) -> str:
        """Open a web search for the query in the user's browser.

        Use this when the user wants to *see* search results on screen. Use the
        DuckDuckGo tool instead when they only want the answer spoken back.

        Args:
            query: What to search for.

        Returns:
            Confirmation that the search page was opened.
        """

        def run() -> str:
            text = query.strip()
            if not text:
                raise SystemToolError("No search query was provided.")
            _run(["open", f"https://duckduckgo.com/?q={quote_plus(text)}"])
            return f"Opened browser search results for '{text}'."

        return self._act("browser.navigate", run)

    def open_application(self, name: str) -> str:
        """Launch or focus a desktop application.

        Args:
            name: The application name, for example "Safari", "Spotify", or "Visual Studio Code".

        Returns:
            Confirmation that the application was opened.
        """

        def run() -> str:
            app = name.strip()
            if not _APP_NAME.match(app):
                raise SystemToolError(f"'{name}' is not a valid application name.")
            _run(["open", "-a", app])
            return f"Opened {app}."

        return self._act("app.launch", run)

    def quit_application(self, name: str) -> str:
        """Quit a running desktop application.

        Args:
            name: The application name to quit.

        Returns:
            Confirmation that the application was asked to quit.
        """

        def run() -> str:
            app = name.strip()
            if not _APP_NAME.match(app):
                raise SystemToolError(f"'{name}' is not a valid application name.")
            if not _is_running(app):
                return f"{app} is not running."
            _osascript(f'tell application "{_applescript_string(app)}" to quit')
            return f"Closed {app}."

        return self._act("app.quit", run)

    def list_running_applications(self) -> str:
        """List the applications that are currently open.

        Returns:
            A comma separated list of running application names.
        """

        def run() -> str:
            script = (
                'tell application "System Events" to return name of '
                "(every process whose background only is false)"
            )
            names = [item.strip() for item in _osascript(script).split(",") if item.strip()]
            return ", ".join(sorted(names)) if names else "No applications are open."

        return self._act("app.list", run)

    def list_installed_applications(self) -> str:
        """List the applications installed on this machine.

        Use this when the user asks what apps they have, not just what is open.

        Returns:
            A comma separated list of installed application names.
        """

        def run() -> str:
            names = {
                entry[:-4]
                for folder in _APP_FOLDERS
                if os.path.isdir(folder)
                for entry in os.listdir(folder)
                if entry.endswith(".app")
            }
            home_apps = os.path.expanduser("~/Applications")
            if os.path.isdir(home_apps):
                names.update(
                    entry[:-4] for entry in os.listdir(home_apps) if entry.endswith(".app")
                )
            if not names:
                raise SystemToolError("No installed applications were found.")
            return f"{len(names)} installed applications: " + ", ".join(sorted(names))

        return self._act("app.list", run)

    def report_memory_usage(self, limit: int = 5) -> str:
        """Report which applications are using the most memory.

        Args:
            limit: How many of the heaviest processes to report.

        Returns:
            The top memory consumers with their usage.
        """

        def run() -> str:
            try:
                count = max(1, min(int(limit), 15))
            except (TypeError, ValueError):
                count = 5
            totals: dict[str, int] = {}
            for line in _run(["ps", "-Ao", "rss=,comm="]).splitlines():
                parts = line.strip().split(None, 1)
                if len(parts) != 2 or not parts[0].isdigit():
                    continue
                name = parts[1].rsplit("/", 1)[-1]
                # Roll helper processes up into the app users actually recognise.
                name = name.split(" Helper", 1)[0]
                totals[name] = totals.get(name, 0) + int(parts[0])
            if not totals:
                raise SystemToolError("Could not read process memory usage.")
            top = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:count]
            parts = [f"{name} {kb / 1024 / 1024:.1f} gigabytes" if kb >= 1024 * 1024
                     else f"{name} {kb / 1024:.0f} megabytes" for name, kb in top]
            return "Highest memory use: " + ", ".join(parts) + "."

        return self._act("system.processes", run)

    def play_music(self, query: str = "") -> str:
        """Play music on the local machine.

        Args:
            query: Optional song, artist, album, or playlist. Leave empty to resume playback.

        Returns:
            What is now playing, or where the music was opened.
        """

        def run() -> str:
            wanted = query.strip()
            if not wanted:
                player = _active_player() or "Music"
                _osascript(f'tell application "{player}" to play')
                return f"Resumed playback in {player}."

            term = _applescript_string(wanted)
            script = f"""
            tell application "Music"
                activate
                set matches to (every track of library playlist 1 whose name contains "{term}" or artist contains "{term}" or album contains "{term}")
                if matches is {{}} then return "NO_MATCH"
                play item 1 of matches
                return (name of current track) & " by " & (artist of current track)
            end tell
            """
            outcome = _osascript(script)
            if outcome != "NO_MATCH":
                return f"Now playing {outcome}."
            _run(["open", f"https://music.youtube.com/search?q={quote_plus(wanted)}"])
            return f"'{wanted}' is not in the local library, so I opened it on YouTube Music."

        return self._act("media.control", run)

    def control_media(self, action: str) -> str:
        """Control playback of the active music player.

        Args:
            action: One of play, pause, next, or previous.

        Returns:
            Confirmation of the playback change.
        """

        def run() -> str:
            command = _MEDIA_ACTIONS.get(action.strip().lower())
            if command is None:
                raise SystemToolError(f"'{action}' is not a supported playback action.")
            player = _active_player()
            if player is None:
                raise SystemToolError("No music player is currently running.")
            _osascript(f'tell application "{player}" to {command}')
            return f"Sent {action.strip().lower()} to {player}."

        return self._act("media.control", run)

    def set_system_volume(self, level: int) -> str:
        """Set the system output volume.

        Args:
            level: Volume percentage between 0 and 100.

        Returns:
            Confirmation of the new volume.
        """

        def run() -> str:
            try:
                value = int(level)
            except (TypeError, ValueError):
                raise SystemToolError(f"'{level}' is not a valid volume.") from None
            if not 0 <= value <= 100:
                raise SystemToolError("Volume must be between 0 and 100.")
            _osascript(f"set volume output volume {value}")
            return f"Set the volume to {value} percent."

        return self._act("system.volume", run)

    def lock_screen(self) -> str:
        """Lock the screen immediately.

        Returns:
            Confirmation that the screen was locked.
        """

        def run() -> str:
            try:
                _osascript(_LOCK_KEYSTROKE)
            except SystemToolError:
                # Without Accessibility permission the keystroke is refused, so sleep
                # the display instead and do not claim a lock that may not have happened.
                _run(["pmset", "displaysleepnow"])
                return (
                    "Put the display to sleep. To lock instantly, allow Accessibility "
                    "access for your terminal in System Settings, Privacy and Security."
                )
            return "Locked the screen."

        return self._act("system.lock", run)


def desktop_control_available() -> bool:
    """True when the host can actually run the desktop actions."""
    return sys.platform == "darwin" and shutil.which("osascript") is not None
