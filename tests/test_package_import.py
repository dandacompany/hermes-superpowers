import importlib
import shutil
import sys


def test_plugin_loads_as_package(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_SUPERPOWERS_STATE_DIR", str(tmp_path / "state"))
    pkg_parent = tmp_path / "plugins"
    pkg_dir = pkg_parent / "superpowers"
    pkg_dir.mkdir(parents=True)
    import pathlib
    repo = pathlib.Path(__file__).resolve().parent.parent
    for f in ["__init__.py", "state.py", "hooks.py", "commands.py", "tools.py", "plugin.yaml"]:
        shutil.copy(repo / f, pkg_dir / f)
    # skills/는 없어도 로드돼야 함 (등록 0개 허용)
    monkeypatch.syspath_prepend(str(pkg_parent))
    for m in list(sys.modules):
        if m == "superpowers" or m.startswith("superpowers."):
            del sys.modules[m]
    pkg = importlib.import_module("superpowers")

    class FakeCtx:
        def __init__(self):
            self.hooks, self.tools, self.commands, self.skills = [], [], [], []
        def register_hook(self, e, h): self.hooks.append(e)
        def register_tool(self, name, toolset, schema, handler, **kwargs):
            assert isinstance(schema, dict) and schema.get("name") == name
            self.tools.append(name)
        def register_command(self, n, h, description="", args_hint=""): self.commands.append(n)
        def register_skill(self, name, path, description=""):
            assert hasattr(path, "exists") and path.exists()
            self.skills.append(name)

    ctx = FakeCtx()
    pkg.register(ctx)
    assert {"pre_llm_call", "on_session_start", "post_tool_call"} <= set(ctx.hooks)
    assert "superpowers_phase" in ctx.tools
    assert {"superpowers", "sp-status", "sp-phase"} <= set(ctx.commands)
