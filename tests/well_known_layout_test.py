#!/usr/bin/env python3
"""Validate .well-known layout for skills URL installation."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WELL_KNOWN = ROOT / ".well-known"
CHANNELS = ["skills", "agent-skills"]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid json {path}: {exc}")
    return {}


def assert_safe_file_path(value: str) -> None:
    if value.startswith("/") or value.startswith("\\"):
        fail(f"absolute path is not allowed in index files: {value}")
    if ".." in value.split("/"):
        fail(f"path traversal is not allowed in index files: {value}")


def validate_skill_frontmatter(skill_md: Path, expected_name: str) -> None:
    text = skill_md.read_text(encoding="utf-8")
    # The frontmatter name must stay aligned with index name.
    match = re.search(r"^name:\s*([a-z0-9-]+)\s*$", text, flags=re.MULTILINE)
    if not match:
        fail(f"missing frontmatter name in {skill_md}")
    if match.group(1) != expected_name:
        fail(
            f"frontmatter name mismatch in {skill_md}: "
            f"expected={expected_name}, actual={match.group(1)}"
        )


def validate_channel(channel: str) -> dict:
    base = WELL_KNOWN / channel
    index_path = base / "index.json"
    index = load_json(index_path)
    skills = index.get("skills")
    if not isinstance(skills, list) or not skills:
        fail(f"{index_path} must contain non-empty skills list")

    seen = set()
    for entry in skills:
        if not isinstance(entry, dict):
            fail(f"invalid entry in {index_path}: {entry!r}")
        name = entry.get("name")
        description = entry.get("description")
        files = entry.get("files")

        if not isinstance(name, str) or not name:
            fail(f"invalid skill name in {index_path}: {entry!r}")
        if name in seen:
            fail(f"duplicate skill name in {index_path}: {name}")
        seen.add(name)

        if not re.match(r"^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$", name):
            fail(f"invalid skill name format: {name}")
        if not isinstance(description, str) or not description.strip():
            fail(f"empty description for skill {name}")
        if not isinstance(files, list) or not files:
            fail(f"files list missing for skill {name}")
        if "SKILL.md" not in files:
            fail(f"SKILL.md must be present in files list for skill {name}")

        skill_dir = base / name
        if not skill_dir.exists():
            fail(f"missing skill directory: {skill_dir}")

        for rel in files:
            if not isinstance(rel, str):
                fail(f"non-string file path in skill {name}: {rel!r}")
            assert_safe_file_path(rel)
            file_path = skill_dir / rel
            if not file_path.exists():
                fail(f"missing declared file for skill {name}: {file_path}")

        validate_skill_frontmatter(skill_dir / "SKILL.md", name)

    return index


def main() -> int:
    indexes = {}
    for channel in CHANNELS:
        indexes[channel] = validate_channel(channel)

    if indexes["skills"] != indexes["agent-skills"]:
        fail("index.json content mismatch between skills and agent-skills")

    print("PASS: .well-known layout is valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
