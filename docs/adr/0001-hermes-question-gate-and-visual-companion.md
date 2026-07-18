# ADR 0001: Hermes question gate and Visual Companion

- Status: Accepted
- Date: 2026-07-18

## Context

Hermes provides `clarify` as its structured user-question interface. The
upstream Superpowers skills can otherwise emit questions as ordinary assistant
text, and its Visual Companion is exposed primarily through shell scripts.
Hermes needs an explicit question policy and a native tool lifecycle without
losing the upstream brainstorming assets.

## Decision

1. Every textual user-facing question must use `clarify`, one question per
   call. The rule is present in the core skills and is reinjected by the
   pre-LLM hook on every turn.
2. A visual question may use Visual Companion only after the user accepts the
   companion through `clarify`. Delegated workers relay questions to the parent
   instead of asking users directly.
3. Hermes registers `superpowers_visual_companion` with `start`, `show`,
   `events`, `status`, and `stop` actions. `start` rejects calls unless
   `user_approved` is explicitly `true`.
4. Upstream sync preserves the Hermes-specific brainstorming instructions and
   Visual Companion guide while continuing to refresh the upstream runtime
   assets.

## Consequences

- The repeated hook instruction makes accidental plain-text questions much
  less likely, but it remains a model instruction rather than an output
  interceptor.
- Visual Companion approval is a hard tool-level check.
- Visual content is restricted to fresh flat HTML filenames inside the active
  session, and the existing tokenized local server remains responsible for
  browser authentication and event capture.
- Maintainers must review upstream changes to the two protected brainstorming
  documents manually during sync.
