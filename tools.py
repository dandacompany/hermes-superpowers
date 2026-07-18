"""Hermes-native tools for the Superpowers workflow."""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

try:
    from . import state  # Hermes package loading
except ImportError:
    import state  # flat imports (pytest from repo root)

PHASE_TOOL_SCHEMA = {
    "name": "superpowers_phase",
    "description": (
        "Transition the superpowers workflow phase. Call after the user "
        "explicitly approves a design (design-approved) or a plan "
        "(plan-approved), when dispatching implementers (implementing), "
        "when starting final review (reviewing), and when done (done). "
        "Never skip an approval phase without explicit user approval."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "phase": {"type": "string", "enum": state.PHASES},
            "session_id": {"type": "string", "description": "current session id"},
        },
        "required": ["phase"],
    },
}

VISUAL_COMPANION_TOOL_SCHEMA = {
    "name": "superpowers_visual_companion",
    "description": (
        "Operate the browser-based Superpowers Visual Companion during "
        "brainstorming. Call start only after the user accepts the offer via "
        "clarify. Use show for visual questions, events on the next turn to "
        "read browser selections, status to check the server, and stop when "
        "brainstorming is complete. Textual questions still require clarify."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["start", "show", "events", "status", "stop"],
            },
            "project_dir": {
                "type": "string",
                "description": "Existing project root; required for start.",
            },
            "session_dir": {
                "type": "string",
                "description": "Session directory returned by start.",
            },
            "filename": {
                "type": "string",
                "description": "Fresh semantic .html filename for show.",
            },
            "html": {
                "type": "string",
                "description": "HTML fragment or full document for show.",
            },
            "open_browser": {
                "type": "boolean",
                "default": True,
                "description": "Open the local browser when the first screen appears.",
            },
            "user_approved": {
                "type": "boolean",
                "description": (
                    "Must be true for start, confirming the user accepted "
                    "the Visual Companion through clarify."
                ),
            },
        },
        "required": ["action"],
        "additionalProperties": False,
    },
}

_PLUGIN_DIR = Path(__file__).resolve().parent
_BRAINSTORM_SCRIPTS = _PLUGIN_DIR / "skills" / "brainstorming" / "scripts"
_SAFE_SCREEN_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.html$")
_MAX_HTML_BYTES = 1_000_000
_MAX_EVENTS_BYTES = 1_000_000


def _bash_command(script: Path, *args: str) -> list[str]:
    bash = shutil.which("bash")
    if not bash:
        raise RuntimeError("Visual Companion requires bash and Node.js")
    return [bash, str(script), *args]


def phase_handler(args: dict, **kwargs) -> str:
    try:
        sid = args.get("session_id") or kwargs.get("session_id") or "default"
        phase = state.set_phase(sid, args.get("phase", ""))
        return json.dumps({"ok": True, "phase": phase, "reminder": state.reminder_for(phase)})
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)})


def _json_result(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False)


def _parse_json_line(output: str) -> dict:
    for line in reversed((output or "").splitlines()):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise RuntimeError("visual companion did not return JSON status")


def _validate_session_dir(raw: str) -> Path:
    if not raw:
        raise ValueError("session_dir is required for this action")
    session_dir = Path(raw).expanduser().resolve(strict=True)
    if session_dir.parent.name != "brainstorm" or session_dir.parent.parent.name != ".superpowers":
        raise ValueError("session_dir must be inside <project>/.superpowers/brainstorm")
    content_dir = session_dir / "content"
    state_dir = session_dir / "state"
    if content_dir.is_symlink() or state_dir.is_symlink():
        raise ValueError("visual companion session directories cannot be symlinks")
    if not content_dir.is_dir() or not state_dir.is_dir():
        raise ValueError("invalid visual companion session directory")
    return session_dir


def _read_server_info(session_dir: Path) -> dict:
    info_path = session_dir / "state" / "server-info"
    stopped_path = session_dir / "state" / "server-stopped"
    if stopped_path.exists() or info_path.is_symlink() or not info_path.is_file():
        raise RuntimeError("visual companion server is not running")
    return json.loads(info_path.read_text(encoding="utf-8"))


def _pid_running(session_dir: Path) -> bool:
    try:
        pid = int((session_dir / "state" / "server.pid").read_text().strip())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def visual_companion_handler(args: dict, **kwargs) -> str:
    """Start and operate the upstream Visual Companion through one Hermes tool."""
    try:
        action = str((args or {}).get("action", "")).strip()
        if action == "start":
            if (args or {}).get("user_approved") is not True:
                raise ValueError(
                    "start requires user_approved=true after approval through clarify"
                )
            raw_project = (args or {}).get("project_dir")
            if not raw_project:
                raise ValueError("project_dir is required for start")
            project_dir = Path(raw_project).expanduser().resolve(strict=True)
            if not project_dir.is_dir():
                raise ValueError("project_dir must be an existing directory")
            script = _BRAINSTORM_SCRIPTS / "start-server.sh"
            command = _bash_command(
                script, "--project-dir", str(project_dir), "--background"
            )
            if (args or {}).get("open_browser", True):
                command.append("--open")
            proc = subprocess.run(
                command,
                cwd=str(_BRAINSTORM_SCRIPTS),
                text=True,
                capture_output=True,
                timeout=15,
                check=False,
            )
            result = _parse_json_line(proc.stdout + "\n" + proc.stderr)
            if proc.returncode or result.get("error"):
                raise RuntimeError(result.get("error") or "visual companion failed to start")
            state_dir = Path(result["state_dir"]).resolve()
            result.update({"ok": True, "session_dir": str(state_dir.parent)})
            return _json_result(result)

        session_dir = _validate_session_dir((args or {}).get("session_dir", ""))

        if action == "show":
            info = _read_server_info(session_dir)
            filename = str((args or {}).get("filename", ""))
            html = (args or {}).get("html")
            if not _SAFE_SCREEN_NAME.fullmatch(filename) or Path(filename).name != filename:
                raise ValueError("filename must be a safe, flat .html filename")
            if not isinstance(html, str) or not html.strip():
                raise ValueError("html is required for show")
            if len(html.encode("utf-8")) > _MAX_HTML_BYTES:
                raise ValueError("html exceeds the 1 MB limit")
            target = session_dir / "content" / filename
            try:
                with target.open("x", encoding="utf-8") as handle:
                    handle.write(html)
            except FileExistsError:
                raise ValueError("screen already exists; use a fresh filename") from None
            return _json_result({
                "ok": True,
                "file": str(target),
                "url": info.get("url"),
                "instruction": "End the turn and let the user inspect the browser. Read events next turn.",
            })

        if action == "events":
            events_path = session_dir / "state" / "events"
            if not events_path.exists():
                return _json_result({"ok": True, "events": []})
            if events_path.is_symlink() or not events_path.is_file():
                raise ValueError("events must be a regular file")
            if events_path.stat().st_size > _MAX_EVENTS_BYTES:
                raise ValueError("events file exceeds the 1 MB limit")
            events = []
            for line in events_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    events.append(json.loads(line))
            return _json_result({"ok": True, "events": events})

        if action == "status":
            try:
                info = _read_server_info(session_dir)
            except RuntimeError:
                info = {}
            running = bool(info) and _pid_running(session_dir)
            return _json_result({
                "ok": True,
                "running": running,
                "url": info.get("url"),
                "screen_dir": info.get("screen_dir"),
                "state_dir": info.get("state_dir"),
            })

        if action == "stop":
            script = _BRAINSTORM_SCRIPTS / "stop-server.sh"
            proc = subprocess.run(
                _bash_command(script, str(session_dir)),
                cwd=str(_BRAINSTORM_SCRIPTS),
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )
            result = _parse_json_line(proc.stdout + "\n" + proc.stderr)
            if proc.returncode or result.get("error"):
                raise RuntimeError(result.get("error") or "visual companion failed to stop")
            return _json_result({"ok": True, **result})

        raise ValueError("action must be one of: start, show, events, status, stop")
    except Exception as exc:
        return _json_result({"ok": False, "error": str(exc)})
