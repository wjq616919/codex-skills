#!/usr/bin/env python3
"""Normalize screenplay-like or narrative Chinese text into scene/beat JSON."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List


SCENE_HEADING_RE = re.compile(
    r"^(?:INT|EXT|INT/EXT|EXT/INT|INT\.?/EXT\.?|EXT\.?/INT\.?|内景|外景|内/外景|外/内景|场景\s*\d+|scene\s+\d+)\b",
    re.IGNORECASE,
)
SPEAKER_RE = re.compile(r"^([A-Z][A-Z0-9 '\-()]{1,40}|[\u4e00-\u9fff]{1,12})[:：]\s*(.+)$")
UPPERCASE_CHARACTER_RE = re.compile(r"\b([A-Z][A-Z]+(?: [A-Z][A-Z]+){0,2})\b")
MULTI_NAME_RE = re.compile(r"([\u4e00-\u9fff]{2,3})(?:和|与)([\u4e00-\u9fff]{2,3})(?=隔|坐|站|说|看|把|没|不|$)")
CHINESE_NAME_HINT_RE = re.compile(
    r"([\u4e00-\u9fff]{2,4})(?=[^。！？\n]{0,2}(?:说|看|望|盯|坐|站|走|跑|抬|翻|拿|推|拉|递|抱|哭|笑|停|愣|深吸|推门|开门|关门|没有|听见|捡起))"
)
TIME_HINTS = ["凌晨", "清晨", "早晨", "上午", "中午", "下午", "傍晚", "黄昏", "夜", "夜晚", "白天", "DAY", "NIGHT", "MORNING", "EVENING"]
SPEAKER_STOP_WORDS = ["声音", "门外", "传来", "说道", "电话里", "屏幕上", "旁白", "画外"]
INVALID_CHARACTER_SUFFIXES = ("前", "后", "里", "外", "上", "下", "中", "间", "边")
TRAILING_ACTION_PARTS = ("没有", "只是", "正在", "慢慢", "忽然")


def split_blocks(text: str) -> List[str]:
    blocks = re.split(r"\n\s*\n", text.strip())
    return [block.strip() for block in blocks if block.strip()]


def parse_heading(block: str) -> Dict[str, str]:
    line = block.splitlines()[0].strip()
    cleaned = re.sub(
        r"^(?:INT|EXT|INT/EXT|EXT/INT|INT\.?/EXT\.?|EXT\.?/INT\.?|内景|外景|内/外景|外/内景)\.?\s*",
        "",
        line,
        flags=re.IGNORECASE,
    ).strip(" -，,。")

    parts = [part.strip(" -，,。") for part in re.split(r"\s*[,-]\s*|，", cleaned) if part.strip()]
    location = parts[0] if parts else cleaned
    time_of_day = ""
    for hint in TIME_HINTS:
        if hint.lower() in line.lower():
            time_of_day = hint
            break
    return {"heading": line, "location": location, "time_of_day": time_of_day}


def split_sentences(text: str) -> List[str]:
    pieces = re.split(r"(?<=[。！？!?；;])\s*", text.strip())
    return [piece.strip() for piece in pieces if piece.strip()]


def normalize_character_candidate(candidate: str) -> str:
    candidate = candidate.strip()
    for suffix in TRAILING_ACTION_PARTS:
        if candidate.endswith(suffix) and len(candidate) - len(suffix) >= 2:
            candidate = candidate[: -len(suffix)]
    if candidate.endswith("说") and len(candidate) > 2:
        candidate = candidate[:-1]
    return candidate


def extract_characters(text: str) -> List[str]:
    found: List[str] = []
    for candidate in UPPERCASE_CHARACTER_RE.findall(text):
        if candidate not in {"INT", "EXT", "DAY", "NIGHT"} and candidate not in found:
            found.append(candidate)
    for left, right in MULTI_NAME_RE.findall(text):
        for candidate in (left, right):
            candidate = normalize_character_candidate(candidate)
            if any(stop_word in candidate for stop_word in SPEAKER_STOP_WORDS):
                continue
            if candidate.endswith(INVALID_CHARACTER_SUFFIXES):
                continue
            if candidate not in found:
                found.append(candidate)
    for candidate in CHINESE_NAME_HINT_RE.findall(text):
        candidate = normalize_character_candidate(candidate)
        if len(candidate) < 2:
            continue
        if any(stop_word in candidate for stop_word in SPEAKER_STOP_WORDS):
            continue
        if candidate.endswith(INVALID_CHARACTER_SUFFIXES):
            continue
        if candidate in {"今天", "这样", "外面", "桌上", "窗外"}:
            continue
        if candidate not in found:
            found.append(candidate)
    return found


def clean_speaker_name(candidate: str) -> str:
    return re.sub(r"(说|问|答|喊|叫|道)$", "", candidate.strip())


def is_likely_speaker_name(candidate: str) -> bool:
    candidate = clean_speaker_name(candidate)
    if not candidate:
        return False
    if any(stop_word in candidate for stop_word in SPEAKER_STOP_WORDS):
        return False
    if "的" in candidate:
        return False
    if re.search(r"[，。！？!?；;]", candidate):
        return False
    if re.search(r"[A-Z]", candidate):
        return True
    return len(candidate) <= 6


def flush_scene(scenes: List[Dict[str, object]], scene: Dict[str, object] | None) -> None:
    if not scene:
        return
    scene["raw_text"] = "\n".join(scene["raw_text"]).strip()
    scenes.append(scene)


def ensure_scene(scenes: List[Dict[str, object]], scene: Dict[str, object] | None) -> Dict[str, object]:
    if scene is not None:
        return scene
    return {
        "scene_id": f"S{len(scenes) + 1}",
        "heading": "未标注场景",
        "location": "",
        "time_of_day": "",
        "raw_text": [],
        "raw_blocks": [],
        "beats": [],
        "action_blocks": [],
        "dialogue_blocks": [],
        "present_characters": [],
    }


def add_beat(scene: Dict[str, object], beat_type: str, text: str, block_id: str, speaker: str = "") -> None:
    text = text.strip()
    if not text:
        return
    beat_index = len(scene["beats"]) + 1
    beat_id = f"{scene['scene_id']}-B{beat_index:02d}"
    characters = [speaker] if speaker else extract_characters(text)
    for candidate in characters:
        if candidate not in scene["present_characters"]:
            scene["present_characters"].append(candidate)
    scene["beats"].append(
        {
            "beat_id": beat_id,
            "block_id": block_id,
            "index": beat_index,
            "type": beat_type,
            "speaker": speaker,
            "text": text,
            "characters": characters,
        }
    )


def normalize(text: str, title: str) -> Dict[str, object]:
    blocks = split_blocks(text)
    scenes: List[Dict[str, object]] = []
    scene: Dict[str, object] | None = None
    screenplay_like = False

    for block in blocks:
        first_line = block.splitlines()[0].strip()
        if SCENE_HEADING_RE.match(first_line):
            screenplay_like = True
            flush_scene(scenes, scene)
            heading = parse_heading(block)
            scene = {
                "scene_id": f"S{len(scenes) + 1}",
                "heading": heading["heading"],
                "location": heading["location"],
                "time_of_day": heading["time_of_day"],
                "raw_text": [],
                "raw_blocks": [],
                "beats": [],
                "action_blocks": [],
                "dialogue_blocks": [],
                "present_characters": [],
            }
            remaining_lines = [line.strip() for line in block.splitlines()[1:] if line.strip()]
            if remaining_lines:
                block = "\n".join(remaining_lines)
            else:
                continue

        scene = ensure_scene(scenes, scene)
        block_id = f"{scene['scene_id']}-R{len(scene['raw_blocks']) + 1:02d}"
        block_lines = [line.strip() for line in block.splitlines() if line.strip()]
        scene["raw_text"].append(block)
        scene["raw_blocks"].append({"block_id": block_id, "text": block})

        for line in block_lines:
            speaker_match = SPEAKER_RE.match(line)
            if speaker_match and is_likely_speaker_name(speaker_match.group(1)):
                screenplay_like = True
                speaker = clean_speaker_name(speaker_match.group(1))
                dialogue = speaker_match.group(2).strip()
                scene["dialogue_blocks"].append({"block_id": block_id, "speaker": speaker, "text": dialogue})
                add_beat(scene, "dialogue", dialogue, block_id, speaker=speaker)
                continue

            scene["action_blocks"].append({"block_id": block_id, "text": line})
            sentences = split_sentences(line)
            for sentence in sentences:
                add_beat(scene, "action", sentence, block_id)

    flush_scene(scenes, scene)

    source_format = "screenplay_like" if screenplay_like else "narrative"
    return {
        "title": title,
        "source_format": source_format,
        "scene_count": len(scenes),
        "scenes": scenes,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize script text into scene/beat JSON.")
    parser.add_argument("--input", required=True, help="Input text file")
    parser.add_argument("--output", help="Output JSON path")
    parser.add_argument("--title", help="Optional title override")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    text = input_path.read_text()
    title = args.title or input_path.stem.replace("_", " ").replace("-", " ").title()
    normalized = normalize(text, title)
    output_text = json.dumps(normalized, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output_text + "\n")
    else:
        print(output_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
