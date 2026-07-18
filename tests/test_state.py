import json
import threading

import pytest


@pytest.fixture
def state(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_SUPERPOWERS_STATE_DIR", str(tmp_path))
    import importlib
    import state as mod
    importlib.reload(mod)
    return mod


def test_default_phase_is_idle(state):
    assert state.load_phase("s1") == "idle"


def test_set_and_load_phase(state):
    state.set_phase("s1", "brainstorming")
    assert state.load_phase("s1") == "brainstorming"


def test_set_invalid_phase_raises(state):
    with pytest.raises(ValueError):
        state.set_phase("s1", "yolo")


def test_corrupt_state_file_falls_back_to_idle(state):
    state.set_phase("s1", "planning")
    (state.state_dir() / "s1.json").write_text("{broken json")
    assert state.load_phase("s1") == "idle"


def test_phases_order(state):
    assert state.PHASES == [
        "idle", "brainstorming", "design-approved", "planning",
        "plan-approved", "implementing", "reviewing", "done",
    ]


def test_reminder_before_implementing_contains_hard_gate(state):
    for p in ["idle", "brainstorming", "design-approved", "planning", "plan-approved"]:
        assert "HARD GATE" in state.reminder_for(p)
    assert "HARD GATE" not in state.reminder_for("implementing")


def test_escalation_roundtrip(state):
    assert not state.is_escalated("s1")
    state.escalate("s1")
    assert state.is_escalated("s1")
    state.clear_escalation("s1")
    assert not state.is_escalated("s1")


def test_session_id_is_sanitized_for_filename(state):
    state.set_phase("a/b:c", "brainstorming")   # 경로 탈출 문자
    assert state.load_phase("a/b:c") == "brainstorming"
    for f in state.state_dir().iterdir():
        assert "/" not in f.name.replace(f.suffix, "")


def test_write_is_atomic_no_tmp_stragglers(state):
    """_write는 임시 파일에 쓰고 os.replace로 교체해야 한다 (F3) — 중간에
    죽어도 손상된 상태 파일이 남지 않고, 완료 시 tmp 잔재도 없어야 한다."""
    state.set_phase("s1", "brainstorming")
    files = list(state.state_dir().iterdir())
    tmp_stragglers = [f for f in files if ".tmp" in f.name]
    assert not tmp_stragglers
    content = json.loads((state.state_dir() / "s1.json").read_text())
    assert content["phase"] == "brainstorming"


def test_sanitized_collision_maps_to_different_files(state):
    """서로 다른 session_id가 sanitize 후 같은 이름이 되면 상태가 섞인다 —
    원본 id의 sha1 앞 8자리를 붙여 구분해야 한다 (F4)."""
    state.set_phase("a/b:c", "brainstorming")
    state.set_phase("a_b_c", "planning")
    assert state.load_phase("a/b:c") == "brainstorming"
    assert state.load_phase("a_b_c") == "planning"
    p1 = state._path("a/b:c")
    p2 = state._path("a_b_c")
    assert p1 != p2


def test_concurrent_mutations_never_clobber_each_other(state):
    """set_phase and escalate run concurrently on the same session; the
    file-locked read-modify-write in _mutate must ensure neither writer's
    field is ever lost from the final state (F-race)."""
    state.set_phase("s1", "planning")  # seed phase before the race

    def spin_phase():
        for _ in range(50):
            state.set_phase("s1", "planning")

    def spin_escalate():
        for _ in range(50):
            state.escalate("s1")

    t1 = threading.Thread(target=spin_phase)
    t2 = threading.Thread(target=spin_escalate)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    raw = (state.state_dir() / "s1.json").read_text()
    data = json.loads(raw)  # must still be valid JSON, never torn
    assert data["phase"] == "planning"
    assert data["escalated"] is True
