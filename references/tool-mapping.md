# Claude Code → Hermes tool mapping

| Claude Code (upstream)                       | Hermes                                            | Notes                                                                         |
| -------------------------------------------- | ------------------------------------------------- | ----------------------------------------------------------------------------- |
| Task tool (subagent dispatch)                | `delegate_task(goal, context, toolsets)`          | batch: `tasks=[...]`; children have NO parent history, NO user interaction    |
| AskUserQuestion                              | `clarify`                                         | unavailable inside delegate_task children — the orchestrator relays questions |
| Visual Companion scripts                    | `superpowers_visual_companion`                    | native start/show/events/status/stop lifecycle; offer must use `clarify`      |
| Skill tool / `superpowers:<name>` invocation | `skill_view("superpowers:<name>")`                | plugin-bundled skills                                                         |
| TodoWrite                                    | markdown checklist (durable work: Hermes Kanban)  |                                                                               |
| SessionStart / PostCompact hooks             | `pre_llm_call` injection (first turn = bootstrap) | plugin does this automatically                                                |
| Bash tool                                    | `terminal` toolset                                |                                                                               |
| subagents in parallel (4)                    | `max_concurrent_children` (default 3)             |                                                                               |

Plugin skill registration is namespaced by Hermes itself. A plugin skill named
`systematic-debugging` resolves as `superpowers:systematic-debugging`; it does
not shadow the flat built-in `systematic-debugging`.

## Hermes-native skill adapters

| Stable plugin entry point             | Flat Hermes skill         | Superpowers delta                                                                                  |
| ------------------------------------- | ------------------------- | -------------------------------------------------------------------------------------------------- |
| `superpowers:writing-plans`           | `plan`                    | design approval, `docs/superpowers/plans/`, global constraints, task interfaces, SDD handoff       |
| `superpowers:systematic-debugging`    | `systematic-debugging`    | bundled root-cause techniques, TDD regression route, conditional `python-debugpy`, completion gate |
| `superpowers:test-driven-development` | `test-driven-development` | approved-plan scope, SDD implementer evidence, anti-pattern reference, final verification          |

`superpowers:requesting-code-review` is not an adapter. It remains the
requirements/plan-compliance reviewer; the flat Hermes skill is a separate
pre-commit security and quality pipeline. `simplify-code` is an optional flat
helper and must only run on explicit user request.

## Mechanical replacement rules (applied by tools_dev/sync_upstream.py)

- `Task tool` / `the Task tool` → `delegate_task`
- `AskUserQuestion` → `clarify`
- `Skill tool` → `skill_view`
- `superpowers:` skill references stay (namespace identical in Hermes)
- `TodoWrite` → `a markdown checklist`
- `Bash` (tool-name context) → `terminal`
