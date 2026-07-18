# Hermes-Native Skill Adapters Implementation Plan

> **For agentic workers:** Execute this plan task-by-task. Preserve the public `superpowers:*` skill names while delegating overlapping process knowledge to Hermes built-ins.

**Goal:** Convert the three overlapping Superpowers skills into thin Hermes-native adapters, keep the non-equivalent review contract, and document optional routing to `simplify-code` and `python-debugpy`.

**Architecture:** The plugin remains the workflow and compatibility layer. `superpowers:writing-plans`, `superpowers:systematic-debugging`, and `superpowers:test-driven-development` stay registered, but each adapter loads its corresponding flat Hermes built-in and adds only the Superpowers-specific delta. Upstream sync skips these adapter-owned skill directories so a future mirror refresh cannot overwrite them.

**Tech Stack:** Markdown agent skills, Python sync/test tooling, Hermes plugin skill registry.

## Global Constraints

- Preserve all 14 public `superpowers:*` skill names.
- Do not replace `superpowers:requesting-code-review`; its requirements-oriented review contract differs from the Hermes pre-commit verification skill.
- Do not make `simplify-code` mandatory; its own contract requires explicit user intent.
- Route `python-debugpy` only after systematic evidence gathering identifies a Python stepping/inspection need.
- Require Hermes Agent 0.18.0 or newer, where the referenced built-in development skills are present.

### Task 1: Add adapter contracts and sync protection

**Files:**

- Modify: `skills/writing-plans/SKILL.md`
- Modify: `skills/systematic-debugging/SKILL.md`
- Modify: `skills/test-driven-development/SKILL.md`
- Modify: `tools_dev/sync_upstream.py`
- Modify: `tools_dev/MANUAL_FIXUPS.md`

- [x] Replace each mirrored skill body with a short adapter that invokes the flat Hermes built-in via `skill_view("<name>")` and preserves the plugin-specific workflow delta.
- [x] Add an adapter-owned skill allowlist to `sync_upstream.py`; skip those directories during upstream copy.
- [x] Document why these three skills are intentionally no longer near-verbatim mirrors.

### Task 2: Update workflow routing

**Files:**

- Modify: `skills/using-superpowers/SKILL.md`
- Modify: `skills/brainstorming/SKILL.md`
- Modify: `state.py`
- Modify: `skills/subagent-driven-development/SKILL.md`

- [x] Keep namespaced adapter entry points in the phase workflow.
- [x] Document built-in routing inside the Hermes loading section.
- [x] Add optional `simplify-code` after implementation and before final review, only on explicit request.
- [x] Add conditional `python-debugpy` routing from systematic debugging for Python state inspection.
- [x] Keep final whole-branch review on `superpowers:requesting-code-review` and distinguish it from the flat Hermes pre-commit gate.

### Task 3: Update public positioning and compatibility documentation

**Files:**

- Modify: `plugin.yaml`
- Modify: `README.md`
- Modify: `README.ko.md`
- Modify: `UPSTREAM.md`
- Modify: `references/tool-mapping.md`

- [x] Change the positioning from a pure 14-skill mirror to a 14-entry hybrid Hermes-native port.
- [x] State the Hermes 0.18.0+ requirement.
- [x] Explain that plugin skills are namespaced and coexist with built-ins rather than overriding them.
- [x] Document the three adapters, the preserved review skill, and optional helper routing.

### Task 4: Add regression tests

**Files:**

- Modify: `tests/test_manual_fixups.py`
- Modify: `tests/test_no_claude_toolnames.py`
- Modify: `tests/test_register.py`
- Create: `tests/test_builtin_adapters.py`

- [x] Assert that all three adapter files load the intended flat built-in.
- [x] Assert that adapters retain required Superpowers deltas.
- [x] Assert that sync skips adapter-owned directories while syncing the remaining upstream skills.
- [x] Preserve the 14-skill registration contract.

### Task 5: Verify

- [x] Run `pytest tests/ -q`.
- [x] Run the publish/security scan tests.
- [x] Load the plugin registration in a smoke fixture and verify all 14 names remain.
- [x] Review the focused implementation diff and separately identify concurrent unrelated formatting changes already present in the shared working tree.
