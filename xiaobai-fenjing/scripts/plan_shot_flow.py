#!/usr/bin/env python3
"""Plan shot flow for the xiaobai-fenjing skill."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from audit_transitions import repair_scene_shots  # noqa: E402


REVEAL_VERBS = ["发现", "看见", "看到", "打开", "露出", "原来", "亮起", "映出", "翻到", "捡起来一看"]
REVEAL_OBJECTS = ["照片", "广告", "合同", "短信", "屏幕", "文件夹", "协议"]
SETUP_KEYWORDS = ["停住", "听见", "看向", "望向", "门外", "声音", "没人先开口", "怀疑", "半小时后到"]
DECISIVE_ACTION_KEYWORDS = ["签", "撕", "压在", "推回去", "推向", "拿起", "放下", "扣住", "推门", "踹", "发动", "走过去"]
RELATION_KEYWORDS = ["对视", "隔桌", "看了", "递给", "推向", "拦你", "先看了", "不再拦你"]
REACTION_KEYWORDS = ["没有回应", "愣", "沉默", "深吸", "停在", "停住", "不说话", "没有看", "只把"]
LOOK_KEYWORDS = ["看", "望", "盯", "瞥", "映出", "屏幕上", "照片上"]
PROP_HINTS = [
    "木箱",
    "杂志",
    "广告",
    "工作台",
    "门",
    "门把",
    "门锁",
    "照片",
    "手机",
    "屏幕",
    "文件夹",
    "协议",
    "投影",
    "油箱",
    "摩托车",
    "缴费单",
    "苹果",
    "高窗",
    "桌子",
    "玻璃",
    "笔",
]
EMOTION_RULES = [
    ("紧张", ["催", "半小时后", "快迟到了", "门锁", "夜", "没人先开口"]),
    ("压抑", ["沉默", "没有回应", "没有看", "扣住", "停住"]),
    ("迟疑", ["犹豫", "停在", "停住", "想", "没有去接"]),
    ("惊疑", ["发现", "看见", "原来", "照片", "短信"]),
    ("决绝", ["撕", "签", "压在", "猛地", "终于"]),
    ("松动", ["深吸", "推门进去", "发动"]),
]
STATE_PATTERNS = {
    "亮起": "lit",
    "扣住": "face_down",
    "撕下来": "torn_off",
    "压在": "pressed_on",
    "开了一条缝": "ajar",
    "发动": "running",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan shot flow from normalized scene JSON.")
    parser.add_argument("--input", required=True, help="Normalized JSON path")
    parser.add_argument("--output", help="Output shot plan JSON")
    parser.add_argument("--constraints", help="Optional constraints JSON path")
    return parser.parse_args()


def load_constraints(path: str | None) -> Dict[str, object]:
    defaults: Dict[str, object] = {
        "language": "zh",
        "medium": "通用影视分镜",
        "rhythm_mode": "适度重构节奏",
        "output_mode": "final_shotlist_only",
    }
    if not path:
        return defaults

    raw = Path(path).read_text().strip()
    if not raw:
        return defaults

    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError:
        loaded = {}
        for line in raw.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            loaded[key.strip()] = value.strip()

    defaults.update(loaded)
    return defaults


def extract_props(text: str) -> List[str]:
    found = []
    for prop in PROP_HINTS:
        if prop in text and prop not in found:
            found.append(prop)
    return found


def infer_emotion(text: str) -> str:
    for label, keywords in EMOTION_RULES:
        if any(keyword in text for keyword in keywords):
            return label
    if any(keyword in text for keyword in LOOK_KEYWORDS):
        return "专注"
    return "克制"


def beat_tags(beat: Dict[str, object], must_keep: List[str]) -> Tuple[float, List[str]]:
    text = str(beat.get("text", ""))
    score = 1.0
    tags: List[str] = []

    if beat.get("type") == "dialogue":
        score += 1.0
        tags.append("dialogue")

    reveal_object_hit = any(keyword in text for keyword in REVEAL_OBJECTS)
    reveal_verb_hit = any(keyword in text for keyword in REVEAL_VERBS)
    if reveal_verb_hit or (reveal_object_hit and any(keyword in text for keyword in ["翻到", "看见", "看到", "屏幕上", "照片上", "捡起来一看"])):
        score += 2.0
        tags.append("reveal")

    if any(keyword in text for keyword in SETUP_KEYWORDS):
        score += 1.0
        tags.append("setup")

    if any(keyword in text for keyword in DECISIVE_ACTION_KEYWORDS):
        score += 2.0
        tags.append("decisive_action")

    if any(keyword in text for keyword in RELATION_KEYWORDS):
        score += 1.5
        tags.append("relation_change")

    if any(keyword in text for keyword in REACTION_KEYWORDS):
        score += 1.5
        tags.append("reaction")

    emotion = infer_emotion(text)
    if emotion not in {"克制", ""}:
        score += 1.0
        tags.append("emotion")

    if any(phrase in text for phrase in must_keep):
        score += 2.5
        tags.append("must_keep")

    return score, list(dict.fromkeys(tags))


def primary_character(scene: Dict[str, object]) -> str:
    characters = scene.get("present_characters", [])
    if characters:
        return str(characters[0])
    for beat in scene.get("beats", []):
        beat_characters = beat.get("characters", [])
        if beat_characters:
            return str(beat_characters[0])
    return "人物"


def scene_objective(scene: Dict[str, object], analyses: List[Dict[str, object]]) -> str:
    subject = primary_character(scene)
    all_tags = {tag for item in analyses for tag in item["tags"]}
    if "reveal" in all_tags and "decisive_action" in all_tags:
        return f"让观众看懂{subject}被关键信息触发后，如何把变化落到动作上。"
    if "relation_change" in all_tags:
        return f"让观众看懂{subject}与对手之间的关系在这一场里发生了变化。"
    if "emotion" in all_tags or "reaction" in all_tags:
        return f"让观众读懂{subject}内心变化如何通过动作和停顿暴露出来。"
    return f"让观众清楚看到{subject}这一场的行动推进和状态变化。"


def audience_focus(scene: Dict[str, object], analyses: List[Dict[str, object]]) -> str:
    subject = primary_character(scene)
    for item in sorted(analyses, key=lambda item: item["score"], reverse=True):
        props = item["props"]
        if props:
            return f"先跟住{subject}，再把注意力压到{props[0]}上的关键信息。"
    return f"先交代{subject}在场景里的位置，再顺着动作把注意力收紧。"


def select_main_indices(analyses: List[Dict[str, object]]) -> List[int]:
    if not analyses:
        return []
    count = len(analyses)
    selected = {0, count - 1}
    for item in analyses:
        if item["score"] >= 4.0 or {"reveal", "decisive_action", "must_keep"} & set(item["tags"]):
            selected.add(item["index"])
    minimum = min(3, count)
    ranked = sorted(analyses, key=lambda item: (-item["score"], item["index"]))
    for item in ranked:
        if len(selected) >= minimum:
            break
        selected.add(item["index"])
    if len(selected) > 6:
        keep = {0, count - 1}
        for item in ranked:
            if len(keep) >= 6:
                break
            keep.add(item["index"])
        selected = keep
    return sorted(selected)


def shared_tokens(left: Dict[str, object], right: Dict[str, object]) -> List[str]:
    anchors = list(dict.fromkeys(left["characters"] + left["props"]))
    return [token for token in anchors if token in right["characters"] or token in right["props"]]


def choose_connector_index(analyses: List[Dict[str, object]], left_index: int, right_index: int) -> int | None:
    candidates = [item for item in analyses if left_index < item["index"] < right_index]
    if not candidates:
        return None
    candidates.sort(
        key=lambda item: (
            0 if shared_tokens(analyses[left_index], item) else 1,
            -item["score"],
            item["index"],
        )
    )
    return candidates[0]["index"]


def connector_indices(analyses: List[Dict[str, object]], mains: List[int]) -> List[int]:
    connectors = set()
    for left, right in zip(mains, mains[1:]):
        gap = right - left
        if gap <= 1:
            continue
        connector = choose_connector_index(analyses, left, right)
        if connector is not None and connector not in mains:
            connectors.add(connector)
    return sorted(connectors)


def shot_size_for(
    analysis: Dict[str, object],
    role: str,
    position: int,
    scene: Dict[str, object],
) -> str:
    tags = set(analysis["tags"])
    props = analysis["props"]
    if position == 0:
        return "全景"
    if role == "connector":
        if props and ("reveal" in tags or "must_keep" in tags):
            return "插入特写"
        if "emotion" in tags or "reaction" in tags:
            return "中近景"
        return "中景"
    if props and "reveal" in tags:
        return "特写"
    if "decisive_action" in tags:
        return "近景"
    if analysis["beat"].get("type") == "dialogue" and len(scene.get("present_characters", [])) >= 2:
        return "双人中景"
    if "emotion" in tags or "reaction" in tags or "setup" in tags:
        return "近景"
    return "中景"


def viewpoint_for(analysis: Dict[str, object]) -> str:
    text = str(analysis["beat"].get("text", ""))
    if any(keyword in text for keyword in ["看见", "看到", "屏幕上", "照片上", "映出"]):
        return "subjective"
    return "objective"


def camera_setup_for(analysis: Dict[str, object], shot_size: str, role: str) -> str:
    tags = set(analysis["tags"])
    if viewpoint_for(analysis) == "subjective":
        return "角色主观视角，顺着视线压过去，让信息直接落到观众眼前。"
    if shot_size in {"全景", "大全景"}:
        return "固定机位，先把空间、人物和关键物件的位置关系立住。"
    if shot_size == "双人中景":
        return "过肩或轴线内固定，守住人物关系和对话方向。"
    if shot_size in {"特写", "插入特写"}:
        return "固定机位，压近到关键物件或细节，让信息直接落地。"
    if role == "connector":
        return "固定机位，补一个顺接动作，把注意力平顺送往下一镜。"
    if "emotion" in tags or "reaction" in tags:
        return "轻微前推，贴住人物状态变化，但不打断表演节奏。"
    return "固定机位，保持动作和视线关系清楚。"


def duration_for(analysis: Dict[str, object], role: str) -> float:
    text_length = len(str(analysis["beat"].get("text", "")))
    if role == "connector":
        return 1.6 if text_length < 18 else 2.2
    if "reveal" in analysis["tags"] or "emotion" in analysis["tags"]:
        return 3.6
    if analysis["beat"].get("type") == "dialogue":
        return 3.2
    return 2.8 if text_length < 18 else 3.2


def narrative_purpose_for(role: str, analysis: Dict[str, object]) -> str:
    tags = set(analysis["tags"])
    if role == "connector":
        return "补足主镜之间缺失的信息，让段落顺着讲下去。"
    if "reveal" in tags:
        return "把关键事实明确揭示给观众。"
    if "decisive_action" in tags:
        return "让决定性动作真正落地，而不是被一句话带过。"
    if "relation_change" in tags:
        return "让人物关系变化被看见。"
    if "emotion" in tags or "reaction" in tags:
        return "让情绪变化有清楚的视觉落点。"
    return "稳住这场戏的主要叙事推进。"


def info_control_for(role: str, analysis: Dict[str, object]) -> str:
    tags = set(analysis["tags"])
    if role == "connector":
        return "bridge"
    if "setup" in tags and "decisive_action" not in tags and "reveal" not in tags:
        return "setup"
    if "reveal" in tags:
        return "reveal"
    if "reaction" in tags or "emotion" in tags:
        return "reaction"
    return "advance"


def state_snapshot(text: str, characters: List[str], props: List[str]) -> Dict[str, object]:
    prop_states: Dict[str, str] = {}
    for keyword, state in STATE_PATTERNS.items():
        if keyword in text:
            for prop in props:
                prop_states[prop] = state
    return {
        "characters": characters,
        "props": props,
        "prop_states": prop_states,
    }


def frame_description(scene: Dict[str, object], analysis: Dict[str, object], shot_size: str) -> str:
    characters = analysis["characters"] or [primary_character(scene)]
    subject = characters[0]
    multi_source = characters[:2]
    if shot_size == "双人中景" and len(multi_source) < 2:
        multi_source = list(dict.fromkeys(list(scene.get("present_characters", []))[:2] + multi_source))
    multi_subject = "、".join(multi_source[:2])
    props = analysis["props"]
    location = scene.get("location") or scene.get("heading") or "场景"
    if shot_size in {"全景", "大全景"}:
        return f"{location}的空间先被交代清楚，{multi_subject}与关键物件的位置关系一眼能看明白。"
    if shot_size == "双人中景":
        return f"{multi_subject}同处画面，保留桌面或门口这类关系线索。"
    if shot_size in {"特写", "插入特写"}:
        focus = props[0] if props else subject
        return f"画面压到{focus}，把关键细节放到观众眼前。"
    anchor = props[0] if props else location
    return f"画面跟住{subject}，同时保留{anchor}作为段落连接线索。"


def build_analysis(scene: Dict[str, object], constraints: Dict[str, object]) -> List[Dict[str, object]]:
    must_keep = list(constraints.get("must_keep", []))
    analyses: List[Dict[str, object]] = []
    beats = scene.get("beats", [])
    for index, beat in enumerate(beats):
        score, tags = beat_tags(beat, must_keep)
        if index in {0, len(beats) - 1}:
            score += 0.8
        props = extract_props(str(beat.get("text", "")))
        analyses.append(
            {
                "index": index,
                "beat": beat,
                "score": round(score, 2),
                "tags": tags,
                "props": props,
                "characters": list(beat.get("characters", [])),
                "emotion": infer_emotion(str(beat.get("text", ""))),
            }
        )
    return analyses


def build_shot(
    scene: Dict[str, object],
    analysis: Dict[str, object],
    role: str,
    position: int,
    scene_goal: str,
    audience_note: str,
) -> Dict[str, object]:
    beat = analysis["beat"]
    shot_size = shot_size_for(analysis, role, position, scene)
    characters = analysis["characters"] or [primary_character(scene)]
    props = analysis["props"]
    anchors = list(dict.fromkeys([scene.get("location", "")] + characters + props))
    anchors = [anchor for anchor in anchors if anchor]
    return {
        "shot_id": "",
        "shot_role": role,
        "shot_size": shot_size,
        "duration_seconds": duration_for(analysis, role),
        "camera_setup": camera_setup_for(analysis, shot_size, role),
        "camera_motion": "固定" if "前推" not in camera_setup_for(analysis, shot_size, role) else "轻推",
        "viewpoint": viewpoint_for(analysis),
        "axis_side": "A",
        "frame_description": frame_description(scene, analysis, shot_size),
        "action": str(beat.get("text", "")),
        "transition_note": "",
        "emotion": analysis["emotion"],
        "scene_objective": scene_goal,
        "audience_focus": audience_note,
        "narrative_purpose": narrative_purpose_for(role, analysis),
        "info_control": info_control_for(role, analysis),
        "continuity_anchors": anchors,
        "state_snapshot": state_snapshot(str(beat.get("text", "")), characters, props),
        "beat_refs": [str(beat.get("beat_id"))],
    }


def transition_note(shot: Dict[str, object], next_shot: Dict[str, object] | None) -> str:
    if next_shot is None:
        return "动作收住，本场结束。"
    action = str(shot.get("action", ""))
    shared = [anchor for anchor in shot.get("continuity_anchors", []) if anchor in next_shot.get("continuity_anchors", [])]
    ignored = set(shot.get("state_snapshot", {}).get("characters", []))
    ignored.update(anchor for anchor in shared if any(hint in anchor for hint in ["室", "馆", "楼下", "走廊", "门口"]))
    focus = next((anchor for anchor in shared if anchor not in ignored), "")
    if next_shot.get("shot_role") == "connector" and shot.get("shot_size") in {"全景", "大全景"}:
        return f"空间落稳后，接到 {next_shot['shot_id']} 的起手动作。"
    if any(keyword in action for keyword in LOOK_KEYWORDS):
        return f"视线带到 {next_shot['shot_id']}。"
    if focus and next_shot.get("shot_size") in {"特写", "插入特写"}:
        return f"顺着{focus}压到 {next_shot['shot_id']}。"
    if any(keyword in action for keyword in ["翻", "抬头", "转头", "推", "拉", "拿", "放", "撕", "开", "关", "踹", "捡起"]):
        return f"动作接切到 {next_shot['shot_id']}。"
    if next_shot.get("info_control") == "reaction":
        return f"反应切到 {next_shot['shot_id']}。"
    if next_shot.get("info_control") == "reveal":
        return f"信息揭示切到 {next_shot['shot_id']}。"
    if next_shot.get("shot_role") == "connector":
        return f"补一个顺接镜过渡到 {next_shot['shot_id']}。"
    return f"顺切到 {next_shot['shot_id']}。"


def build_scene_plan(scene: Dict[str, object], scene_number: int, constraints: Dict[str, object]) -> Dict[str, object]:
    analyses = build_analysis(scene, constraints)
    if not analyses:
        return {
            "scene_id": scene.get("scene_id", f"S{scene_number}"),
            "scene_number": scene_number,
            "heading": scene.get("heading", ""),
            "location": scene.get("location", ""),
            "scene_objective": "让观众清楚看到本场的基本信息。",
            "audience_focus": "先交代场景，再给出最基本的人物状态。",
            "meaningful_changes": [],
            "main_shots": [],
            "connector_shots": [],
            "continuity_risks": [],
            "transition_audit": [],
            "shots": [],
        }

    scene_goal = scene_objective(scene, analyses)
    audience_note = audience_focus(scene, analyses)
    mains = select_main_indices(analyses)
    connectors = connector_indices(analyses, mains)
    selected_roles = {index: "main" for index in mains}
    for index in connectors:
        selected_roles.setdefault(index, "connector")

    ordered_indices = sorted(selected_roles)
    shots = [
        build_shot(
            scene=scene,
            analysis=analyses[index],
            role=selected_roles[index],
            position=position,
            scene_goal=scene_goal,
            audience_note=audience_note,
        )
        for position, index in enumerate(ordered_indices)
    ]

    scene_plan = {
        "scene_id": scene.get("scene_id", f"S{scene_number}"),
        "scene_number": scene_number,
        "heading": scene.get("heading", ""),
        "location": scene.get("location", ""),
        "scene_objective": scene_goal,
        "audience_focus": audience_note,
        "meaningful_changes": [analyses[index]["beat"]["text"] for index in mains],
        "main_shots": [],
        "connector_shots": [],
        "continuity_risks": [],
        "transition_audit": [],
        "shots": shots,
    }

    scene_plan = repair_scene_shots(scene_plan)

    for index, shot in enumerate(scene_plan["shots"]):
        next_shot = scene_plan["shots"][index + 1] if index + 1 < len(scene_plan["shots"]) else None
        shot["transition_note"] = transition_note(shot, next_shot)

    scene_plan["main_shots"] = [shot["shot_id"] for shot in scene_plan["shots"] if shot.get("shot_role") == "main"]
    scene_plan["connector_shots"] = [shot["shot_id"] for shot in scene_plan["shots"] if shot.get("shot_role") == "connector"]
    return scene_plan


def plan_project(normalized: Dict[str, object], constraints: Dict[str, object]) -> Dict[str, object]:
    scenes = [
        build_scene_plan(scene, index, constraints)
        for index, scene in enumerate(normalized.get("scenes", []), start=1)
    ]
    return {
        "project": {
            "title": normalized.get("title", "Untitled"),
            "language": constraints.get("language", "zh"),
            "medium": constraints.get("medium", "通用影视分镜"),
            "rhythm_mode": constraints.get("rhythm_mode", "适度重构节奏"),
            "output_mode": constraints.get("output_mode", "final_shotlist_only"),
            "constraints": constraints,
        },
        "scenes": scenes,
    }


def main() -> int:
    args = parse_args()
    normalized = json.loads(Path(args.input).read_text())
    constraints = load_constraints(args.constraints)
    plan = plan_project(normalized, constraints)
    output_text = json.dumps(plan, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output_text + "\n")
    else:
        print(output_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
