import importlib
import pytest


class FakeCtx:
    def __init__(self):
        self.tools, self.hooks, self.commands, self.skills = [], [], [], []

    def register_tool(self, name, toolset, schema, handler, **kwargs):
        assert isinstance(schema, dict) and schema.get("name") == name
        self.tools.append(name)

    def register_hook(self, event, handler):
        self.hooks.append(event)

    def register_command(self, name, handler, description="", args_hint=""):
        self.commands.append(name)

    def register_skill(self, name, path, description=""):
        assert hasattr(path, "exists") and path.exists()   # real API requires Path
        self.skills.append(name)


@pytest.fixture
def pkg(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_SUPERPOWERS_STATE_DIR", str(tmp_path))
    import __init__ as plugin
    importlib.reload(plugin)
    return plugin


def test_register_wires_everything(pkg):
    ctx = FakeCtx()
    pkg.register(ctx)
    assert "superpowers_phase" in ctx.tools
    assert {"pre_llm_call", "on_session_start", "post_tool_call"} <= set(ctx.hooks)
    assert {"superpowers", "sp-status", "sp-phase"} <= set(ctx.commands)


def test_register_registers_all_skill_dirs(pkg, tmp_path):
    ctx = FakeCtx()
    pkg.register(ctx)
    # skills/가 아직 비어 있으면 0개여도 register 자체는 성공해야 함
    from pathlib import Path
    expected = [d.name for d in (Path(pkg.__file__).parent / "skills").glob("*/") if (d / "SKILL.md").exists()]
    assert sorted(ctx.skills) == sorted(expected)


def test_register_survives_missing_register_skill(pkg):
    """register_skill이 없는 ctx는 스킬 등록만 건너뛰고 나머지는 성공해야 한다
    (스킬은 선택 기능 — 하나가 실패해도 플러그인 전체가 죽으면 안 됨)."""
    class MinimalCtx:
        def register_hook(self, *a, **k): pass
        def register_tool(self, *a, **k): pass
        def register_command(self, *a, **k): pass
    pkg.register(MinimalCtx())   # register_skill이 없어도 예외 전파 금지


def test_register_raises_when_hook_registration_fails(pkg):
    """훅/도구/커맨드 등록은 필수 기능이다 — 실패하면 예외를 전파해서 Hermes
    플러그인 로더가 플러그인을 errored로 표시하게 해야 한다 (fail-loud, F2)."""
    class BrokenCtx:
        def register_hook(self, *a, **k):
            raise RuntimeError("boom")
        def register_tool(self, *a, **k): pass
        def register_command(self, *a, **k): pass
        def register_skill(self, *a, **k): pass
    with pytest.raises(RuntimeError):
        pkg.register(BrokenCtx())


def test_register_skill_receives_path_object(pkg):
    ctx = FakeCtx()
    pkg.register(ctx)
    assert len(ctx.skills) == 14
    assert {
        "writing-plans",
        "systematic-debugging",
        "test-driven-development",
        "requesting-code-review",
    } <= set(ctx.skills)
