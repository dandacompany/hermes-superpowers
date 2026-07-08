"""Lifecycle hooks — the enforcement layer.

pre_llm_call is the ONLY hook whose return value Hermes uses: return
{"context": str} to inject text into the current turn. First turn gets the
full using-superpowers skill (mirrors upstream's SessionStart hook); later
turns get a one-line phase reminder from the state machine.
"""
from pathlib import Path

try:
    from . import state  # Hermes package loading
except ImportError:
    import state  # flat imports (pytest from repo root)

WRITE_TOOLS = {"write_file", "patch"}

_SKILL_DIR = Path(__file__).parent / "skills"


def bootstrap_text() -> str:
    """Load using-superpowers SKILL.md or fall back to comprehensive reminder.

    If SKILL.md exists, return its full content. Otherwise, return a default
    message plus the full workflow phase reminders to ensure >500 chars of
    useful bootstrap content.
    """
    p = _SKILL_DIR / "using-superpowers" / "SKILL.md"
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        # Fallback: default message + full workflow phase reminders
        default_msg = (
            "You have superpowers (hermes-superpowers plugin). Load "
            'skill_view("superpowers:using-superpowers") before any task.'
        )

        # Build workflow phases section with all reminders
        phases_section = "\n\n## Workflow Phases\n\n"
        for phase in state.PHASES:
            reminder = state.reminder_for(phase)
            phases_section += f"**{phase}**: {reminder}\n\n"

        return default_msg + phases_section


def pre_llm_call(session_id, user_message, conversation_history, is_first_turn, **kwargs):
    """Inject context before LLM call.

    First turn: full bootstrap (SKILL.md or fallback)
    Later turns: phase-specific reminder, with WARNING if escalated

    Returns: {"context": str} or {} (if any exception occurs)
    """
    try:
        if is_first_turn:
            text = bootstrap_text()
            return {"context": "<superpowers-bootstrap>\n" + text + "\n</superpowers-bootstrap>"}
        phase = state.load_phase(session_id)
        reminder = state.reminder_for(phase)
        if state.is_escalated(session_id):
            state.clear_escalation(session_id)
            reminder = (
                "WARNING: a file-writing tool ran while the superpowers workflow "
                "is still pre-implementation (phase: " + phase + "). If this was "
                "implementation work, STOP and return to the design/plan gate. "
                + reminder
            )
        return {"context": "<superpowers-gate>" + reminder + "</superpowers-gate>"}
    except Exception:
        return {}


def on_session_start(session_id, **kwargs):
    """Reset session state to idle on start."""
    try:
        state.set_phase(session_id, "idle")
        state.clear_escalation(session_id)
    except Exception:
        pass


def post_tool_call(tool_name, args, result, task_id=None, **kwargs):
    """Escalate if a write tool runs while workflow is gated.

    Hermes passes a real ``session_id`` kwarg; prefer it over ``task_id``,
    which is only a fallback for older call conventions.
    """
    try:
        if tool_name not in WRITE_TOOLS:
            return
        session_id = kwargs.get("session_id") or task_id or "default"
        if state.gated(state.load_phase(session_id)):
            state.escalate(session_id)
    except Exception:
        pass
