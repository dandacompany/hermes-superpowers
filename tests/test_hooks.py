import importlib
import pytest


@pytest.fixture
def mods(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_SUPERPOWERS_STATE_DIR", str(tmp_path))
    import state, hooks
    importlib.reload(state)
    importlib.reload(hooks)
    return state, hooks


def test_first_turn_injects_bootstrap(mods):
    state, hooks = mods
    out = hooks.pre_llm_call("s1", "hello", [], is_first_turn=True)
    assert "superpowers" in out["context"].lower()
    assert len(out["context"]) > 500          # 전문 주입 (한 줄 리마인더가 아님)


def test_later_turns_inject_phase_reminder(mods):
    state, hooks = mods
    state.set_phase("s1", "brainstorming")
    out = hooks.pre_llm_call("s1", "next", [], is_first_turn=False)
    assert "HARD GATE" in out["context"]
    assert len(out["context"]) < 500          # 리마인더는 한 줄급


def test_done_phase_still_returns_context(mods):
    state, hooks = mods
    state.set_phase("s1", "done")
    out = hooks.pre_llm_call("s1", "next", [], is_first_turn=False)
    assert "done" in out["context"]


def test_pre_llm_call_never_raises(mods, monkeypatch):
    state, hooks = mods
    monkeypatch.setattr(hooks, "bootstrap_text", lambda: 1 / 0)
    out = hooks.pre_llm_call("s1", "x", [], is_first_turn=True)
    assert out == {} or isinstance(out, dict)


def test_post_tool_call_escalates_on_gated_write(mods):
    state, hooks = mods
    state.set_phase("s1", "brainstorming")
    hooks.post_tool_call("write_file", {"path": "a.py"}, "ok", task_id="s1")
    assert state.is_escalated("s1")
    out = hooks.pre_llm_call("s1", "x", [], is_first_turn=False)
    assert "WARNING" in out["context"]
    # 경고는 1회 소비 후 해제
    assert not state.is_escalated("s1")


def test_post_tool_call_uses_session_id_over_task_id(mods):
    """실제 Hermes post_tool_call은 session_id kwarg를 전달한다 — task_id와
    충돌하면 session_id가 우선해야 한다 (F1)."""
    state, hooks = mods
    state.set_phase("s2", "brainstorming")
    hooks.post_tool_call(
        "write_file", {"path": "a.py"}, "ok",
        task_id="s1", session_id="s2")
    assert state.is_escalated("s2")
    assert not state.is_escalated("s1")


def test_post_tool_call_ignores_write_when_implementing(mods):
    state, hooks = mods
    state.set_phase("s1", "implementing")
    hooks.post_tool_call("write_file", {}, "ok", task_id="s1")
    assert not state.is_escalated("s1")


def test_post_tool_call_ignores_readonly_tools(mods):
    state, hooks = mods
    state.set_phase("s1", "idle")
    hooks.post_tool_call("web_search", {}, "ok", task_id="s1")
    assert not state.is_escalated("s1")


def test_on_session_start_resets_to_idle(mods):
    state, hooks = mods
    state.set_phase("s1", "implementing")
    hooks.on_session_start("s1")
    assert state.load_phase("s1") == "idle"
