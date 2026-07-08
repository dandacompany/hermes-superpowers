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
    # --- narrowly-scoped rewords tied to STRIP_PATHS removals below; each
    # pattern is specific enough to only ever match the one sentence/block
    # it targets (see tools_dev/MANUAL_FIXUPS.md for the rationale) ---
    (
        r"If your harness appears here, read its reference file for special instructions:\n\n"
        r"- Codex: `references/codex-tools\.md`\n"
        r"- Pi: `references/pi-tools\.md`\n"
        r"- Antigravity: `references/antigravity-tools\.md`\n\n",
        "",
    ),
    (
        r"User instructions \(CLAUDE\.md, AGENTS\.md, GEMINI\.md, etc, direct requests\) "
        r"take precedence over skills, which in turn override default behavior\.",
        "User instructions (host instruction files such as SOUL.md, and direct requests) "
        "take precedence over skills, which in turn override default behavior.",
    ),
]

# Other-harness / dev-log files that are dead weight in a Hermes-only port.
# Removed after copytree in sync() below. Paths are relative to `dest`
# (i.e. relative to the `skills/` root), matching the layout described in
# tools_dev/MANUAL_FIXUPS.md.
STRIP_PATHS = [
    "using-superpowers/references/codex-tools.md",
    "using-superpowers/references/pi-tools.md",
    "using-superpowers/references/antigravity-tools.md",
    "systematic-debugging/CREATION-LOG.md",
    "writing-skills/examples/CLAUDE_MD_TESTING.md",
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

    # Strip other-harness / dev-log leftovers, then prune any directory
    # (e.g. references/, examples/) that is now empty as a result.
    for rel in STRIP_PATHS:
        stripped = dest / rel
        if stripped.exists():
            stripped.unlink()
            parent = stripped.parent
            if parent != dest and not any(parent.iterdir()):
                parent.rmdir()

    return synced


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, type=Path)
    ap.add_argument("--dest", default=Path("skills"), type=Path)
    args = ap.parse_args()
    names = sync(args.source.expanduser(), args.dest)
    print(f"synced {len(names)} skills: {', '.join(names)}")
