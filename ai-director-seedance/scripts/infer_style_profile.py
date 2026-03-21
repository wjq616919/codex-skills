#!/usr/bin/env python3
"""Infer or merge a style profile for the AI director skill."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List


BASE_PROFILES: Dict[str, Dict[str, object]] = {
    "drama": {
        "medium": "cinematic live action",
        "realism_level": "grounded",
        "palette": "naturalistic muted palette",
        "contrast": "medium",
        "texture": "real-world texture",
        "lighting_bias": "motivated practical light",
        "movement_energy": "restrained",
        "composition_density": "balanced",
        "rhythm": "measured",
        "audience": "general audience",
        "prompt_tags": ["emotional realism"]
    },
    "thriller": {
        "medium": "cinematic live action",
        "realism_level": "grounded heightened tension",
        "palette": "cool shadows with selective warm contrast",
        "contrast": "high",
        "texture": "hard edges and wet reflections",
        "lighting_bias": "low-key motivated lighting",
        "movement_energy": "controlled but tense",
        "composition_density": "compressed",
        "rhythm": "tight escalation",
        "audience": "adult audience",
        "prompt_tags": ["tension", "suspense", "controlled geometry"]
    },
    "romance": {
        "medium": "cinematic live action",
        "realism_level": "grounded with lyrical warmth",
        "palette": "warm skin tones with soft complementary accents",
        "contrast": "soft-medium",
        "texture": "gentle bloom and atmospheric softness",
        "lighting_bias": "soft directional light",
        "movement_energy": "gentle",
        "composition_density": "clean",
        "rhythm": "breathing emotional rhythm",
        "audience": "broad audience",
        "prompt_tags": ["emotional intimacy", "lyrical atmosphere"]
    },
    "comedy": {
        "medium": "cinematic live action",
        "realism_level": "grounded readable stylization",
        "palette": "clean readable color separation",
        "contrast": "medium",
        "texture": "clean practical environments",
        "lighting_bias": "readable high-key motivated light",
        "movement_energy": "nimble",
        "composition_density": "readable layered staging",
        "rhythm": "snappy",
        "audience": "broad audience",
        "prompt_tags": ["readable reactions", "comic timing"]
    },
    "historical": {
        "medium": "epic cinematic live action",
        "realism_level": "grounded period stylization",
        "palette": "earth tones with controlled accents",
        "contrast": "medium-high",
        "texture": "fabric, dust, wood, stone",
        "lighting_bias": "natural firelight and daylight motivation",
        "movement_energy": "controlled grandeur",
        "composition_density": "rich layered depth",
        "rhythm": "deliberate",
        "audience": "broad audience",
        "prompt_tags": ["period detail", "spatial scale"]
    },
    "fantasy": {
        "medium": "cinematic stylized live action",
        "realism_level": "stylized mythic",
        "palette": "selective magical palette with controlled contrast",
        "contrast": "medium-high",
        "texture": "atmospheric haze and stylized detail",
        "lighting_bias": "expressive motivated light",
        "movement_energy": "fluid",
        "composition_density": "layered depth and negative space",
        "rhythm": "lyrical progression",
        "audience": "broad audience",
        "prompt_tags": ["mythic atmosphere", "visual wonder"]
    },
    "scifi": {
        "medium": "cinematic live action",
        "realism_level": "designed high-tech realism",
        "palette": "cool neutrals with luminous accents",
        "contrast": "high",
        "texture": "clean engineered surfaces",
        "lighting_bias": "precise practical and emissive light",
        "movement_energy": "precise",
        "composition_density": "controlled geometry",
        "rhythm": "systematic build",
        "audience": "broad audience",
        "prompt_tags": ["futuristic precision", "engineered space"]
    },
    "wuxia": {
        "medium": "cinematic stylized live action",
        "realism_level": "poetic stylization",
        "palette": "limited palette with ink-like accents",
        "contrast": "medium-high",
        "texture": "mist, fabric flow, calligraphic negative space",
        "lighting_bias": "expressive directional light",
        "movement_energy": "gliding",
        "composition_density": "negative space with elegant layering",
        "rhythm": "graceful escalation",
        "audience": "broad audience",
        "prompt_tags": ["poetic motion", "martial elegance", "ink mood"]
    },
    "documentary": {
        "medium": "documentary realism",
        "realism_level": "high realism",
        "palette": "natural color reproduction",
        "contrast": "medium",
        "texture": "real-world imperfections",
        "lighting_bias": "available light first",
        "movement_energy": "observational",
        "composition_density": "functional readability",
        "rhythm": "observational progression",
        "audience": "general audience",
        "prompt_tags": ["observational camera", "real-life texture"]
    }
}


KEYWORDS: Dict[str, List[str]] = {
    "thriller": ["thriller", "suspense", "murder", "chase", "fear", "panic", "追杀", "悬疑", "惊悚", "恐惧", "逃亡"],
    "romance": ["romance", "love", "kiss", "longing", "heartbreak", "爱情", "心动", "告白", "拥抱", "离别"],
    "comedy": ["comedy", "funny", "awkward", "absurd", "joke", "搞笑", "喜剧", "荒诞", "尴尬", "笑"],
    "historical": ["dynasty", "kingdom", "period", "warlord", "palace", "古代", "王朝", "宫廷", "民国", "史诗"],
    "fantasy": ["magic", "dragon", "myth", "spell", "spirit", "奇幻", "神话", "仙", "妖", "法术"],
    "scifi": ["spaceship", "android", "future", "cyber", "lab", "科幻", "未来", "机器人", "太空", "实验室"],
    "wuxia": ["sword", "jianghu", "martial", "sect", "剑", "江湖", "武侠", "门派", "侠客"],
    "documentary": ["documentary", "interview", "archive", "observational", "纪录片", "采访", "纪实", "档案"]
}


def load_jsonish(value: str) -> Dict[str, object]:
    path = Path(value)
    if path.exists():
        return json.loads(path.read_text())
    return json.loads(value)


def detect_genre(script: str) -> str:
    lowered = script.lower()
    scores = {name: 0 for name in BASE_PROFILES}
    for genre, words in KEYWORDS.items():
        for word in words:
            scores[genre] += lowered.count(word.lower())
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "drama"


def collect_reasons(script: str, genre: str) -> List[str]:
    reasons = [f"genre evidence points to {genre}"]
    lowered = script.lower()
    if re.search(r"\bnight\b|夜|雨|storm|rain", lowered):
        reasons.append("script contains low-light or weather cues")
    if re.search(r"\btrain\b|station|platform|车站|列车", lowered):
        reasons.append("script suggests strong location-based practical lighting")
    if re.search(r"kiss|embrace|拥抱|告白|离别", lowered):
        reasons.append("script emphasizes emotional intimacy")
    if re.search(r"fight|sword|gun|追|跑|battle|爆炸", lowered):
        reasons.append("script implies higher movement or tension")
    return reasons


def merge_dicts(base: Dict[str, object], override: Dict[str, object]) -> Dict[str, object]:
    merged = dict(base)
    for key, value in override.items():
        if key == "prompt_tags" and isinstance(value, list):
            existing = list(merged.get("prompt_tags", []))
            merged["prompt_tags"] = existing + [item for item in value if item not in existing]
        else:
            merged[key] = value
    return merged


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Infer or merge a style profile.")
    parser.add_argument("--script", required=True, help="Path to the script text file")
    parser.add_argument(
        "--mode",
        choices=["inferred", "locked", "hybrid"],
        default="inferred",
        help="How style should be resolved"
    )
    parser.add_argument(
        "--style-override",
        help="JSON string or path to JSON containing locked style fields"
    )
    parser.add_argument("--output", help="Optional output file path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    script_path = Path(args.script)
    script_text = script_path.read_text()

    genre = detect_genre(script_text)
    profile = dict(BASE_PROFILES[genre])
    reasons = collect_reasons(script_text, genre)

    style_mode = {
        "inferred": "script_inferred_style",
        "locked": "user_locked_style",
        "hybrid": "hybrid_style"
    }[args.mode]

    locked_fields: Dict[str, object] = {}
    if args.style_override:
        locked_fields = load_jsonish(args.style_override)
        profile = merge_dicts(profile, locked_fields)
        reasons.append("style override fields were merged on top of the inferred base")

    result = {
        "style_mode": style_mode,
        "detected_genre": genre,
        "style_profile": profile,
        "style_rationale": reasons,
        "inherited_fields": sorted(locked_fields.keys())
    }

    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output + "\n")
    else:
        sys.stdout.write(output + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
