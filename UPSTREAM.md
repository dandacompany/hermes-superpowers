# Upstream tracking

This plugin is a hybrid port of
[obra/superpowers](https://github.com/obra/superpowers), a Claude Code plugin
by Jesse Vincent (MIT licensed).

- **Tracked version:** `6.1.1`
- **Upstream repo:** https://github.com/obra/superpowers
- **License:** MIT (Jesse Vincent)

## The 14 stable skill entry points

`skills/` exposes all 14 upstream names. Eleven contain near-verbatim upstream
bodies with Claude-Code tool names mechanically replaced by Hermes
equivalents; three are Hermes-native adapters protected from re-sync:

- `brainstorming`
- `dispatching-parallel-agents`
- `executing-plans`
- `finishing-a-development-branch`
- `receiving-code-review`
- `requesting-code-review`
- `subagent-driven-development`
- `systematic-debugging`
- `test-driven-development`
- `using-git-worktrees`
- `using-superpowers`
- `verification-before-completion`
- `writing-plans`
- `writing-skills`

Adapter-owned entry points:

- `writing-plans` → flat Hermes `plan`
- `systematic-debugging` → flat Hermes `systematic-debugging`
- `test-driven-development` → flat Hermes `test-driven-development`

`requesting-code-review` intentionally remains mirrored because its
requirements-oriented review contract is different from the flat Hermes
pre-commit verification skill.

## Re-syncing from a new upstream release

`tools_dev/sync_upstream.py` copies the 11 mirrored skill directories from an
upstream checkout into `skills/` and applies the mechanical tool-name replacements
(`Task tool` → `delegate_task`, `AskUserQuestion` → `clarify`, `Skill tool`
→ `skill_view`, `TodoWrite` → "a markdown checklist", `Bash tool` →
`terminal toolset`), then stamps a "Hermes port note" into each `SKILL.md`
frontmatter block. `ADAPTER_SKILLS` skips the three adapter-owned directories,
so their checked-in bodies and supporting files are never overwritten.

```bash
python3 tools_dev/sync_upstream.py \
  --source <path-to-upstream-checkout>/skills \
  --dest skills
```

`<path-to-upstream-checkout>` is wherever you have a checkout of
`obra/superpowers` at the target version (a maintainer's local plugin
cache, a fresh `git clone`, or an extracted release tarball) — pass its
`skills/` subdirectory.

### After every re-sync

1. **Re-apply the manual fixups.** The script only does mechanical
   text replacement. A handful of skills need hand-written passages that
   no mechanical rule can produce — new sections, Hermes-specific batch-call
   examples, concrete rule text about `delegate_task` semantics. These are
   **not** preserved by `sync_upstream.py` (it overwrites `skills/` wholesale
   from upstream). Re-apply every hand-edit listed in
   `tools_dev/MANUAL_FIXUPS.md` before committing — that file documents
   the exact anchor point and content for each one.
2. **Commit `skills/` immediately.** Do not leave the regenerated
   `skills/` tree uncommitted across a session boundary — an editor/repo
   formatter running between the sync and the commit can introduce
   whitespace drift in the freshly-copied files that is hard to distinguish
   from an intentional edit later. Sync, re-apply fixups, verify (`pytest`,
   especially `tests/test_no_claude_toolnames.py` and
   `tests/test_manual_fixups.py`), and commit as one unit.
3. **Bump the tracked version** in this file and in `plugin.yaml`'s
   `description` if it references a version number.

## Verifying a re-sync

```bash
python3 -m pytest tests/ -q
```

`tests/test_no_claude_toolnames.py` fails if any Claude-Code-specific tool
name leaked through untransformed; `tests/test_manual_fixups.py` fails if
one of the hand-written sections tracked in `MANUAL_FIXUPS.md` is missing
after the re-sync. A successful refresh reports 11 synced mirror skills; the
three adapters remain unchanged and are covered by
`tests/test_builtin_adapters.py`.
