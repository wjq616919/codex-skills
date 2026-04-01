#!/usr/bin/env python3
"""Audit and lightly repair transition flow between adjacent storyboard shots."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Dict, List, Tuple


SIZE_ORDER = ["大全景", "全景", "中景", "双人中景", "中近景", "近景", "特写", "插入特写"]
LOCATION_HINTS = ["室", "馆", "楼下", "走廊", "会议室", "咖啡馆", "医院", "出租屋", "工作室", "小区", "门口"]
STATE_KEYWORDS = {
    "打开": "open",
    "开了一条缝": "ajar",
    "关上": "closed",
    "亮起": "lit",
    "扣住": "face_down",
    "撕下来": "torn_off",
    "压在": "pressed_on",
    "发动": "running",
    "停住": "paused",
}
MOTION_KEYWORDS = ["翻", "抬头", "转头", "走", "跑", "推", "拉", "递", "拿起", "放下", "撕", "开", "关", "踹", "捡起", "推门"]
LOOK_KEYWORDS = ["看", "望", "盯", "瞥", "映出", "屏幕上", "照片上"]


def size_rank(label: str) -> int:
    if label in SIZE_ORDER:
        return SIZE_ORDER.index(label)
    return SIZE_ORDER.index("中景")


def letter_code(index: int) -> str:
    index += 1
    letters = []
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters.append(chr(65 + remainder))
    return "".join(reversed(letters))


def renumber_shots(shots: List[Dict[str, object]], scene_index: int) -> List[Dict[str, object]]:
    for index, shot in enumerate(shots):
        shot["shot_id"] = f"{scene_index:02d}{letter_code(index)}"
    return shots


def state_snapshot_conflict(prev_shot: Dict[str, object], next_shot: Dict[str, object]) -> bool:
    prev_states = prev_shot.get("state_snapshot", {}).get("prop_states", {})
    next_states = next_shot.get("state_snapshot", {}).get("prop_states", {})
    next_action = str(next_shot.get("action", ""))
    if not prev_states or not next_states:
        return False
    for prop, prev_state in prev_states.items():
        next_state = next_states.get(prop)
        if next_state and next_state != prev_state and not any(keyword in next_action for keyword in STATE_KEYWORDS):
            return True
    return False


def shared_anchors(prev_shot: Dict[str, object], next_shot: Dict[str, object]) -> List[str]:
    prev_anchors = [str(item) for item in prev_shot.get("continuity_anchors", [])]
    next_anchors = [str(item) for item in next_shot.get("continuity_anchors", [])]
    return [anchor for anchor in prev_anchors if anchor in next_anchors]


def is_location_like(anchor: str) -> bool:
    return any(hint in anchor for hint in LOCATION_HINTS)


def first_non_character_anchor(shared: List[str], prev_shot: Dict[str, object], next_shot: Dict[str, object]) -> str:
    prev_chars = set(prev_shot.get("state_snapshot", {}).get("characters", []))
    next_chars = set(next_shot.get("state_snapshot", {}).get("characters", []))
    for anchor in shared:
        if anchor not in prev_chars and anchor not in next_chars:
            if is_location_like(anchor):
                continue
            return anchor
    return shared[0] if shared else ""


def inspect_pair(
    prev_shot: Dict[str, object],
    next_shot: Dict[str, object],
    setup_seen: int,
) -> Tuple[List[str], List[str]]:
    issues: List[str] = []
    notes: List[str] = []
    shared = shared_anchors(prev_shot, next_shot)
    prev_action = str(prev_shot.get("action", ""))
    next_action = str(next_shot.get("action", ""))

    if not shared and next_shot.get("info_control") not in {"reveal"} and prev_shot.get("shot_role") != "connector":
        issues.append("event_link_weak")
        notes.append("前后镜头缺少共同锚点，事件连接偏弱。")

    prev_axis = prev_shot.get("axis_side")
    next_axis = next_shot.get("axis_side")
    if prev_axis and next_axis and prev_axis != next_axis:
        if "特写" not in str(prev_shot.get("shot_size")) and "特写" not in str(next_shot.get("shot_size")):
            issues.append("axis_shift")
            notes.append("轴向突然变化，可能影响左右关系。")

    if prev_shot.get("viewpoint") == "subjective" and next_shot.get("info_control") not in {"reaction", "reveal", "bridge"}:
        issues.append("gaze_unresolved")
        notes.append("主观视角之后没有给到被看对象或反应。")

    meaningful_shared = [anchor for anchor in shared if not is_location_like(anchor)]
    if abs(size_rank(str(prev_shot.get("shot_size", "中景"))) - size_rank(str(next_shot.get("shot_size", "中景")))) > 2:
        motivated_push = (
            next_shot.get("info_control") in {"reveal", "reaction"}
            or any(keyword in prev_action for keyword in MOTION_KEYWORDS + LOOK_KEYWORDS)
            or bool(meaningful_shared)
        )
        if next_shot.get("shot_role") != "connector" and prev_shot.get("info_control") != "setup" and not motivated_push:
            issues.append("size_jump_unmotivated")
            notes.append("景别跳变过大，但缺少明确动机。")

    if any(keyword in prev_action for keyword in MOTION_KEYWORDS) and not shared and next_shot.get("shot_role") != "connector":
        issues.append("action_handoff")
        notes.append("上个镜头抛出动作，但下个镜头没有顺势接住。")

    if next_shot.get("info_control") == "reveal" and setup_seen == 0 and prev_shot.get("info_control") != "setup":
        issues.append("reveal_without_setup")
        notes.append("关键信息揭示前缺少建立期待的镜头。")

    if state_snapshot_conflict(prev_shot, next_shot):
        issues.append("prop_state_break")
        notes.append("关键物件状态前后不连续。")

    return issues, notes


def audit_scene_shots(scene: Dict[str, object]) -> Dict[str, object]:
    shots = scene.get("shots", [])
    pairs: List[Dict[str, object]] = []
    residual_risks: List[str] = []
    setup_seen = 0

    for index in range(len(shots) - 1):
        prev_shot = shots[index]
        next_shot = shots[index + 1]
        issues, notes = inspect_pair(prev_shot, next_shot, setup_seen)
        pair = {
            "pair_index": index,
            "from_shot": prev_shot.get("shot_id", f"shot-{index}"),
            "to_shot": next_shot.get("shot_id", f"shot-{index + 1}"),
            "passed": not issues,
            "fail_reasons": issues,
            "notes": notes,
        }
        pairs.append(pair)
        if issues:
            residual_risks.append(f"{pair['from_shot']} -> {pair['to_shot']}: {', '.join(issues)}")
        if prev_shot.get("info_control") == "setup":
            setup_seen += 1

    for index in range(len(shots) - 2):
        left = shots[index]
        middle = shots[index + 1]
        right = shots[index + 2]
        same_size = left.get("shot_size") == middle.get("shot_size") == right.get("shot_size")
        left_duration = float(left.get("duration_seconds", 0))
        middle_duration = float(middle.get("duration_seconds", 0))
        right_duration = float(right.get("duration_seconds", 0))
        close_durations = max(left_duration, middle_duration, right_duration) - min(left_duration, middle_duration, right_duration) < 1.0
        if same_size and close_durations:
            pairs[index + 1]["passed"] = False
            if "rhythm_flat" not in pairs[index + 1]["fail_reasons"]:
                pairs[index + 1]["fail_reasons"].append("rhythm_flat")
                pairs[index + 1]["notes"].append("连续三个相近景别和时长，节奏发平。")
            residual_risks.append(
                f"{middle.get('shot_id', index + 1)} 附近节奏偏平，建议打破同景别连续重复。"
            )

    return {
        "scene_id": scene.get("scene_id", ""),
        "pair_count": len(pairs),
        "issue_count": sum(1 for pair in pairs if not pair["passed"]),
        "pairs": pairs,
        "residual_risks": residual_risks,
    }


def soften_shot_size(prev_size: str, next_size: str) -> str:
    prev_rank = size_rank(prev_size)
    next_rank = size_rank(next_size)
    if abs(prev_rank - next_rank) <= 2:
        return next_size
    if next_rank > prev_rank:
        target_rank = min(prev_rank + 2, len(SIZE_ORDER) - 1)
    else:
        target_rank = max(prev_rank - 2, 0)
    return SIZE_ORDER[target_rank]


def make_connector(
    prev_shot: Dict[str, object],
    next_shot: Dict[str, object],
    scene_objective: str,
) -> Dict[str, object]:
    shared = shared_anchors(prev_shot, next_shot)
    focus = first_non_character_anchor(shared, prev_shot, next_shot)
    if not focus:
        focus = "人物动作关系"
    shot_size = "插入特写" if focus and focus not in prev_shot.get("state_snapshot", {}).get("characters", []) else "中近景"
    return {
        "shot_id": "",
        "shot_role": "connector",
        "shot_size": shot_size,
        "duration_seconds": 1.8,
        "camera_setup": "固定机位，补一个顺接镜，把动作和信息平顺送到下一镜。",
        "camera_motion": "固定",
        "viewpoint": "objective",
        "axis_side": prev_shot.get("axis_side") or next_shot.get("axis_side") or "A",
        "frame_description": f"补足{focus}与人物动作之间的连接关系。",
        "action": f"先接住前一镜的余势，再把注意力送往下一镜的重点。",
        "transition_note": "",
        "emotion": next_shot.get("emotion") or prev_shot.get("emotion") or "克制",
        "scene_objective": scene_objective,
        "audience_focus": next_shot.get("audience_focus") or prev_shot.get("audience_focus"),
        "narrative_purpose": "用最少的信息补齐主镜之间的顺接。",
        "info_control": "bridge",
        "continuity_anchors": list(dict.fromkeys(shared or (prev_shot.get("continuity_anchors", []) + next_shot.get("continuity_anchors", [])))),
        "state_snapshot": {
            "characters": list(dict.fromkeys(prev_shot.get("state_snapshot", {}).get("characters", []) + next_shot.get("state_snapshot", {}).get("characters", []))),
            "props": list(dict.fromkeys(prev_shot.get("state_snapshot", {}).get("props", []) + next_shot.get("state_snapshot", {}).get("props", []))),
            "prop_states": {},
        },
        "beat_refs": list(dict.fromkeys(prev_shot.get("beat_refs", []) + next_shot.get("beat_refs", []))),
        "inserted_by_audit": True,
    }


def repair_scene_shots(scene: Dict[str, object]) -> Dict[str, object]:
    fixed_scene = copy.deepcopy(scene)
    shots = renumber_shots(fixed_scene.get("shots", []), int(fixed_scene.get("scene_number", 1)))
    fixed_scene["shots"] = shots

    for _ in range(3):
        report = audit_scene_shots(fixed_scene)
        changed = False

        for pair in report["pairs"]:
            if pair["passed"]:
                continue
            index = int(pair["pair_index"])
            if index >= len(fixed_scene["shots"]) - 1:
                continue
            prev_shot = fixed_scene["shots"][index]
            next_shot = fixed_scene["shots"][index + 1]
            reasons = set(pair["fail_reasons"])

            if "axis_shift" in reasons:
                next_shot["axis_side"] = prev_shot.get("axis_side") or next_shot.get("axis_side") or "A"
                changed = True

            if "size_jump_unmotivated" in reasons:
                next_shot["shot_size"] = soften_shot_size(str(prev_shot.get("shot_size", "中景")), str(next_shot.get("shot_size", "中景")))
                changed = True

            if "gaze_unresolved" in reasons:
                next_shot["info_control"] = "reaction"
                changed = True

            if "rhythm_flat" in reasons and next_shot.get("shot_role") == "connector":
                next_shot["shot_size"] = "插入特写" if next_shot.get("shot_size") != "插入特写" else "中近景"
                next_shot["duration_seconds"] = max(1.2, float(next_shot.get("duration_seconds", 1.8)) - 0.6)
                changed = True

            if "reveal_without_setup" in reasons:
                if prev_shot.get("shot_size") in {"全景", "大全景"} or prev_shot.get("shot_role") == "connector":
                    prev_shot["info_control"] = "setup"
                    changed = True
                elif next_shot.get("shot_role") == "main":
                    next_shot["info_control"] = "advance"
                    changed = True

            hard_link_break = {"action_handoff", "prop_state_break"} & reasons
            if hard_link_break:
                connector = make_connector(prev_shot, next_shot, str(fixed_scene.get("scene_objective", "")))
                fixed_scene["shots"].insert(index + 1, connector)
                changed = True
                break

        fixed_scene["shots"] = renumber_shots(fixed_scene["shots"], int(fixed_scene.get("scene_number", 1)))
        if not changed:
            break

    final_report = audit_scene_shots(fixed_scene)
    fixed_scene["transition_audit"] = final_report["pairs"]
    fixed_scene["continuity_risks"] = final_report["residual_risks"]
    return fixed_scene


def audit_plan(plan: Dict[str, object], repair: bool = False) -> Tuple[Dict[str, object], Dict[str, object]]:
    scenes_out: List[Dict[str, object]] = []
    reports: List[Dict[str, object]] = []

    for scene in plan.get("scenes", []):
        scene_result = repair_scene_shots(scene) if repair else scene
        report = audit_scene_shots(scene_result)
        reports.append(report)
        scenes_out.append(scene_result)

    report_payload = {
        "scene_count": len(reports),
        "issue_count": sum(item["issue_count"] for item in reports),
        "scenes": reports,
    }
    revised_plan = copy.deepcopy(plan)
    revised_plan["scenes"] = scenes_out
    return revised_plan, report_payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit or repair shot transitions.")
    parser.add_argument("--input", required=True, help="Input shot plan JSON")
    parser.add_argument("--output", help="Output audit JSON path")
    parser.add_argument("--rewrite-output", help="Optional revised shot plan JSON path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = json.loads(Path(args.input).read_text())
    revised_plan, report = audit_plan(plan, repair=bool(args.rewrite_output))

    audit_text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(audit_text + "\n")
    else:
        print(audit_text)

    if args.rewrite_output:
        Path(args.rewrite_output).write_text(json.dumps(revised_plan, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
