"""Copy upstream superpowers skills and apply the Hermes tool-name mapping.

Usage:
    python3 tools_dev/sync_upstream.py \
        --source <path-to-obra-superpowers-checkout>/skills \
        --dest skills
"""
import argparse
import re
import shutil
from pathlib import Path

REPLACEMENTS = [
    # --- multi-word / longer patterns first, so shorter ones don't clobber them ---
    (r"\bthe Task tool\b", "delegate_task"),
    (r"\bTask tool\b", "delegate_task"),
    (r"Subagent \(general-purpose\):", "delegate_task dispatch:"),
    (r"\bAskUserQuestion tool\b", "clarify"),
    (r"\bAskUserQuestion\b", "clarify"),
    (r"\bSkill tool\b", "skill_view"),
    (r"\bTodoWrite tool\b", "a markdown checklist"),
    (r"\bTodoWrite\b", "a markdown checklist"),
    (r"\bsubagent_type\b", "toolsets"),
    # Bash tool-name context (avoid touching "bash" as a generic shell/language word)
    (r"\bthe Bash tool\b", "the terminal toolset"),
    (r"\bBash tool\b", "terminal toolset"),
]

HEADER_NOTE = (
    "\n> **Hermes port note:** tool names in this document are mapped for "
    "Hermes Agent (see references/tool-mapping.md in the plugin root): "
    "subagents = `delegate_task`, user questions = `clarify`, skill loads = "
    "`skill_view(\"superpowers:<name>\")`.\n"
)


def transform(text: str) -> str:
    for pat, repl in REPLACEMENTS:
        text = re.sub(pat, repl, text)
    return text


def sync(source: Path, dest: Path) -> list[str]:
    dest.mkdir(parents=True, exist_ok=True)
    synced = []
    for skill_dir in sorted(p for p in source.iterdir() if p.is_dir()):
        target = dest / skill_dir.name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(skill_dir, target)
        for md in target.rglob("*.md"):
            text = transform(md.read_text(encoding="utf-8"))
            if md.name == "SKILL.md" and "Hermes port note" not in text:
                # frontmatter(--- ... ---) 직후에 노트 삽입
                m = re.match(r"(?s)^(---.*?---\n)", text)
                text = (m.group(1) + HEADER_NOTE + text[m.end():]) if m else HEADER_NOTE + text
            md.write_text(text, encoding="utf-8")
        synced.append(skill_dir.name)
    return synced


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, type=Path)
    ap.add_argument("--dest", default=Path("skills"), type=Path)
    args = ap.parse_args()
    names = sync(args.source.expanduser(), args.dest)
    print(f"synced {len(names)} skills: {', '.join(names)}")
