from pathlib import Path
import sys


ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from tools_dev.sync_upstream import ADAPTER_SKILLS, sync


SKILLS = ROOT / "skills"


def read_skill(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


def test_adapters_load_expected_flat_hermes_skills():
    expected = {
        "writing-plans": 'skill_view("plan")',
        "systematic-debugging": 'skill_view("systematic-debugging")',
        "test-driven-development": 'skill_view("test-driven-development")',
    }
    assert ADAPTER_SKILLS == set(expected)
    for adapter, invocation in expected.items():
        text = read_skill(adapter)
        assert invocation in text
        assert "Hermes Agent 0.18.0" in text


def test_writing_plans_adapter_preserves_superpowers_contract():
    text = read_skill("writing-plans")
    assert "explicitly" in text and "approved the design" in text
    assert "docs/superpowers/plans/" in text
    assert "Global Constraints" in text
    assert "Task interfaces" in text
    assert "No placeholders" in text
    assert "superpowers:subagent-driven-development" in text
    assert "superpowers:executing-plans" in text


def test_debugging_adapter_keeps_supporting_techniques_and_python_route():
    text = read_skill("systematic-debugging")
    for relative in (
        "root-cause-tracing.md",
        "defense-in-depth.md",
        "condition-based-waiting.md",
        "find-polluter.sh",
    ):
        assert relative in text
        assert (SKILLS / "systematic-debugging" / relative).exists()
    assert 'skill_view("python-debugpy")' in text
    assert "superpowers:verification-before-completion" in text


def test_tdd_adapter_keeps_superpowers_integration():
    text = read_skill("test-driven-development")
    assert "superpowers:subagent-driven-development" in text
    assert "testing-anti-patterns.md" in text
    assert "superpowers:systematic-debugging" in text
    assert "superpowers:verification-before-completion" in text


def test_requesting_review_remains_requirements_review_not_native_adapter():
    text = read_skill("requesting-code-review")
    assert "PLAN_OR_REQUIREMENTS" in text
    assert "code-reviewer.md" in text
    assert 'skill_view("requesting-code-review")' not in text


def test_sync_preserves_adapters_and_refreshes_mirrored_skills(tmp_path):
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source.mkdir()
    dest.mkdir()

    for name in ADAPTER_SKILLS:
        source_dir = source / name
        source_dir.mkdir()
        (source_dir / "SKILL.md").write_text(
            f"---\nname: {name}\n---\nupstream body\n", encoding="utf-8"
        )
        dest_dir = dest / name
        dest_dir.mkdir()
        (dest_dir / "SKILL.md").write_text(
            f"---\nname: {name}\n---\nadapter sentinel\n", encoding="utf-8"
        )

    mirrored = source / "brainstorming"
    mirrored.mkdir()
    (mirrored / "SKILL.md").write_text(
        "---\nname: brainstorming\n---\nUse AskUserQuestion.\n",
        encoding="utf-8",
    )

    synced = sync(source, dest)

    assert synced == ["brainstorming"]
    for name in ADAPTER_SKILLS:
        assert "adapter sentinel" in (dest / name / "SKILL.md").read_text(
            encoding="utf-8"
        )
    refreshed = (dest / "brainstorming" / "SKILL.md").read_text(encoding="utf-8")
    assert "clarify" in refreshed
    assert "Hermes port note" in refreshed
