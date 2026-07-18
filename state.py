"""Workflow state machine for hermes-superpowers.

Phase per Hermes session, persisted as a tiny JSON file. Never raises to
callers except set_phase(ValueError) — everything else falls back to safe
defaults so a broken state file can never break the agent.
"""
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX platforms
    fcntl = None

PHASES = [
    "idle", "brainstorming", "design-approved", "planning",
    "plan-approved", "implementing", "reviewing", "done",
]

_GATED = {"idle", "brainstorming", "design-approved", "planning", "plan-approved"}

_REMINDERS = {
    "idle": "Superpowers phase: idle. HARD GATE: no implementation until a design is approved. Start with skill_view(\"superpowers:brainstorming\") for any creative work.",
    "brainstorming": "Superpowers phase: brainstorming. HARD GATE: no implementation code until the user approves a design. Move on with /sp-phase design-approved only after explicit user approval.",
    "design-approved": "Superpowers phase: design-approved. HARD GATE: still no implementation — load the Hermes-native plan adapter (skill_view(\"superpowers:writing-plans\")), then /sp-phase planning.",
    "planning": "Superpowers phase: planning. HARD GATE: no implementation until the plan is approved by the user (/sp-phase plan-approved).",
    "plan-approved": "Superpowers phase: plan-approved. HARD GATE: implementation starts only via subagent-driven development (delegate_task implementer+reviewer pairs). Set /sp-phase implementing when dispatching begins.",
    "implementing": "Superpowers phase: implementing. Follow the plan task-by-task with delegate_task implementer + reviewer pairs; commit per task.",
    "reviewing": "Superpowers phase: reviewing. Run the Superpowers requirements review, any explicitly requested simplify-code pass, and verification-before-completion before claiming done (/sp-phase done).",
    "done": "Superpowers phase: done. Workflow complete — reset with /sp-phase idle for the next unit of work.",
}


def state_dir() -> Path:
    d = os.environ.get("HERMES_SUPERPOWERS_STATE_DIR")
    p = Path(d) if d else Path.home() / ".hermes" / "superpowers" / "state"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _path(session_id: str) -> Path:
    original = session_id or "default"
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", original)
    if safe != original:
        # Sanitization is lossy — two distinct ids can collapse to the same
        # safe name (e.g. "a/b:c" and "a_b_c" both -> "a_b_c"). Disambiguate
        # by suffixing a short hash of the original id.
        digest = hashlib.sha1(original.encode("utf-8", "surrogatepass")).hexdigest()[:8]
        safe = f"{safe}-{digest}"
    return state_dir() / f"{safe}.json"


def _read(session_id: str) -> dict:
    try:
        return json.loads(_path(session_id).read_text())
    except Exception:
        return {}


def _write(session_id: str, data: dict) -> None:
    tmp_name = None
    try:
        target = _path(session_id)
        with tempfile.NamedTemporaryFile(
            mode="w", dir=str(state_dir()), prefix=f".{target.name}.", suffix=".tmp",
            delete=False,
        ) as tmp:
            tmp_name = tmp.name
            tmp.write(json.dumps(data))
        os.replace(tmp_name, target)
        tmp_name = None
    except Exception:
        pass
    finally:
        if tmp_name and os.path.exists(tmp_name):
            try:
                os.remove(tmp_name)
            except Exception:
                pass


def _mutate(session_id: str, fn) -> None:
    """Read-modify-write under an exclusive per-session file lock.

    `fn(data)` mutates `data` in place. Lock acquisition never raises to the
    caller — if `fcntl` is unavailable or the lock can't be taken, the
    mutation still runs, just without the concurrency guarantee.
    """
    lock_path = str(_path(session_id)) + ".lock"
    lock_file = None
    if fcntl is not None:
        try:
            lock_file = open(lock_path, "a+")
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        except Exception:
            if lock_file is not None:
                try:
                    lock_file.close()
                except Exception:
                    pass
            lock_file = None
    try:
        data = _read(session_id)
        fn(data)
        _write(session_id, data)
    finally:
        if lock_file is not None:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass
            try:
                lock_file.close()
            except Exception:
                pass


def load_phase(session_id: str) -> str:
    phase = _read(session_id).get("phase", "idle")
    return phase if phase in PHASES else "idle"


def set_phase(session_id: str, phase: str) -> str:
    if phase not in PHASES:
        raise ValueError(f"unknown phase {phase!r}; valid: {', '.join(PHASES)}")

    def _apply(data: dict) -> None:
        data["phase"] = phase

    _mutate(session_id, _apply)
    return phase


def reminder_for(phase: str) -> str:
    return _REMINDERS.get(phase, _REMINDERS["idle"])


def gated(phase: str) -> bool:
    return phase in _GATED


def escalate(session_id: str) -> None:
    def _apply(data: dict) -> None:
        data["escalated"] = True

    _mutate(session_id, _apply)


def is_escalated(session_id: str) -> bool:
    return bool(_read(session_id).get("escalated"))


def clear_escalation(session_id: str) -> None:
    def _apply(data: dict) -> None:
        data.pop("escalated", None)

    _mutate(session_id, _apply)
