---
name: using-superpowers
description: Use when starting any conversation - establishes how to find and use skills, requiring skill invocation before ANY response including clarifying questions
---

> **Hermes port note:** tool names in this document are mapped for Hermes Agent (see references/tool-mapping.md in the plugin root): subagents = `delegate_task`, user questions = `clarify`, skill loads = `skill_view("superpowers:<name>")`.

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, ignore this skill.
</SUBAGENT-STOP>

<HERMES-QUESTION-GATE>
Every user-facing question MUST use `clarify`. Never ask a user-facing question in plain assistant text. Ask exactly one question per `clarify` call; if a topic needs more exploration, make separate calls after each answer.

This includes clarification, feedback, approval, review, and offers such as the visual companion. Rhetorical prose that does not request an answer is not a user-facing question. Terminal safety approval remains owned by the terminal tool. A `delegate_task` child cannot call `clarify`; it must return a `QUESTIONS` section so the orchestrator can ask.

After the user has approved the Visual Companion via `clarify`, a genuinely visual choice may be presented with `superpowers_visual_companion` instead. Do not duplicate that browser question in plain assistant text. Any follow-up that expects a terminal answer returns to `clarify`.
</HERMES-QUESTION-GATE>

<EXTREMELY-IMPORTANT>
If you think there is even a 1% chance a skill might apply to what you are doing, you ABSOLUTELY MUST invoke the skill.

IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.

This is not negotiable. You cannot rationalize your way out of this.
</EXTREMELY-IMPORTANT>

## The Rule

**Invoke relevant or requested skills BEFORE any response or action** — including clarifying questions, exploring the codebase, or checking files. If it turns out wrong for the situation, you don't have to use it.

**Before entering plan mode:** if you haven't already brainstormed, invoke the brainstorming skill first.

Then announce "Using [skill] to [purpose]" and follow the skill exactly. If it has a checklist, create a todo per item.

## Skill Priority

When multiple skills apply, process skills come first — they set the approach, then implementation skills (frontend-design, etc.) carry it out. Brainstorming and systematic-debugging are Superpowers' most common process skills, but the rule holds for any of them.

- "Let's build X" → superpowers:brainstorming first, then implementation skills.
- "Fix this bug" → superpowers:systematic-debugging first, then domain skills.

## Red Flags

These thoughts mean STOP—you're rationalizing:

| Thought | Reality |
|---------|---------|
| "This is just a simple question" | Questions are tasks. Check for skills. |
| "I need more context first" | Skill check comes BEFORE clarifying questions. |
| "Let me explore the codebase first" | Skills tell you HOW to explore. Check first. |
| "I can check git/files quickly" | Files lack conversation context. Check for skills. |
| "Let me gather information first" | Skills tell you HOW to gather information. |
| "This doesn't need a formal skill" | If a skill exists, use it. |
| "I remember this skill" | Skills evolve. Read current version. |
| "This doesn't count as a task" | Action = task. Check for skills. |
| "The skill is overkill" | Simple things become complex. Use it. |
| "I'll just do this one thing first" | Check BEFORE doing anything. |
| "This feels productive" | Undisciplined action wastes time. Skills prevent this. |
| "I know what that means" | Knowing the concept ≠ using the skill. Invoke it. |

## Loading Skills on Hermes

Every skill reference in this document — including the ones above — resolves
to a `skill_view` call, not a file read. Load a skill with:

```python
skill_view("superpowers:brainstorming")
skill_view("superpowers:systematic-debugging")
skill_view("superpowers:subagent-driven-development")
```

Hermes 0.18.0+ also ships flat, built-in development skills. This plugin does
not override them: plugin skills are explicitly namespaced as
`superpowers:<name>` and coexist with flat names. Three stable Superpowers
entry points are Hermes-native adapters:

| Superpowers entry point               | Native skill loaded by the adapter |
| ------------------------------------- | ---------------------------------- |
| `superpowers:writing-plans`           | `plan`                             |
| `superpowers:systematic-debugging`    | `systematic-debugging`             |
| `superpowers:test-driven-development` | `test-driven-development`          |

Always enter through the namespaced Superpowers skill while following this
workflow. The adapter loads the native skill and then adds the design gate,
plan/SDD contract, supporting references, and completion rules.

Two other flat skills are helpers, not replacements:

- Load `simplify-code` only after implementation is green and only when the
  user explicitly requests cleanup or simplification.
- Load `python-debugpy` from systematic debugging only when a Python problem
  genuinely requires stepping, post-mortem inspection, or process attach.
- Keep `superpowers:requesting-code-review` for requirements/plan compliance.
  The flat `requesting-code-review` is a separate pre-commit security and
  quality gate and may run afterward when the user is preparing to commit,
  push, or merge.

The Hermes plugin also injects reminders on its own: a `pre_llm_call` hook
bootstraps this skill at conversation start and re-injects HARD-GATE
reminders (e.g. "no implementation before brainstorming approval") as the
conversation continues, so you will see this guidance again even if you
don't call `skill_view` yourself. That injection is a safety net, not a
substitute — invoke the skill explicitly per the rule above rather than
waiting for the reminder.

**`/sp-phase` transitions:** phase-gated skills (brainstorming → plan →
implementation) only advance via `/sp-phase` once your human partner has
approved the current phase's output. Do not call `/sp-phase` to move
yourself into implementation on your own judgment — that call is the
partner's approval, not a bookkeeping step you perform for them.

## Platform Adaptation

- Hermes: see "Loading Skills on Hermes" above

## User Instructions

User instructions (host instruction files such as SOUL.md, and direct requests) take precedence over skills, which in turn override default behavior. Only skip skill workflows or instructions when your human partner has explicitly told you to.
