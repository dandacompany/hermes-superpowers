# Codex adversarial review — findings & disposition

Source: Codex adversarial review pass on branch `feat/plugin-core`. Verified
against actual Hermes platform behavior (hook kwargs, real tool names,
plugin-loader error handling) before fixing.

## Findings

1. **F1 (High)** — `hooks.post_tool_call` keyed session state off `task_id`
   only; the real Hermes `post_tool_call` kwarg is `session_id`, so
   escalation could land on/read from the wrong session (or never fire) once
   a real `session_id` diverges from `task_id`.
2. **F1b (High, discovered during F1 verification)** — `WRITE_TOOLS` listed
   tool names (`file_edit`, `file_write`, `create_file`, `str_replace_editor`,
   `apply_patch`) that don't exist on Hermes; the real write tools are
   `write_file` and `patch`. As shipped, the escalation path could never
   fire against a live Hermes session.
3. **F2 (High)** — `__init__.py`'s `register(ctx)` wrapped every
   registration (hooks, tool, commands, skills) in `_safe`, which swallows
   exceptions. A broken hook/tool/command registration would silently leave
   the plugin running with zero enforcement instead of surfacing as an
   errored plugin in `/plugins`.
4. **F3 (Medium)** — `state._write` wrote directly to the target JSON file
   (`Path.write_text`), which is not atomic; a crash or concurrent read
   mid-write could observe a truncated/corrupt state file.
5. **F4 (Medium)** — `state._path` sanitizes session ids with a regex
   substitution but two distinct ids can collapse to the same sanitized
   filename (e.g. `"a/b:c"` and `"a_b_c"` both sanitize to `a_b_c.json`),
   silently merging unrelated sessions' state.
6. **F5 (Medium)** — Several skill docs synced from upstream (before the
   Hermes tool-mapping existed) still contained the literal Claude-Code
   `Subagent (general-purpose):` dispatch template, which doesn't correspond
   to any real Hermes call.
7. **F6 (Low, rejected)** — The bootstrap text's "user instructions take
   precedence" wording was flagged as a potential prompt-injection risk.
8. **R1 (Medium)** — `state.set_phase`/`escalate`/`clear_escalation` each did
   a separate `_read()` then `_write()`; concurrent mutations on the same
   session could race and clobber each other's field.
9. **R2 (Medium)** — The F5 fix mapped the old Claude-Code template to a new
   string, `delegate_task child (fresh context): / description: / model: /
prompt: |`, but that string is still a pseudo-header, not the real
   `delegate_task(goal, context, toolsets)` call syntax used elsewhere in the
   plugin — an agent following the template literally still couldn't copy it
   into a working call.

## Disposition

| #   | Finding                                               | Disposition                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| --- | ----------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| F1  | session key mismatch (`task_id` vs `session_id`)      | **Fixed** — `hooks.py` `post_tool_call` now uses `kwargs.get("session_id") or task_id or "default"`. Test: `tests/test_hooks.py::test_post_tool_call_uses_session_id_over_task_id`.                                                                                                                                                                                                                                                                                                                                                                                         |
| F1b | wrong `WRITE_TOOLS` names                             | **Fixed** — `WRITE_TOOLS = {"write_file", "patch"}` in `hooks.py`; README.md/README.ko.md hook-behavior sections updated to match; existing tests switched from `file_edit` to `write_file`.                                                                                                                                                                                                                                                                                                                                                                                |
| F2  | fail-open `register()`                                | **Fixed** — `__init__.py` now calls `ctx.register_hook`/`register_tool`/`register_command` directly (no `_safe`), so a broken registration raises and the Hermes plugin loader marks the plugin errored. `_safe` retained only for the optional per-skill `register_skill` loop. Tests: `tests/test_register.py::test_register_survives_missing_register_skill`, `::test_register_raises_when_hook_registration_fails`.                                                                                                                                                     |
| F3  | non-atomic state writes                               | **Fixed** — `state._write` now writes to a `tempfile.NamedTemporaryFile(dir=state_dir())` and `os.replace`s onto the target; never-raise contract preserved. Test: `tests/test_state.py::test_write_is_atomic_no_tmp_stragglers`.                                                                                                                                                                                                                                                                                                                                           |
| F4  | sanitized session-id collision                        | **Fixed** — `state._path` appends `-<sha1(original)[:8]>` whenever sanitization changes the id. Test: `tests/test_state.py::test_sanitized_collision_maps_to_different_files`.                                                                                                                                                                                                                                                                                                                                                                                              |
| F5  | Claude-style subagent template in `skills/`           | **Fixed** — added `(r"Subagent \(general-purpose\):", "delegate_task child (fresh context):")` to `tools_dev/sync_upstream.py` `REPLACEMENTS` (covers future re-syncs automatically) and applied the same transform in place to the 7 already-synced files that still had the old text, without a full re-sync (which would have wiped `tools_dev/MANUAL_FIXUPS.md`'s hand-written sections). Recorded in `tools_dev/MANUAL_FIXUPS.md`. Guard test: `tests/test_no_claude_toolnames.py::test_no_forbidden_toolnames` (added `Subagent \(general-purpose\)` to `FORBIDDEN`). |
| F6  | "user instructions take precedence" bootstrap wording | **Rejected** — this is upstream philosophy retained by design (a no-hard-blocking spec decision, consistent with "Differences from upstream" in README.md/README.ko.md); not a defect to fix.                                                                                                                                                                                                                                                                                                                                                                               |
| F7  | (register-loop related)                               | Covered by F2's fixes and tests above.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| R1  | state.py read-modify-write race                       | **Fixed** — added `state._mutate(session_id, fn)`, which holds an exclusive `fcntl.flock` on a per-session `<state file>.lock` around read→modify→write; `fcntl` import wrapped in `try/except` (no-op unlocked fallback on non-POSIX platforms, and on lock-acquisition failure — never-raise contract preserved). `set_phase`/`escalate`/`clear_escalation` now route through it. Test: `tests/test_state.py::test_concurrent_mutations_never_clobber_each_other`.                                                                                                        |
| R2  | SDD/review templates still pseudo-headers             | **Fixed** — replaced the `delegate_task child (fresh context): / description: / model: / prompt:                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | `pseudo-header in the affected templates with a real`delegate_task(goal=..., context="""...""", toolsets=[...])`skeleton (template body left unchanged, one-line note that it fills`context`); reworded the two inline mentions in `antigravity-tools.md`/`pi-tools.md`and the "general-purpose subagent" phrase in`requesting-code-review/SKILL.md`. Recorded in `tools_dev/MANUAL_FIXUPS.md`. Guard test: `tests/test_no_claude_toolnames.py::test_no_forbidden_toolnames`(added`delegate_task child \(fresh context\):`and case-insensitive`general-purpose subagent`to`FORBIDDEN`). |

## Re-review plan

1. Re-run the full suite (`python3 -m pytest tests/ -q`) after any future
   change to `hooks.py`, `__init__.py`, or `state.py` to confirm the F1–F4
   regression tests still pass.
2. After any future `tools_dev/sync_upstream.py --source ... --dest skills`
   re-sync, run `tests/test_no_claude_toolnames.py` and
   `tests/test_manual_fixups.py` to confirm the F5 mapping and manual
   fixups both survived regeneration (the F5 mapping is now mechanical, so
   this should be a no-op check rather than a required manual step).
3. Spot-check `/plugins` in a live Hermes session after any `register()`
   change to confirm a deliberately broken registration still surfaces as
   an errored plugin (fail-loud contract from F2), rather than relying on
   unit tests alone.
