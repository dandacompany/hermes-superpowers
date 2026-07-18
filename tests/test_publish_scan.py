"""Hermes skills_guard 스캔 회귀 — dangerous verdict 재발 방지 (hermes 소스 있을 때만)."""
from pathlib import Path

import pytest

HERMES_SRC = Path.home() / ".hermes" / "hermes-agent"
pytestmark = pytest.mark.skipif(
    not HERMES_SRC.is_dir(), reason="hermes-agent source not available"
)


def _load_scan_skill():
    # 플러그인 루트의 tools.py가 sys.modules['tools']를 선점하므로
    # hermes의 tools 패키지와 충돌하지 않게 파일 경로로 직접 로드한다.
    import importlib.util

    path = HERMES_SRC / "tools" / "skills_guard.py"
    spec = importlib.util.spec_from_file_location("_hermes_skills_guard", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.scan_skill


def test_no_dangerous_scan_verdicts():
    scan_skill = _load_scan_skill()

    skills = Path(__file__).parent.parent / "skills"
    bad = []
    for d in sorted(skills.iterdir()):
        if not (d / "SKILL.md").exists():
            continue
        r = scan_skill(d)
        if r.verdict == "dangerous":
            crits = [f"{f.file}:{f.line} [{f.pattern_id}]" for f in r.findings if f.severity == "critical"]
            bad.append(f"{d.name}: {crits}")
    assert not bad, "\n".join(bad)
