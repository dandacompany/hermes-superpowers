---
name: systematic-debugging
description: Use for bugs and failures; routes through Hermes' native root-cause workflow with Superpowers supporting techniques
---

# Systematic Debugging — Hermes Adapter

This is the stable `superpowers:systematic-debugging` entry point. Hermes Agent
0.18.0+ owns the core root-cause workflow; this adapter connects that workflow
to Superpowers' deeper techniques and completion gates.

## Required native skill

Before investigating or proposing a fix, load:

```python
skill_view("systematic-debugging")
```

Follow that skill in full. Its feedback-loop and root-cause rules are
authoritative. If the flat skill is unavailable, stop and report that
hermes-superpowers requires Hermes Agent 0.18.0 or newer.

## Superpowers workflow delta

Use these bundled references when the native four-phase process reaches the
matching situation:

- [root-cause-tracing.md](root-cause-tracing.md) — trace a bad value backward
  through callers until the original source is identified.
- [defense-in-depth.md](defense-in-depth.md) — after finding the root cause,
  add validation at appropriate boundaries without masking the source.
- [condition-based-waiting.md](condition-based-waiting.md) — replace arbitrary
  sleeps and timing guesses with observable conditions.
- `find-polluter.sh` — isolate order-dependent test pollution.

### Regression test

When the native workflow reaches implementation, load
`superpowers:test-driven-development` and create the smallest failing test that
reproduces the confirmed root cause. Do not write the fix before seeing that
test fail for the expected reason.

### Python state inspection

Load the flat Hermes skill below only when all of these are true:

- the failing system is Python;
- traceback, logs, `pytest --showlocals`, and the tight repro do not expose the
  incorrect state transition; and
- stepping, post-mortem inspection, or attaching to a long-running process is
  the next evidence-gathering action.

```python
skill_view("python-debugpy")
```

`python-debugpy` is an observation tool inside Phase 1, not a replacement for
root-cause analysis and not permission to patch by intuition.

### Completion

After the regression test and relevant suite pass, load
`superpowers:verification-before-completion` before claiming the bug is fixed.
