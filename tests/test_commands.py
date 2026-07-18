import importlib
import json
import pytest


@pytest.fixture
def mods(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_SUPERPOWERS_STATE_DIR", str(tmp_path))
    import state, commands, tools
    for m in (state, commands, tools):
        importlib.reload(m)
    return state, commands, tools


def test_status_shows_phase(mods):
    state, commands, _ = mods
    state.set_phase("default", "planning")
    out = commands.handle_status("")
    assert "planning" in out


def test_phase_transition(mods):
    state, commands, _ = mods
    out = commands.handle_phase("brainstorming")
    assert "brainstorming" in out
    assert state.load_phase("default") == "brainstorming"


def test_phase_invalid_lists_valid_phases(mods):
    _, commands, _ = mods
    out = commands.handle_phase("nope")
    assert "idle" in out and "implementing" in out   # 유효 목록 안내


def test_phase_tool_returns_json(mods):
    state, _, tools = mods
    res = json.loads(tools.phase_handler({"phase": "planning", "session_id": "s9"}))
    assert res["ok"] is True
    assert state.load_phase("s9") == "planning"


def test_phase_tool_error_is_json_not_exception(mods):
    _, _, tools = mods
    res = json.loads(tools.phase_handler({"phase": "bogus"}))
    assert res["ok"] is False


def test_superpowers_command_mentions_skills(mods):
    _, commands, _ = mods
    out = commands.handle_superpowers("")
    assert "using-superpowers" in out


def test_handlers_never_raise_even_on_state_failure(mods, monkeypatch):
    state, commands, tools_mod = mods
    def boom(*a, **k):
        raise OSError("disk on fire")
    monkeypatch.setattr(state, "load_phase", boom)
    monkeypatch.setattr(state, "set_phase", boom)
    assert isinstance(commands.handle_status(""), str)
    assert isinstance(commands.handle_phase("planning"), str)
    assert isinstance(commands.handle_superpowers(""), str)
    assert json.loads(tools_mod.phase_handler({"phase": "planning"}))["ok"] is False
