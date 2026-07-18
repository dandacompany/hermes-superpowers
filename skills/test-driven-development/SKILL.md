---
name: test-driven-development
description: Use before production code; routes through Hermes' native RED-GREEN-REFACTOR workflow with Superpowers integration
---

# Test-Driven Development — Hermes Adapter

This is the stable `superpowers:test-driven-development` entry point. Hermes
Agent 0.18.0+ owns the RED-GREEN-REFACTOR rules; this adapter connects them to
the rest of the Superpowers workflow.

## Required native skill

Before writing production code, load:

```python
skill_view("test-driven-development")
```

Follow that skill in full. Its test-first rule, observed RED requirement,
minimal GREEN implementation, vertical tracer-bullet guidance, and refactor
gate are authoritative. If the flat skill is unavailable, stop and report that
hermes-superpowers requires Hermes Agent 0.18.0 or newer.

## Superpowers workflow delta

1. **Plan alignment:** implement only the current approved plan task. A green
   test does not authorize behavior outside that task or the approved spec.
2. **Fresh implementers:** when running under
   `superpowers:subagent-driven-development`, include strict TDD in every
   implementer brief. The implementer must report the RED and GREEN commands
   and their observed results.
3. **Testing pitfalls:** load
   [testing-anti-patterns.md](testing-anti-patterns.md) when introducing mocks,
   test-only production hooks, or large fixture/setup abstractions.
4. **Debugging:** if RED fails for an unexpected reason or GREEN remains red
   after a minimal implementation, stop changing code and load
   `superpowers:systematic-debugging`.
5. **Verification:** completing one RED-GREEN-REFACTOR cycle is not a completion
   claim. Run the relevant broader suite and load
   `superpowers:verification-before-completion` at the workflow's final gate.

Do not invoke `simplify-code` during RED or GREEN. Optional multi-agent cleanup
belongs after the approved implementation is green and only when the user
explicitly requests it.
