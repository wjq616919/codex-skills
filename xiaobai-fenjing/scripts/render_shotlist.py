#!/usr/bin/env python3
"""Render the final Chinese shot list from a structured plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render final Chinese shot list from plan JSON.")
    parser.add_argument("--input", required=True, help="Shot plan JSON")
    parser.add_argument("--output", help="Output markdown path")
    parser.add_argument("--no-title", action="store_true", help="Suppress title heading")
    parser.add_argument("--no-scene-headings", action="store_true", help="Suppress scene headings")
    return parser.parse_args()


def format_duration(value: float) -> str:
    rounded = round(float(value), 1)
    if rounded.is_integer():
        return f"{int(rounded)}秒"
    return f"{rounded:.1f}秒"


def render_shot(shot: Dict[str, object]) -> str:
    return "\n".join(
        [
            f"{shot['shot_id']} [{shot['shot_size']}｜{format_duration(float(shot.get('duration_seconds', 0)))}]",
            f"机位/运动：{shot.get('camera_setup', '固定机位，保持信息清楚。')}",
            f"画面：{shot.get('frame_description', '')}",
            f"发生：{shot.get('action', '')}",
            f"接点：{shot.get('transition_note', '动作收住，本场结束。')}",
            f"情绪：{shot.get('emotion', '克制')}",
        ]
    )


def scene_heading(scene: Dict[str, object]) -> str:
    heading = str(scene.get("heading", "")).strip()
    if heading:
        return f"场景 {int(scene.get('scene_number', 0)):02d}｜{heading}"
    location = str(scene.get("location", "")).strip()
    if location:
        return f"场景 {int(scene.get('scene_number', 0)):02d}｜{location}"
    return f"场景 {int(scene.get('scene_number', 0)):02d}"


def render_plan(plan: Dict[str, object], include_title: bool, include_scene_headings: bool) -> str:
    sections: List[str] = []
    title = str(plan.get("project", {}).get("title", "")).strip()
    if include_title and title:
        sections.append(f"# {title}")

    for scene in plan.get("scenes", []):
        scene_lines: List[str] = []
        if include_scene_headings:
            scene_lines.append(f"## {scene_heading(scene)}")
            scene_lines.append("")
        for shot in scene.get("shots", []):
            scene_lines.append(render_shot(shot))
            scene_lines.append("")
        sections.append("\n".join(scene_lines).rstrip())

    return "\n\n".join(section for section in sections if section).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    plan = json.loads(Path(args.input).read_text())
    rendered = render_plan(
        plan,
        include_title=not args.no_title,
        include_scene_headings=not args.no_scene_headings,
    )
    if args.output:
        Path(args.output).write_text(rendered)
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
