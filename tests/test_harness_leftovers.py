from pathlib import Path

SKILLS = Path(__file__).parent.parent / "skills"
REMOVED = [
    "using-superpowers/references/codex-tools.md",
    "using-superpowers/references/pi-tools.md",
    "using-superpowers/references/antigravity-tools.md",
    "systematic-debugging/CREATION-LOG.md",
    "writing-skills/examples/CLAUDE_MD_TESTING.md",
]

def test_other_harness_files_removed():
    leftover = [p for p in REMOVED if (SKILLS / p).exists()]
    assert not leftover, leftover

def test_no_dangling_references_to_removed_files():
    names = ["codex-tools.md", "pi-tools.md", "antigravity-tools.md", "CREATION-LOG.md", "CLAUDE_MD_TESTING", "testing-skills-with-subagents"]
    hits = []
    for md in SKILLS.rglob("*.md"):
        text = md.read_text(encoding="utf-8")
        for n in names:
            if n in text:
                hits.append(f"{md}: {n}")
    assert not hits, "\n".join(hits)
