# Manual fixups on top of sync_upstream.py

`sync_upstream.py` mechanically replaces upstream Claude-Code tool names
with their Hermes equivalents (see `REPLACEMENTS` / `HEADER_NOTE` in that
script). A few skills needed additional hand-written passages that the
mechanical replacement cannot produce — new sections, batch-call examples,
concrete rule text. This file tracks those hand-edits so a future re-sync
(which overwrites `skills/` from upstream + the mechanical transform) knows
what to re-apply after regenerating.

Scope discipline: every insertion below is limited to **tool-mapping
semantics** (how Hermes primitives like `delegate_task`, `clarify`,
`skill_view`, `max_concurrent_children` behave). The surrounding upstream
methodology text was left untouched.

## Hermes-native adapter skills (intentionally not upstream mirrors)

Hermes Agent 0.18.0+ includes native `plan`, `systematic-debugging`, and
`test-driven-development` skills. The plugin keeps its stable namespaced entry
points but delegates core methodology to those built-ins:

- `skills/writing-plans/SKILL.md` → `skill_view("plan")`
- `skills/systematic-debugging/SKILL.md` →
  `skill_view("systematic-debugging")`
- `skills/test-driven-development/SKILL.md` →
  `skill_view("test-driven-development")`

Each adapter contains only the Superpowers-specific delta: approval and plan
format requirements, bundled supporting references, SDD integration, and
completion routing. `superpowers:requesting-code-review` remains a mirrored
requirements-review skill because Hermes' flat skill with the same bare name
implements a different pre-commit verification pipeline.

**Made durable in `tools_dev/sync_upstream.py`:** `ADAPTER_SKILLS` skips these
three source directories before `copytree`, preserving the checked-in adapters
and their supporting files during a future upstream refresh.

**Guarded by:** `tests/test_builtin_adapters.py` verifies the native skill
targets, required Superpowers deltas, 14-entry public registration surface, and
sync preservation behavior.

**Re-apply after re-sync:** nothing. The sync script must report 11 mirrored
skills while leaving the three adapters untouched.

## Other-harness / dev-log leftovers removed (quality cleanup, not scanner-motivated)

Upstream `superpowers` ships adaptation docs and dev artifacts for harnesses
this Hermes port doesn't run, plus one Claude-Code-specific worked example.
None of it applies here, so it was deleted outright rather than mapped:

- `skills/using-superpowers/references/codex-tools.md`
- `skills/using-superpowers/references/pi-tools.md`
- `skills/using-superpowers/references/antigravity-tools.md`
- `skills/systematic-debugging/CREATION-LOG.md` (upstream dev log, not
  agent-facing content)
- `skills/writing-skills/examples/CLAUDE_MD_TESTING.md` (a worked example
  specific to Claude Code's CLAUDE.md convention)

Two directories (`using-superpowers/references/`, `writing-skills/examples/`)
became empty as a result and were removed too.

**Made durable in `tools_dev/sync_upstream.py`:**

- `STRIP_PATHS` lists the five paths above (relative to `skills/`); `sync()`
  deletes them right after `copytree` and prunes their parent directory if it
  is left empty, so a fresh re-sync from upstream won't reintroduce them.
- `REPLACEMENTS` gained two narrowly-scoped entries (matched against the
  _exact_ upstream text, not a blanket substitution) that fix the two
  dangling references the deletions would otherwise leave in
  `skills/using-superpowers/SKILL.md`:
  1. Strips the "If your harness appears here..." intro line plus the
     Codex/Pi/Antigravity bullets out of the `## Platform Adaptation`
     section (the Hermes bullet is still added by the manual fixup
     documented below, under "skills/using-superpowers/SKILL.md").
  2. Rewords the "User Instructions" sentence away from naming
     `CLAUDE.md, AGENTS.md, GEMINI.md` to generic Hermes phrasing
     ("host instruction files such as SOUL.md").

**Guarded by:** `tests/test_harness_leftovers.py` — asserts the five paths
don't exist under `skills/` and that no `.md` under `skills/` mentions
`codex-tools.md`, `pi-tools.md`, `antigravity-tools.md`, `CREATION-LOG.md`,
or `CLAUDE_MD_TESTING`.

**Re-apply after re-sync:** nothing manual — `STRIP_PATHS` and the two new
`REPLACEMENTS` entries run automatically as part of `sync()`.

## skills/subagent-driven-development/SKILL.md

- **Section added:** `## Dispatching on Hermes`, inserted directly after the
  "Continuous execution" paragraph and before `## When to Use`.
- **What it says:** children start a fresh conversation with no parent
  history; a `delegate_task(...)` example for the implementer and a second
  one for the reviewer; a Rules list covering: children cannot call
  `clarify` (questions must be relayed by the orchestrator), REJECT verdicts
  trigger a fix-implementer dispatch (max 2 rounds then escalate), and
  `delegate_task` is not durable across a parent-turn interruption (hence
  commit-per-task).
- **Re-apply after re-sync:** re-insert the same section at the same
  anchor point (after "Continuous execution", before "## When to Use").

## skills/using-superpowers/SKILL.md

- **Section added:** `## Loading Skills on Hermes`, inserted after the "Red
  Flags" table and before `## Platform Adaptation`.
- **What it says:** every skill reference in the doc resolves to a
  `skill_view("superpowers:<name>")` call (with three concrete examples);
  the Hermes plugin's `pre_llm_call` hook auto-bootstraps this skill and
  re-injects HARD-GATE reminders, but that injection is a safety net, not a
  substitute for invoking the skill explicitly; `/sp-phase` only advances a
  phase-gated skill after the human partner has approved the current
  phase's output — the agent must not call it unilaterally.
- **Platform Adaptation list:** as of the harness-leftovers cleanup (see
  "Other-harness / dev-log leftovers removed" section below), the
  Codex/Pi/Antigravity bullets are gone — `sync_upstream.py`'s
  `REPLACEMENTS` now strips that whole block mechanically on re-sync. The
  list reads just `- Hermes: see "Loading Skills on Hermes" above`.
- **Re-apply after re-sync:** re-insert the `## Loading Skills on Hermes`
  section at the same anchor (after Red Flags, before Platform Adaptation).
  The Platform Adaptation list itself no longer needs a manual bullet
  insert — `REPLACEMENTS` produces the final Hermes-only list directly.

## skills/dispatching-parallel-agents/SKILL.md

- **Section replaced:** the "### 3. Dispatch in Parallel" subsection's
  example. The mechanical transform left the old `Subagent (general-purpose):`
  text-block example, which doesn't correspond to any real Hermes call.
  Replaced it with a `delegate_task(tasks=[...])` batch-call example (three
  task dicts, each with `goal`/`context`/`toolsets`) plus a paragraph on the
  `max_concurrent_children` cap (default 3, overridable via
  `DELEGATION_MAX_CONCURRENT_CHILDREN`) and what happens when a batch
  exceeds it (queued, not failed — but the queued tasks still need to be
  independent of any still-running task).
- **Re-apply after re-sync:** replace the "### 3. Dispatch in Parallel"
  example block with the same `delegate_task(tasks=[...])` batch form and
  concurrency-limit paragraph.

## skills/using-superpowers/references/pi-tools.md (historical — file removed)

- **Superseded:** this file was deleted in the "Other-harness / dev-log
  leftovers removed" cleanup above (`STRIP_PATHS`). The wording fix recorded
  below applied to it while it still existed in the tree; kept here only as
  a record — there is nothing left to re-apply.
- **Wording fix (not upstream-semantic, purely a mechanical-substitution
  artifact):** the `Task lists` section used to read "Older Superpowers
  docs may refer to `a markdown checklist`; treat that as the task-tracking
  action above" — the backtick-quoted phrase is where
  `sync_upstream.py`'s `TodoWrite` → `a markdown checklist` replacement
  landed verbatim inside a sentence, reading awkwardly. Reworded to
  "Older Superpowers docs may refer to maintaining a markdown checklist;
  treat that instruction as the task-tracking action described above." No
  semantic change — cosmetic smoothing of a mechanical replacement seam.
- **Re-apply after re-sync:** N/A — the file no longer exists post-cleanup;
  `STRIP_PATHS` deletes it again if a re-sync recreates it.

## Codex adversarial review (F5) — `Subagent (general-purpose):` template leftovers

- **What was wrong:** several skill docs synced from upstream before the
  `Subagent (general-purpose):` → `delegate_task` mapping existed still had
  the literal Claude-Code subagent-dispatch template header, which doesn't
  correspond to any real Hermes call and would confuse an agent trying to
  follow the doc literally.
- **Fix applied in two parts:**
  1. `REPLACEMENTS` in `tools_dev/sync_upstream.py` now includes
     `(r"Subagent \(general-purpose\):", "delegate_task child (fresh context):")`,
     so any **future** re-sync picks up the mapping automatically — no
     manual step needed going forward.
  2. Because a full re-sync would overwrite the hand-written sections
     documented above in this file, the mapping was also applied **in
     place** (one-off, via `python3 -c` importing `transform` from
     `tools_dev.sync_upstream`) to the 7 already-synced files that still
     had the old template text: `skills/subagent-driven-development/task-reviewer-prompt.md`,
     `skills/subagent-driven-development/implementer-prompt.md`,
     `skills/brainstorming/spec-document-reviewer-prompt.md`,
     `skills/using-superpowers/references/pi-tools.md`,
     `skills/requesting-code-review/code-reviewer.md`,
     `skills/writing-plans/plan-document-reviewer-prompt.md`,
     `skills/using-superpowers/references/antigravity-tools.md`.
- **Re-apply after re-sync:** nothing to do — `REPLACEMENTS` now covers this
  mapping mechanically, so a fresh sync will never regenerate the old
  template text.
- **Guarded by:** `tests/test_no_claude_toolnames.py::test_no_forbidden_toolnames`
  (added `r"Subagent \(general-purpose\)"` to `FORBIDDEN`).
- **Note:** of the 7 files listed above, `references/pi-tools.md` and
  `references/antigravity-tools.md` were later deleted entirely (see
  "Other-harness / dev-log leftovers removed"); the fix record for them is
  kept for history only.

## Codex adversarial review (R2) — pseudo-header → real `delegate_task(...)` call syntax

- **What was wrong:** `delegate_task child (fresh context): / description: / model: / prompt: |`
  was still a made-up pseudo-header, not a call an agent could copy-paste and
  run. It doesn't match the real signature (`delegate_task(goal, context,
toolsets)`) documented in `references/tool-mapping.md` and used correctly
  elsewhere (e.g. `skills/subagent-driven-development/SKILL.md`).
- **Fix applied (hand-edit, template body left byte-for-byte unchanged):**
  Replaced the pseudo-header in each affected template with a real
  `delegate_task(goal=..., context="""...""", toolsets=[...])` skeleton, plus
  a one-line note that the unchanged template body below the skeleton is the
  `context` value. Files touched:
  - `skills/subagent-driven-development/implementer-prompt.md`
  - `skills/subagent-driven-development/task-reviewer-prompt.md`
  - `skills/requesting-code-review/code-reviewer.md`
  - `skills/brainstorming/spec-document-reviewer-prompt.md` (not explicitly
    scoped by the review, but shared the same pseudo-header — fixed to keep
    the guard test green project-wide)
  - `skills/writing-plans/plan-document-reviewer-prompt.md` (same reason)
  - `skills/using-superpowers/references/antigravity-tools.md` — inline
    mention reworded from the pseudo-header string to
    ``the `delegate_task(goal, context, toolsets)` call skeleton``
  - `skills/using-superpowers/references/pi-tools.md` — same inline reword
  - `skills/requesting-code-review/SKILL.md` — "Dispatch a `general-purpose`
    subagent" reworded to "Dispatch a `delegate_task` child"
- **Guarded by:** `tests/test_no_claude_toolnames.py::test_no_forbidden_toolnames`
  — added `r"delegate_task child \(fresh context\):"` and
  `r"(?i)general-purpose subagent"` to `FORBIDDEN`.
- **Re-apply after re-sync:** if a future re-sync regenerates the pseudo-header
  (via the `REPLACEMENTS` mapping in `sync_upstream.py` that produced it),
  re-apply the same `delegate_task(...)` skeleton + one-line note in place of
  it in the files above that still exist. The two reference-doc inline
  mentions (`references/antigravity-tools.md`, `references/pi-tools.md`) are
  moot — both files were deleted in the "Other-harness / dev-log leftovers
  removed" cleanup and `STRIP_PATHS` keeps them gone.

## Tests

`tests/test_manual_fixups.py` asserts these fixups are present (child
constraints + question-relay wording, 2+ `delegate_task(` call sites in the
SDD skill, `skill_view("superpowers:` in using-superpowers, and
`max_concurrent_children` in dispatching-parallel-agents). Re-run
`python3 -m pytest tests/test_manual_fixups.py -v` after any re-sync to
confirm the fixups survived or need re-applying.
