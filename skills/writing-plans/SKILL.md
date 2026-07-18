---
name: writing-plans
description: Use after design approval to create a Superpowers execution plan through Hermes' built-in plan skill
---

# Writing Plans — Hermes Adapter

This is the stable `superpowers:writing-plans` entry point. Hermes Agent 0.18.0+
already ships the underlying plan-writing craft, so this adapter loads the
native skill and adds only the Superpowers workflow contract.

## Required native skill

Before writing or editing a plan, load:

```python
skill_view("plan")
```

Follow that skill in full. Its planning-only guard applies: inspect with
read-only tools, do not implement, and do not modify project files other than
the plan document.

If the flat `plan` skill is unavailable, stop and tell the user that
hermes-superpowers requires Hermes Agent 0.18.0 or newer. Do not silently fall
back to an improvised plan.

## Superpowers workflow delta

Apply all of these additions after loading `plan`:

1. **Design gate:** enter this skill only after the user has explicitly
   approved the design produced by `superpowers:brainstorming`. If approval is
   missing, return to brainstorming; do not infer approval.
2. **Plan location:** save to
   `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`. This explicit plugin
   path overrides the built-in skill's `.hermes/plans/` default.
3. **Global constraints:** copy project-wide requirements from the approved
   spec verbatim into a `## Global Constraints` section.
4. **Task interfaces:** for every task that depends on another task, state the
   exact interface it consumes and produces: function names, parameters,
   return types, schemas, file formats, or commands.
5. **Checklist steps:** use `- [ ]` for every implementation step so progress
   can be resumed safely.
6. **No placeholders:** no `TBD`, `TODO`, “add validation”, “handle errors”, or
   “similar to Task N”. Include exact paths, complete code where code changes,
   exact commands, and expected results.
7. **Task boundary:** each task must produce one independently testable unit
   that a fresh reviewer could approve or reject without evaluating unrelated
   work.
8. **Self-review:** before presenting the plan, verify spec coverage, scan for
   placeholders, and check that names and types are consistent across tasks.

Every plan starts with:

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` (recommended) or
> `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** [one sentence]

**Architecture:** [2-3 sentences]

**Tech Stack:** [key technologies]

## Global Constraints

[approved project-wide constraints]
```

## Handoff

After the user approves the completed plan, offer two execution paths:

1. **Subagent-Driven** — load
   `superpowers:subagent-driven-development`; use a fresh implementer and
   reviewer for each task.
2. **Inline Execution** — load `superpowers:executing-plans`; execute in
   batches with human checkpoints.

Do not start either path until the user approves the plan and the workflow has
transitioned to `plan-approved`.
