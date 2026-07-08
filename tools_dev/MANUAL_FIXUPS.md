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
- **Platform Adaptation list:** added a line `- Hermes: see "Loading Skills
on Hermes" above` alongside the existing Codex/Pi/Antigravity entries.
- **Re-apply after re-sync:** re-insert the section at the same anchor
  (after Red Flags, before Platform Adaptation) and re-add the Hermes
  bullet to the Platform Adaptation list.

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

## skills/using-superpowers/references/pi-tools.md

- **Wording fix (not upstream-semantic, purely a mechanical-substitution
  artifact):** the `Task lists` section used to read "Older Superpowers
  docs may refer to `a markdown checklist`; treat that as the task-tracking
  action above" — the backtick-quoted phrase is where
  `sync_upstream.py`'s `TodoWrite` → `a markdown checklist` replacement
  landed verbatim inside a sentence, reading awkwardly. Reworded to
  "Older Superpowers docs may refer to maintaining a markdown checklist;
  treat that instruction as the task-tracking action described above." No
  semantic change — cosmetic smoothing of a mechanical replacement seam.
- **Re-apply after re-sync:** re-apply the same wording fix if the mechanical
  replacement regenerates the awkward phrasing.

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
  it in all 7 files above, and re-check the two reference-doc inline mentions.

## Tests

`tests/test_manual_fixups.py` asserts these fixups are present (child
constraints + question-relay wording, 2+ `delegate_task(` call sites in the
SDD skill, `skill_view("superpowers:` in using-superpowers, and
`max_concurrent_children` in dispatching-parallel-agents). Re-run
`python3 -m pytest tests/test_manual_fixups.py -v` after any re-sync to
confirm the fixups survived or need re-applying.
