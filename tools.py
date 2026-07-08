"""superpowers_phase tool — lets the agent transition workflow state."""
import json

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


def phase_handler(args: dict, **kwargs) -> str:
    try:
        sid = args.get("session_id") or kwargs.get("session_id") or "default"
        phase = state.set_phase(sid, args.get("phase", ""))
        return json.dumps({"ok": True, "phase": phase, "reminder": state.reminder_for(phase)})
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)})
