"""Slash commands: /superpowers, /sp-status, /sp-phase <phase>."""
try:
    from . import state  # Hermes package loading
except ImportError:
    import state  # flat imports (pytest from repo root)


def handle_status(raw: str, session_id: str = "default") -> str:
    try:
        phase = state.load_phase(session_id)
        return (
            f"superpowers phase: {phase}\n"
            f"valid phases: {' -> '.join(state.PHASES)}\n"
            f"change with /sp-phase <phase>"
        )
    except Exception as e:
        return f"superpowers error: {e}"


def handle_phase(raw: str, session_id: str = "default") -> str:
    target = (raw or "").strip()
    try:
        state.set_phase(session_id, target)
        return f"superpowers phase set: {target}\n{state.reminder_for(target)}"
    except ValueError:
        return f"unknown phase {target!r}. valid: {', '.join(state.PHASES)}"
    except Exception as e:
        return f"superpowers error: {e}"


def handle_superpowers(raw: str, session_id: str = "default") -> str:
    try:
        return (
            "superpowers loaded. Read the workflow entry skill now: "
            'skill_view("superpowers:using-superpowers"). '
            "Then follow it: brainstorming before any creative work, "
            "writing-plans before code, subagent-driven-development for builds.\n"
            + handle_status("", session_id)
        )
    except Exception as e:
        return f"superpowers error: {e}"
