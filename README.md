# hermes-superpowers

A full port of [obra/superpowers](https://github.com/obra/superpowers) for
[Hermes Agent](https://github.com/NousResearch/hermes-agent): 14 process
skills (brainstorming, writing plans, subagent-driven development, TDD,
systematic debugging, code review, and more), an enforcement layer that
keeps the agent on-process via lifecycle hooks, and a spec-driven-development
(SDD) workflow adapted to Hermes's `delegate_task` subagent model.

Where upstream targets Claude Code, this plugin re-implements the same
skills and workflow discipline as a Hermes plugin: `plugin.yaml` +
`register(ctx)` wiring, a small phase state machine, three slash commands,
and one tool the agent can call to advance the workflow.

## Install

Hermes plugins are directories dropped under `~/.hermes/plugins/`, each
with a `plugin.yaml` manifest and an `__init__.py` exposing `register(ctx)`
— this repo already has that shape at its root.

### Option A — clone + symlink (recommended for development)

```bash
git clone https://github.com/dandacompany/hermes-superpowers.git ~/src/hermes-superpowers
mkdir -p ~/.hermes/plugins
ln -s ~/src/hermes-superpowers ~/.hermes/plugins/superpowers
```

A plain copy (`cp -r` instead of `ln -s`) works identically; the symlink
just makes `git pull` in the source checkout update the plugin in place.

### Option B — `hermes plugins install`

If the repo is hosted on GitHub, Hermes can clone it directly into
`~/.hermes/plugins/`:

```bash
hermes plugins install dandacompany/hermes-superpowers
```

This accepts `owner/repo` shorthand or a full git URL. It asks
`Enable 'superpowers' now? [y/N]` — answer `y`, or pass `--enable` /
`--no-enable` to skip the prompt in a scripted install. It does not accept
a local filesystem path; for a local checkout, use Option A.

### Verify

```bash
hermes plugins list
```

You should see `superpowers` listed with `Source: git` (Option B) or a
local directory (Option A), version `0.1.0`, and status `not enabled` —
plugins are opt-in by default. Enable it:

```bash
hermes plugins enable superpowers
```

This prompts `Allow this plugin to replace built-in tools (e.g. shell_exec,
write_file)? [y/N]` — answer **no**. This plugin only registers hooks, one
tool, and three commands; it does not override any built-in tool. Restart
your session (or the gateway, `hermes gateway restart`) for the plugin to
take effect.

If the plugin doesn't show up, or shows up but isn't loading, get verbose
plugin-discovery logging:

```bash
HERMES_PLUGINS_DEBUG=1 hermes plugins list
```

or tail the persisted log:

```bash
hermes logs --level WARNING | grep -i plugin
```

## Slash commands

| Command             | Effect                                                                                                                                                                                                                  |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/superpowers`      | Load the workflow entry point — tells the agent to read `superpowers:using-superpowers` and follow the process (brainstorming before creative work, writing-plans before code, subagent-driven-development for builds). |
| `/sp-status`        | Print the current workflow phase and the full phase list.                                                                                                                                                               |
| `/sp-phase <phase>` | Set the workflow phase explicitly (one of the 8 phases below). Rejects unknown phase names.                                                                                                                             |

## How the hooks behave

Three hooks are registered (`pre_llm_call`, `on_session_start`,
`post_tool_call`). None of them block a tool call — the design is
reminder-based, not enforcement-based:

- **First-turn bootstrap** (`pre_llm_call`, `is_first_turn=True`): injects
  the full `using-superpowers` skill text (or a fallback summary if the
  file can't be read) wrapped in `<superpowers-bootstrap>` tags, mirroring
  upstream's `SessionStart` hook.
- **Per-turn gate reminder** (`pre_llm_call`, every later turn): injects a
  one-line `<superpowers-gate>` reminder of the current phase and what's
  gating it (e.g. "no implementation until a design is approved").
- **Write-tool escalation** (`post_tool_call` + next `pre_llm_call`): if a
  file-writing tool (`write_file`, `patch`) runs while the workflow is in a
  pre-implementation phase (`idle` through `plan-approved`), the next
  turn's gate reminder is upgraded to a `WARNING` telling the agent to stop
  and return to the design/plan gate.
- **Session reset** (`on_session_start`): resets phase to `idle` and clears
  any pending escalation, so each new session starts clean.

Nothing here hard-blocks a tool call — see "Differences from upstream"
below for why.

## Workflow phases

`idle → brainstorming → design-approved → planning → plan-approved →
implementing → reviewing → done`

The agent transitions phases itself, either via `/sp-phase <phase>` or by
calling the `superpowers_phase` tool (same effect, tool-callable). The
**approval phases** (`design-approved`, `plan-approved`) are meant to be
set only after the human has explicitly approved the design or the plan —
the hooks and skill text repeatedly remind the agent of this, but nothing
in code prevents the agent from skipping the rule; it is a documented
convention the agent is expected to honor.

## SDD (spec-driven development) on Hermes

`subagent-driven-development` and `dispatching-parallel-agents` are ported
to use `delegate_task` instead of Claude Code's Task tool. In practice:

- Implementation happens through **implementer + reviewer pairs**: dispatch
  one `delegate_task` to implement a plan task, then a second to review the
  diff; a REJECT verdict triggers a fix-implementer dispatch (capped at 2
  rounds before escalating back to the orchestrator).
- Children started via `delegate_task` get **no parent conversation
  history** and **cannot call `clarify`** — any question from a child must
  be relayed by the orchestrating agent.
- `delegate_task` dispatches are **not durable** across a parent-turn
  interruption, so plans are executed **commit-per-task**: each completed
  task is committed before moving to the next, so a resume never has to
  replay in-flight subagent work.
- Batches of independent tasks use `delegate_task(tasks=[...])`, capped by
  `max_concurrent_children` (default 3; override via
  `DELEGATION_MAX_CONCURRENT_CHILDREN`) — a batch beyond the cap is queued,
  not failed.

See `references/tool-mapping.md` for the full Claude Code → Hermes tool
mapping and the mechanical replacement rules applied when re-syncing from
upstream.

## Differences from upstream

- **No compaction hook.** Claude Code has a `PostCompact` hook to
  re-inject process reminders after context compaction; Hermes has no
  equivalent, so this plugin instead injects a phase reminder on **every**
  turn via `pre_llm_call`, escalating to a `WARNING` after a stray write.
- **No hard blocking, by design.** Every hook here is best-effort and
  reminder-only (each catches its own exceptions and falls back safely).
  The workflow discipline depends on the agent reading and honoring the
  injected reminders, not on the plugin refusing to let a tool run.
- **`skill_view` instead of the Skill tool.** Claude Code's `Skill tool` /
  `superpowers:<name>` invocation becomes `skill_view("superpowers:<name>")`
  on Hermes; all 14 skills were mechanically re-mapped by
  `tools_dev/sync_upstream.py` plus a handful of hand-written passages
  tracked in `tools_dev/MANUAL_FIXUPS.md`.
- **Other-harness adaptation files removed.** Upstream ships reference docs
  for harnesses this port doesn't run (Codex, Pi, Antigravity) and a
  Claude-Code-specific worked example (`CLAUDE_MD_TESTING.md`), plus an
  upstream dev log (`CREATION-LOG.md`). None of it applies on Hermes, so
  it's deleted rather than mapped; see `tools_dev/MANUAL_FIXUPS.md` for
  what was removed and how re-syncs stay clean of it.

## Attribution

Based on [obra/superpowers](https://github.com/obra/superpowers) 6.1.1 by
Jesse Vincent, MIT licensed. The 14 skill bodies here are near-verbatim
mirrors of upstream with Hermes tool names substituted in; see
`UPSTREAM.md` for the re-sync procedure.
