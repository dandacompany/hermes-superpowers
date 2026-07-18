from pathlib import Path

SKILLS = Path(__file__).parent.parent / "skills"


def read(name):
    return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


def test_sdd_documents_child_constraints():
    sdd = read("subagent-driven-development")
    assert "no parent history" in sdd.lower() or "fresh conversation" in sdd.lower()
    assert "question" in sdd.lower()          # 질문 중계 프로토콜
    assert 'toolsets=["terminal", "file"]' in sdd or "toolsets" in sdd


def test_sdd_has_implementer_and_reviewer_dispatch():
    sdd = read("subagent-driven-development")
    assert sdd.count("delegate_task(") >= 2   # 구현자 + 리뷰어 예시 코드


def test_using_superpowers_points_to_skill_view():
    us = read("using-superpowers")
    # Header port-note alone would only produce one hit; require the real
    # "Loading Skills on Hermes" section (with its skill_view examples) too.
    assert us.count('skill_view("superpowers:') >= 3


def test_parallel_dispatch_mentions_concurrency_limit():
    dp = read("dispatching-parallel-agents")
    assert "max_concurrent_children" in dp


def test_using_superpowers_documents_hybrid_routing():
    us = read("using-superpowers")
    assert "explicitly namespaced" in us
    assert "coexist with flat names" in us
    assert "`simplify-code`" in us
    assert "`python-debugpy`" in us
    assert "separate pre-commit" in us
