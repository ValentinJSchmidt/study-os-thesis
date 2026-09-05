"""Deterministic checks for the `npx skills add` install surface.

The Vercel skills CLI (https://github.com/vercel-labs/skills) is the one-command
route for local agents. It discovers skills in `skills/` *and* in agent
directories such as `.claude/skills/` and `.codex/skills/`, where this repo keeps
its maintainer-only simulation skills. Those must stay hidden behind
`metadata.internal: true`, or students get them listed in the picker and
installed by `--skill '*'`.
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCANNED_DIRS = (
    REPO_ROOT / "skills",
    REPO_ROOT / ".claude" / "skills",
    REPO_ROOT / ".codex" / "skills",
)
PUBLIC_SKILLS = {
    "build-student-profile",
    "design-agent-skill",
    "discover-company-candidates",
    "discover-university-candidates",
    "draft-thesis-contact",
    "find-company-thesis-options",
    "find-recent-papers",
    "find-university-chairs",
    "generate-thesis-directions",
    "thesis-finder",
}
INTERNAL_SKILLS = {
    "create-thesis-sim-student",
    "run-thesis-simulations",
}
INTERNAL_MARKER = re.compile(r"^metadata:\n(?:[ \t]+.*\n)*?[ \t]+internal:[ \t]*true[ \t]*$", flags=re.MULTILINE)


def _frontmatter(skill_md: Path) -> str:
    match = re.match(r"^---\n(?P<body>.*?)\n---\n", skill_md.read_text(encoding="utf-8"), flags=re.DOTALL)
    assert match, f"{skill_md} is missing YAML frontmatter"
    return match.group("body") + "\n"


def _discovered_skills() -> dict[str, list[Path]]:
    found: dict[str, list[Path]] = {}
    for scanned_dir in SCANNED_DIRS:
        assert scanned_dir.is_dir(), f"{scanned_dir} is missing"
        for path in sorted(scanned_dir.iterdir()):
            skill_md = path / "SKILL.md"
            if path.is_dir() and skill_md.is_file():
                found.setdefault(path.name, []).append(skill_md)
    return found


def test_installer_offers_exactly_the_public_skills() -> None:
    offered = {name for name, skill_mds in _discovered_skills().items() if any(not INTERNAL_MARKER.search(_frontmatter(skill_md)) for skill_md in skill_mds)}

    assert offered == PUBLIC_SKILLS


def test_maintainer_skills_are_marked_internal() -> None:
    discovered = _discovered_skills()
    assert INTERNAL_SKILLS <= set(discovered)

    for name in INTERNAL_SKILLS:
        for skill_md in discovered[name]:
            assert INTERNAL_MARKER.search(_frontmatter(skill_md)), f"{skill_md} is missing metadata.internal: true"
