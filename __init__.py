"""hermes-superpowers plugin entry point."""
import logging
from pathlib import Path

try:
    from . import commands, hooks, tools  # Hermes package loading
except ImportError:
    import commands, hooks, tools  # flat imports (pytest from repo root)

_HERE = Path(__file__).parent


def _safe(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except Exception:
        logging.getLogger("superpowers").warning(
            "registration step failed", exc_info=True)


def register(ctx):
    """Wire up the plugin against a Hermes plugin context.

    Hooks/tool/commands are the enforcement layer itself — if any of these
    fail to register, the plugin must fail loudly so the Hermes plugin
    loader marks it as errored (visible in /plugins) instead of silently
    running with no gate enforcement. Skill registration is optional (a
    single malformed skill directory shouldn't take down the whole
    plugin), so that step alone stays wrapped in `_safe`.
    """
    ctx.register_hook("pre_llm_call", hooks.pre_llm_call)
    ctx.register_hook("on_session_start", hooks.on_session_start)
    ctx.register_hook("post_tool_call", hooks.post_tool_call)

    ctx.register_tool(
        name="superpowers_phase",
        toolset="superpowers",
        schema=tools.PHASE_TOOL_SCHEMA,
        handler=tools.phase_handler,
        description="Transition the superpowers workflow phase")

    ctx.register_command(
        "superpowers", commands.handle_superpowers,
        description="Load the superpowers workflow entry point")
    ctx.register_command(
        "sp-status", commands.handle_status,
        description="Show current superpowers workflow phase")
    ctx.register_command(
        "sp-phase", commands.handle_phase,
        description="Set superpowers workflow phase", args_hint="<phase>")

    skills_dir = _HERE / "skills"
    if skills_dir.is_dir():
        for d in sorted(skills_dir.iterdir()):
            md = d / "SKILL.md"
            if md.is_file():
                _safe(lambda d=d, md=md: ctx.register_skill(
                    d.name, md,
                    description=f"superpowers process skill: {d.name}"))
