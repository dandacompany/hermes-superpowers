# Claude Code → Hermes tool mapping

| Claude Code (upstream)                       | Hermes                                            | Notes                                                                         |
| -------------------------------------------- | ------------------------------------------------- | ----------------------------------------------------------------------------- |
| Task tool (subagent dispatch)                | `delegate_task(goal, context, toolsets)`          | batch: `tasks=[...]`; children have NO parent history, NO user interaction    |
| AskUserQuestion                              | `clarify`                                         | unavailable inside delegate_task children — the orchestrator relays questions |
| Skill tool / `superpowers:<name>` invocation | `skill_view("superpowers:<name>")`                | plugin-bundled skills                                                         |
| TodoWrite                                    | markdown checklist (durable work: Hermes Kanban)  |                                                                               |
| SessionStart / PostCompact hooks             | `pre_llm_call` injection (first turn = bootstrap) | plugin does this automatically                                                |
| Bash tool                                    | `terminal` toolset                                |                                                                               |
| subagents in parallel (4)                    | `max_concurrent_children` (default 3)             |                                                                               |

## Mechanical replacement rules (applied by tools_dev/sync_upstream.py)

- `Task tool` / `the Task tool` → `delegate_task`
- `AskUserQuestion` → `clarify`
- `Skill tool` → `skill_view`
- `superpowers:` skill references stay (namespace identical in Hermes)
- `TodoWrite` → `a markdown checklist`
- `Bash` (tool-name context) → `terminal`
