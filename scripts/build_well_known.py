#!/usr/bin/env python3
"""Build and validate well-known skill artifacts for public distribution."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


REPO_ROOT = Path(__file__).resolve().parents[1]
WELL_KNOWN_DIR = REPO_ROOT / ".well-known"


@dataclass(frozen=True)
class SkillPackage:
    name: str
    description: str
    source_skill_md: str
    extra_files: List[str]
    replacements: Dict[str, str] | None = None


PACKAGES: List[SkillPackage] = [
    SkillPackage(
        name="designkit-skills",
        description=(
            "美图设计室 DesignKit 能力集合根入口。路由到 edit/ecommerce/product/"
            "tryon/video/marketing 子能力，并统一使用 DESIGNKIT_OPENCLAW_AK。"
        ),
        source_skill_md="SKILL.md",
        extra_files=[
            "api/commands.json",
            "claw.json",
            "scripts/ecommerce_product_kit.py",
            "scripts/run_command.sh",
            "scripts/run_ecommerce_kit.sh",
            "skills/designkit-ecommerce-product-kit/SKILL.md",
            "skills/designkit-edit-tools/SKILL.md",
            "skills/designkit-marketing-kit/SKILL.md",
            "skills/designkit-product-kit/SKILL.md",
            "skills/designkit-tryon-kit/SKILL.md",
            "skills/designkit-video-kit/SKILL.md",
        ],
    ),
    SkillPackage(
        name="designkit-edit-tools",
        description=(
            "通用图片编辑：智能抠图（sod）与 AI 变清晰（image_restoration），"
            "其余编辑能力保留为预留态。"
        ),
        source_skill_md="skills/designkit-edit-tools/SKILL.md",
        extra_files=[
            "api/commands.json",
            "scripts/run_command.sh",
        ],
        replacements={
            "__SKILL_DIR__/../../api/commands.json": "__SKILL_DIR__/api/commands.json",
            "__SKILL_DIR__/../../scripts/run_command.sh": "__SKILL_DIR__/scripts/run_command.sh",
        },
    ),
    SkillPackage(
        name="designkit-ecommerce-product-kit",
        description=(
            "电商商品套图多步工作流：先收集卖点，再收集上架配置，随后进行风格"
            "与成图任务调用。"
        ),
        source_skill_md="skills/designkit-ecommerce-product-kit/SKILL.md",
        extra_files=[
            "scripts/ecommerce_product_kit.py",
            "scripts/run_ecommerce_kit.sh",
        ],
    ),
    SkillPackage(
        name="designkit-product-kit",
        description="电商商品图生产能力规划（白底图、三视图、换背景、A+、SKU 等）。",
        source_skill_md="skills/designkit-product-kit/SKILL.md",
        extra_files=[],
    ),
    SkillPackage(
        name="designkit-tryon-kit",
        description="穿搭/换模特/换场景等试衣与模特展示能力规划。",
        source_skill_md="skills/designkit-tryon-kit/SKILL.md",
        extra_files=[],
    ),
    SkillPackage(
        name="designkit-video-kit",
        description="商品与营销视频能力规划（特写、360、广告、视频复刻）。",
        source_skill_md="skills/designkit-video-kit/SKILL.md",
        extra_files=[],
    ),
    SkillPackage(
        name="designkit-marketing-kit",
        description="营销内容能力规划（海报、小红书套图、改图中文字）。",
        source_skill_md="skills/designkit-marketing-kit/SKILL.md",
        extra_files=[],
    ),
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def collect_tree_hashes(root: Path) -> Dict[str, str]:
    if not root.exists():
        return {}
    hashes: Dict[str, str] = {}
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        hashes[rel] = sha256_bytes(path.read_bytes())
    return hashes


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def copy_file(src_rel: str, dst_root: Path) -> None:
    src = REPO_ROOT / src_rel
    if not src.exists():
        raise FileNotFoundError(f"missing source file: {src_rel}")
    dst = dst_root / src_rel
    ensure_parent(dst)
    shutil.copy2(src, dst)


def write_skill(package: SkillPackage, skill_root: Path) -> List[str]:
    source_path = REPO_ROOT / package.source_skill_md
    content = source_path.read_text(encoding="utf-8")
    if package.replacements:
        for old, new in package.replacements.items():
            content = content.replace(old, new)

    files = ["SKILL.md"]
    skill_md_out = skill_root / "SKILL.md"
    ensure_parent(skill_md_out)
    skill_md_out.write_text(content, encoding="utf-8")

    for rel in package.extra_files:
        copy_file(rel, skill_root)
        files.append(rel)

    return files


def build_channel(channel_dir: Path) -> None:
    for package in PACKAGES:
        target = channel_dir / package.name
        target.mkdir(parents=True, exist_ok=True)
        files = write_skill(package, target)
        # Re-write per-skill manifest for discoverability/debugging.
        manifest = {
            "name": package.name,
            "description": package.description,
            "files": sorted(files),
        }
        (target / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    index = {
        "skills": [
            {
                "name": package.name,
                "description": package.description,
                "files": sorted(["SKILL.md", *package.extra_files]),
            }
            for package in PACKAGES
        ]
    }
    (channel_dir / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def render_well_known(target_root: Path) -> None:
    skills_dir = target_root / "skills"
    agent_skills_dir = target_root / "agent-skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    agent_skills_dir.mkdir(parents=True, exist_ok=True)
    build_channel(skills_dir)

    # Mirror `.well-known/skills` to `.well-known/agent-skills` for CLI compatibility.
    for item in skills_dir.iterdir():
        src = item
        dst = agent_skills_dir / item.name
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)


def run_check(rendered_root: Path) -> int:
    expected = collect_tree_hashes(rendered_root)
    actual = collect_tree_hashes(WELL_KNOWN_DIR)
    if expected == actual:
        print("well-known artifacts are up to date")
        return 0

    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    changed = sorted(
        rel for rel in set(expected) & set(actual) if expected[rel] != actual[rel]
    )
    if missing:
        print("missing files:")
        for rel in missing:
            print(f"  + {rel}")
    if extra:
        print("unexpected files:")
        for rel in extra:
            print(f"  - {rel}")
    if changed:
        print("changed files:")
        for rel in changed:
            print(f"  * {rel}")
    print("run: python3 scripts/build_well_known.py")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build or validate .well-known skill distribution artifacts."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate .well-known matches generated output without writing",
    )
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="well-known-build-") as tmp:
        tmp_root = Path(tmp) / ".well-known"
        render_well_known(tmp_root)

        if args.check:
            return run_check(tmp_root)

        if WELL_KNOWN_DIR.exists():
            shutil.rmtree(WELL_KNOWN_DIR)
        shutil.copytree(tmp_root, WELL_KNOWN_DIR)
        print(f"wrote {WELL_KNOWN_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
