"""skills/ 안에 Claude 하네스 도구명이 잔존하면 실패."""
import re
from pathlib import Path

SKILLS = Path(__file__).parent.parent / "skills"
FORBIDDEN = [
    r"\bAskUserQuestion\b",
    r"\bTodoWrite\b",
    r"\bTask tool\b",
    r"\bSkill tool\b",
    r"\bsubagent_type\b",
    r"Subagent \(general-purpose\)",
    r"delegate_task child \(fresh context\):",
    r"(?i)general-purpose subagent",
]


def test_skills_dir_has_14_skills():
    dirs = [d for d in SKILLS.iterdir() if (d / "SKILL.md").is_file()]
    assert len(dirs) == 14


def test_three_public_entries_are_native_adapters():
    from tools_dev.sync_upstream import ADAPTER_SKILLS

    assert ADAPTER_SKILLS == {
        "writing-plans",
        "systematic-debugging",
        "test-driven-development",
    }
    assert all((SKILLS / name / "SKILL.md").is_file() for name in ADAPTER_SKILLS)


def test_no_forbidden_toolnames():
    offenders = []
    for md in SKILLS.rglob("*.md"):
        text = md.read_text(encoding="utf-8")
        for pat in FORBIDDEN:
            if re.search(pat, text):
                offenders.append(f"{md}: {pat}")
    assert not offenders, "\n".join(offenders)


def test_delegate_task_present_in_sdd_skill():
    sdd = (SKILLS / "subagent-driven-development" / "SKILL.md").read_text(encoding="utf-8")
    assert "delegate_task" in sdd
    assert "clarify" in sdd


def test_sync_transform_does_not_emit_forbidden_strings():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from tools_dev.sync_upstream import transform
    out = transform("Subagent (general-purpose):\n  description: x")
    for pat in FORBIDDEN:
        assert not re.search(pat, out), pat
