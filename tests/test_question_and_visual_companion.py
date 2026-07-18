import importlib
import json
from pathlib import Path
from urllib.request import urlopen

import pytest


ROOT = Path(__file__).parents[1]


class FakeCtx:
    def __init__(self):
        self.tools = {}
        self.hooks = []
        self.commands = []
        self.skills = []

    def register_tool(self, name, toolset, schema, handler, **kwargs):
        self.tools[name] = {"schema": schema, "handler": handler, **kwargs}

    def register_hook(self, event, handler):
        self.hooks.append(event)

    def register_command(self, name, handler, **kwargs):
        self.commands.append(name)

    def register_skill(self, name, path, **kwargs):
        self.skills.append(name)


def read_skill(name):
    return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


def test_question_gate_is_explicit_and_reinjected(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_SUPERPOWERS_STATE_DIR", str(tmp_path / "state"))
    import hooks

    importlib.reload(hooks)
    using = read_skill("using-superpowers")
    brainstorming = read_skill("brainstorming")

    required = [
        "Every user-facing question MUST use `clarify`",
        "Never ask a user-facing question in plain assistant text",
        "one question per `clarify` call",
    ]
    for phrase in required:
        assert phrase in using
        assert phrase in brainstorming

    assert "visual companion offer MUST use `clarify`" in brainstorming
    injected = hooks.pre_llm_call("s1", "hello", [], False)["context"]
    assert "Every user-facing question MUST use clarify" in injected
    assert "plain assistant text" in injected


def test_visual_companion_is_registered_and_declared():
    import __init__ as plugin

    ctx = FakeCtx()
    plugin.register(ctx)
    assert "superpowers_visual_companion" in ctx.tools
    schema = ctx.tools["superpowers_visual_companion"]["schema"]
    assert schema["parameters"]["properties"]["action"]["enum"] == [
        "start", "show", "events", "status", "stop"
    ]
    manifest = (ROOT / "plugin.yaml").read_text(encoding="utf-8")
    assert "- superpowers_visual_companion" in manifest


def test_upstream_sync_preserves_hermes_brainstorming_contract(tmp_path):
    from tools_dev.sync_upstream import sync

    source = tmp_path / "source"
    dest = tmp_path / "dest"
    (source / "brainstorming").mkdir(parents=True)
    (source / "brainstorming" / "SKILL.md").write_text("upstream skill")
    (source / "brainstorming" / "visual-companion.md").write_text("upstream guide")
    (source / "brainstorming" / "server.js").write_text("new server")

    (dest / "brainstorming").mkdir(parents=True)
    (dest / "brainstorming" / "SKILL.md").write_text("Hermes clarify gate")
    (dest / "brainstorming" / "visual-companion.md").write_text("Hermes native tool")
    (dest / "brainstorming" / "server.js").write_text("old server")

    assert sync(source, dest) == ["brainstorming"]
    assert (dest / "brainstorming" / "SKILL.md").read_text() == "Hermes clarify gate"
    assert (dest / "brainstorming" / "visual-companion.md").read_text() == "Hermes native tool"
    assert (dest / "brainstorming" / "server.js").read_text() == "new server"


def test_visual_companion_end_to_end(tmp_path):
    import tools

    started = json.loads(tools.visual_companion_handler({
        "action": "start",
        "project_dir": str(tmp_path),
        "user_approved": True,
        "open_browser": False,
    }))
    assert started["ok"] is True
    session_dir = started["session_dir"]

    try:
        shown = json.loads(tools.visual_companion_handler({
            "action": "show",
            "session_dir": session_dir,
            "filename": "layout-options.html",
            "html": "<h2>Choose a layout</h2><div data-choice='a'>A</div>",
        }))
        assert shown["ok"] is True
        assert shown["url"] == started["url"]
        screen_url = started["url"].replace(
            "/?key=", "/files/layout-options.html?key="
        )
        with urlopen(screen_url, timeout=3) as response:
            page = response.read().decode("utf-8")
        assert "Choose a layout" in page

        status = json.loads(tools.visual_companion_handler({
            "action": "status", "session_dir": session_dir,
        }))
        assert status["ok"] is True
        assert status["running"] is True

        events = json.loads(tools.visual_companion_handler({
            "action": "events", "session_dir": session_dir,
        }))
        assert events == {"ok": True, "events": []}

        duplicate = json.loads(tools.visual_companion_handler({
            "action": "show",
            "session_dir": session_dir,
            "filename": "layout-options.html",
            "html": "<p>overwrite</p>",
        }))
        assert duplicate["ok"] is False
        assert "fresh filename" in duplicate["error"]
    finally:
        stopped = json.loads(tools.visual_companion_handler({
            "action": "stop", "session_dir": session_dir,
        }))
        assert stopped["ok"] is True


@pytest.mark.parametrize("filename", ["../escape.html", "nested/file.html", "x.txt"])
def test_visual_companion_rejects_unsafe_filenames(tmp_path, filename):
    import tools

    started = json.loads(tools.visual_companion_handler({
        "action": "start",
        "project_dir": str(tmp_path),
        "user_approved": True,
        "open_browser": False,
    }))
    try:
        result = json.loads(tools.visual_companion_handler({
            "action": "show",
            "session_dir": started["session_dir"],
            "filename": filename,
            "html": "<p>x</p>",
        }))
        assert result["ok"] is False
    finally:
        tools.visual_companion_handler({
            "action": "stop", "session_dir": started["session_dir"],
        })


def test_visual_companion_start_requires_explicit_approval(tmp_path):
    import tools

    result = json.loads(tools.visual_companion_handler({
        "action": "start",
        "project_dir": str(tmp_path),
        "open_browser": False,
    }))
    assert result["ok"] is False
    assert "user_approved=true" in result["error"]
