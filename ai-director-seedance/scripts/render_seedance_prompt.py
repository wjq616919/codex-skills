#!/usr/bin/env python3
"""Render Seedance-oriented prompts from a structured shot plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List


STYLE_MODE_LABELS = {
    "script_inferred_style": "script inferred",
    "user_locked_style": "user locked",
    "hybrid_style": "hybrid"
}

ZH_STYLE_MODE_LABELS = {
    "script_inferred_style": "按剧本推导",
    "user_locked_style": "按用户锁定风格",
    "hybrid_style": "混合风格"
}

ZH_TERM_MAP = {
    "wide": "远景",
    "full": "全景人物",
    "medium_full": "中全景",
    "medium": "中景",
    "medium_close": "近中景",
    "close_up": "特写",
    "extreme_close_up": "大特写",
    "insert": "插入特写",
    "eye_level": "平视",
    "high_angle": "俯角",
    "low_angle": "仰角",
    "overhead": "高位俯拍",
    "top_down": "顶拍",
    "profile": "侧面",
    "over_shoulder": "过肩",
    "point_of_view": "主观视角",
    "slight_profile": "轻微侧面",
    "neutral_standard": "标准焦段视感",
    "intimate_portrait": "人像焦段视感",
    "expansive_wide": "广角视感",
    "compressed_telephoto": "长焦压缩视感",
    "macro_detail": "微距细节视感",
    "slow_push_in": "缓慢推进",
    "follow": "跟随拍摄",
    "locked_off": "固定机位",
    "lateral_track": "横向跟移",
    "orbit": "环绕",
    "dolly_in": "推轨",
    "dolly_out": "拉轨",
    "crane_up": "升镜",
    "crane_down": "降镜",
    "tilt": "摇镜",
    "pan": "摇摄",
    "whip_pan": "甩摇",
    "rack_focus": "焦点切换",
    "handheld_subtle": "轻微手持",
    "handheld_urgent": "急促手持",
    "motivated_practical": "动机光源",
    "backlit": "逆光",
    "backlit rain haze": "逆光雨雾",
    "soft_side_light": "柔和侧光",
    "practical warm rim light": "暖色实用轮廓光",
    "soft_side_light with practical warm rim light": "柔和侧光与暖色实用轮廓光",
    "negative_space": "留白构图",
    "layered_depth": "层次纵深",
    "off_center": "偏心构图",
    "clean_background": "干净背景"
}

ZH_SOUND_TERM_MAP = {
    "ambience_forward": "环境氛围前置",
    "foley_forward": "拟音前置",
    "character_reaction_forward": "角色反应声前置",
    "music_forward": "配乐前置",
    "brand_mnemonic_forward": "品牌声记忆前置"
}

OUTPUT_MODES = {"storyboard_script", "final_prompt_only", "director_review"}


def zh_term(value: str) -> str:
    return ZH_TERM_MAP.get(value, value)


def zh_csv_terms(value: str) -> str:
    items = [item.strip() for item in value.split(",")]
    return "、".join(zh_term(item) for item in items if item)


def zh_sound_term(value: str) -> str:
    return ZH_SOUND_TERM_MAP.get(value, value)


def merge_profiles(*profiles: Dict[str, object]) -> Dict[str, object]:
    merged: Dict[str, object] = {}
    for profile in profiles:
        if not profile:
            continue
        for key, value in profile.items():
            if key == "prompt_tags" and isinstance(value, list):
                existing = list(merged.get("prompt_tags", []))
                merged["prompt_tags"] = existing + [item for item in value if item not in existing]
            else:
                merged[key] = value
    return merged


def beats_to_text(beats: List[Dict[str, object]], language: str) -> str:
    if not beats:
        return ""
    parts = []
    for beat in beats:
        start = beat["start"]
        end = beat["end"]
        desc = beat["description"]
        if language == "zh":
            parts.append(f"[{start:g}s-{end:g}s] {desc}")
        else:
            parts.append(f"[{start:g}s-{end:g}s] {desc}")
    return " ".join(parts)


def zh_sound_line(shot: Dict[str, object], audio_profile: Dict[str, object]) -> str:
    sound = shot.get("sound_design", {})
    if not sound and not audio_profile:
        return ""
    parts = []
    if sound.get("ambience"):
        parts.append(f"环境氛围：{sound['ambience']}")
    if sound.get("foley"):
        parts.append(f"拟音：{sound['foley']}")
    if sound.get("character_vocalization"):
        parts.append(f"角色微表演声音：{sound['character_vocalization']}")
    if sound.get("magic_or_stylized_sfx"):
        parts.append(f"魔法/风格化音效：{sound['magic_or_stylized_sfx']}")
    if sound.get("music") or audio_profile.get("score_style"):
        music = sound.get("music") or audio_profile.get("score_style")
        parts.append(f"配乐：{music}")
    if sound.get("mix_focus"):
        parts.append(f"混音重点：{zh_sound_term(sound['mix_focus'])}")
    if sound.get("brand_mnemonic") or audio_profile.get("brand_mnemonic"):
        mnemonic = sound.get("brand_mnemonic") or audio_profile.get("brand_mnemonic")
        if mnemonic:
            parts.append(f"品牌声音记忆：{mnemonic}")
    if sound.get("audio_reference_hint"):
        parts.append(f"音频参考：{sound['audio_reference_hint']}")
    return "；".join(parts)


def zh_scene_sound_line(scene: Dict[str, object], audio_profile: Dict[str, object]) -> str:
    ambience: List[str] = []
    foley: List[str] = []
    vocals: List[str] = []
    sfx: List[str] = []
    music: List[str] = []
    mnemonic: List[str] = []

    def add_unique(target: List[str], value: str) -> None:
        if value and value not in target:
            target.append(value)

    for shot in scene.get("shots", []):
        sound = shot.get("sound_design", {})
        add_unique(ambience, str(sound.get("ambience", "")))
        add_unique(foley, str(sound.get("foley", "")))
        add_unique(vocals, str(sound.get("character_vocalization", "")))
        add_unique(sfx, str(sound.get("magic_or_stylized_sfx", "")))
        add_unique(music, str(sound.get("music", "")))
        add_unique(mnemonic, str(sound.get("brand_mnemonic", "")))

    if audio_profile.get("score_style"):
        add_unique(music, str(audio_profile["score_style"]))
    if audio_profile.get("brand_mnemonic"):
        add_unique(mnemonic, str(audio_profile["brand_mnemonic"]))

    parts = []
    if ambience:
        parts.append(f"环境：{'；'.join(ambience)}")
    if foley:
        parts.append(f"拟音：{'；'.join(foley)}")
    if vocals:
        parts.append(f"角色声音：{'；'.join(vocals)}")
    if sfx:
        parts.append(f"音效：{'；'.join(sfx)}")
    if music:
        parts.append(f"配乐：{'；'.join(music)}")
    if mnemonic:
        parts.append(f"品牌声音：{'；'.join(mnemonic)}")
    return " ".join(parts)


def en_sound_line(shot: Dict[str, object], audio_profile: Dict[str, object]) -> str:
    sound = shot.get("sound_design", {})
    if not sound and not audio_profile:
        return ""
    parts = []
    if sound.get("ambience"):
        parts.append(f"ambience: {sound['ambience']}")
    if sound.get("foley"):
        parts.append(f"foley: {sound['foley']}")
    if sound.get("character_vocalization"):
        parts.append(f"character micro-vocals: {sound['character_vocalization']}")
    if sound.get("magic_or_stylized_sfx"):
        parts.append(f"stylized sfx: {sound['magic_or_stylized_sfx']}")
    if sound.get("music") or audio_profile.get("score_style"):
        music = sound.get("music") or audio_profile.get("score_style")
        parts.append(f"music: {music}")
    if sound.get("mix_focus"):
        parts.append(f"mix focus: {sound['mix_focus']}")
    if sound.get("brand_mnemonic") or audio_profile.get("brand_mnemonic"):
        mnemonic = sound.get("brand_mnemonic") or audio_profile.get("brand_mnemonic")
        if mnemonic:
            parts.append(f"brand mnemonic: {mnemonic}")
    if sound.get("audio_reference_hint"):
        parts.append(f"audio reference: {sound['audio_reference_hint']}")
    return "; ".join(parts)


def zh_lighting_line(shot: Dict[str, object], profile: Dict[str, object]) -> str:
    design = shot.get("lighting_design", {})
    parts = []
    if design.get("key_light"):
        parts.append(f"主光：{design['key_light']}")
    if design.get("fill_light"):
        parts.append(f"辅光：{design['fill_light']}")
    if design.get("rim_light"):
        parts.append(f"轮廓光：{design['rim_light']}")
    if design.get("background_light"):
        parts.append(f"背景光：{design['background_light']}")
    if design.get("color_relation"):
        parts.append(f"色温关系：{design['color_relation']}")
    if design.get("motivated_source"):
        parts.append(f"光源动机：{design['motivated_source']}")
    if design.get("contrast"):
        parts.append(f"反差：{design['contrast']}")
    if design.get("material_response"):
        parts.append(f"材质重点：{design['material_response']}")
    if parts:
        return "；".join(parts)

    fallback = []
    if shot.get("lighting"):
        fallback.append(f"光线锚点：{zh_csv_terms(str(shot['lighting']))}")
    if profile.get("lighting_bias"):
        fallback.append(f"整体光线倾向：{profile['lighting_bias']}")
    return "；".join(fallback)


def en_lighting_line(shot: Dict[str, object], profile: Dict[str, object]) -> str:
    design = shot.get("lighting_design", {})
    parts = []
    if design.get("key_light"):
        parts.append(f"key light: {design['key_light']}")
    if design.get("fill_light"):
        parts.append(f"fill light: {design['fill_light']}")
    if design.get("rim_light"):
        parts.append(f"rim light: {design['rim_light']}")
    if design.get("background_light"):
        parts.append(f"background light: {design['background_light']}")
    if design.get("color_relation"):
        parts.append(f"color relation: {design['color_relation']}")
    if design.get("motivated_source"):
        parts.append(f"motivated source: {design['motivated_source']}")
    if design.get("contrast"):
        parts.append(f"contrast: {design['contrast']}")
    if design.get("material_response"):
        parts.append(f"material response: {design['material_response']}")
    if parts:
        return "; ".join(parts)

    fallback = []
    if shot.get("lighting"):
        fallback.append(f"lighting anchors: {shot['lighting']}")
    if profile.get("lighting_bias"):
        fallback.append(f"overall lighting bias: {profile['lighting_bias']}")
    return "; ".join(fallback)


def zh_decision_line(shot: Dict[str, object]) -> str:
    decision = shot.get("director_decision", {})
    parts = []
    if shot.get("narrative_purpose"):
        parts.append(f"目的：{shot['narrative_purpose']}")
    if shot.get("audience_focus"):
        parts.append(f"观众先看：{shot['audience_focus']}")
    if decision.get("blocking_plan"):
        parts.append(f"主体调度：{decision['blocking_plan']}")
    if decision.get("composition_goal"):
        parts.append(f"构图目标：{decision['composition_goal']}")
    if decision.get("focus_shift"):
        parts.append(f"视觉重心转移：{decision['focus_shift']}")
    if decision.get("movement_motivation"):
        parts.append(f"运镜动机：{decision['movement_motivation']}")
    if decision.get("tempo"):
        parts.append(f"节奏：{decision['tempo']}")
    if decision.get("transition_reason"):
        parts.append(f"转场依据：{decision['transition_reason']}")
    return "；".join(parts)


def en_decision_line(shot: Dict[str, object]) -> str:
    decision = shot.get("director_decision", {})
    parts = []
    if shot.get("narrative_purpose"):
        parts.append(f"purpose: {shot['narrative_purpose']}")
    if shot.get("audience_focus"):
        parts.append(f"audience focus: {shot['audience_focus']}")
    if decision.get("blocking_plan"):
        parts.append(f"blocking: {decision['blocking_plan']}")
    if decision.get("composition_goal"):
        parts.append(f"composition goal: {decision['composition_goal']}")
    if decision.get("focus_shift"):
        parts.append(f"focus shift: {decision['focus_shift']}")
    if decision.get("movement_motivation"):
        parts.append(f"movement motivation: {decision['movement_motivation']}")
    if decision.get("tempo"):
        parts.append(f"tempo: {decision['tempo']}")
    if decision.get("transition_reason"):
        parts.append(f"transition reason: {decision['transition_reason']}")
    return "; ".join(parts)


def zh_critique_line(shot: Dict[str, object]) -> str:
    critique = shot.get("critique_pass", {})
    parts = []
    if critique.get("primary_risk"):
        parts.append(f"风险：{critique['primary_risk']}")
    if critique.get("why_it_can_fail"):
        parts.append(f"为什么会失手：{critique['why_it_can_fail']}")
    if critique.get("correction"):
        parts.append(f"修正：{critique['correction']}")
    if critique.get("verified_choice"):
        parts.append(f"定稿依据：{critique['verified_choice']}")
    return "；".join(parts)


def en_critique_line(shot: Dict[str, object]) -> str:
    critique = shot.get("critique_pass", {})
    parts = []
    if critique.get("primary_risk"):
        parts.append(f"risk: {critique['primary_risk']}")
    if critique.get("why_it_can_fail"):
        parts.append(f"failure reason: {critique['why_it_can_fail']}")
    if critique.get("correction"):
        parts.append(f"correction: {critique['correction']}")
    if critique.get("verified_choice"):
        parts.append(f"verified choice: {critique['verified_choice']}")
    return "; ".join(parts)


def zh_evaluation_line(shot: Dict[str, object]) -> str:
    evaluation = shot.get("evaluation", {})
    if not evaluation:
        return ""
    parts = []
    label_map = [
        ("narrative_fidelity", "叙事"),
        ("protagonist_priority", "主体"),
        ("blocking_clarity", "调度"),
        ("composition_logic", "构图"),
        ("camera_motivation", "运镜"),
        ("rhythm_control", "节奏"),
        ("action_timing_readability", "时长"),
        ("generation_controllability", "可控"),
    ]
    for key, label in label_map:
        value = evaluation.get(key)
        if isinstance(value, (int, float)):
            parts.append(f"{label}{float(value):.1f}")
    overall = evaluation.get("overall_score")
    if isinstance(overall, (int, float)):
        parts.append(f"总分{float(overall):.2f}/5")
    if evaluation.get("verdict"):
        parts.append(f"结论：{evaluation['verdict']}")
    if evaluation.get("notes"):
        parts.append(f"备注：{evaluation['notes']}")
    return " ".join(parts)


def en_evaluation_line(shot: Dict[str, object]) -> str:
    evaluation = shot.get("evaluation", {})
    if not evaluation:
        return ""
    parts = []
    label_map = [
        ("narrative_fidelity", "narrative"),
        ("protagonist_priority", "protagonist"),
        ("blocking_clarity", "blocking"),
        ("composition_logic", "composition"),
        ("camera_motivation", "camera"),
        ("rhythm_control", "rhythm"),
        ("action_timing_readability", "timing"),
        ("generation_controllability", "controllability"),
    ]
    for key, label in label_map:
        value = evaluation.get(key)
        if isinstance(value, (int, float)):
            parts.append(f"{label} {float(value):.1f}")
    overall = evaluation.get("overall_score")
    if isinstance(overall, (int, float)):
        parts.append(f"overall {float(overall):.2f}/5")
    if evaluation.get("verdict"):
        parts.append(f"verdict: {evaluation['verdict']}")
    if evaluation.get("notes"):
        parts.append(f"notes: {evaluation['notes']}")
    return "; ".join(parts)


def zh_prompt(shot: Dict[str, object], profile: Dict[str, object], mode: str) -> str:
    parts = [shot["subject"], shot["setting"], shot["action"]]
    style_terms = [profile.get("medium", ""), profile.get("palette", ""), profile.get("texture", "")]
    style_terms = [term for term in style_terms if term]
    if style_terms:
        parts.append("，".join(style_terms))
    parts.append(f"{zh_term(shot['shot_size'])}，{zh_term(shot['angle'])}，{zh_term(shot['lens'])}")
    if shot.get("foreground"):
        parts.append(shot["foreground"])
    if shot.get("composition"):
        parts.append(f"构图{zh_csv_terms(shot['composition'])}")
    parts.append(f"光线{zh_csv_terms(shot['lighting'])}")
    parts.append(f"运镜{zh_term(shot['camera_movement'])}")
    return "，".join([part for part in parts if part]).rstrip("，。") + "。"


def en_prompt(shot: Dict[str, object], profile: Dict[str, object], mode: str) -> str:
    parts = [shot["subject"], shot["setting"], shot["action"]]
    style_terms = [profile.get("medium", ""), profile.get("palette", ""), profile.get("texture", "")]
    parts.extend([term for term in style_terms if term])
    parts.append(f"{shot['shot_size']}, {shot['angle']}, {shot['lens']}")
    if shot.get("foreground"):
        parts.append(shot["foreground"])
    if shot.get("composition"):
        parts.append(f"composition: {shot['composition']}")
    parts.append(f"lighting: {shot['lighting']}")
    parts.append(f"camera movement: {shot['camera_movement']}")
    return "; ".join([part for part in parts if part]).rstrip("; ") + "."


def format_anchors(shot: Dict[str, object], profile: Dict[str, object], language: str) -> str:
    anchors = list(shot.get("continuity_anchors", []))
    for tag in profile.get("prompt_tags", []):
        if tag not in anchors:
            anchors.append(tag)
    return "、".join(anchors) if language == "zh" else ", ".join(anchors)


def beat_range(beat: Dict[str, object]) -> str:
    return f"{beat['start']:g}-{beat['end']:g}s"


def zh_global_style(project: Dict[str, object]) -> str:
    profile = project.get("style_profile", {})
    parts = [
        profile.get("medium", ""),
        profile.get("palette", ""),
        profile.get("texture", ""),
        profile.get("lighting_bias", ""),
    ]
    tags = profile.get("prompt_tags", [])
    if tags:
        parts.append("、".join(tags))
    return "，".join([part for part in parts if part]).rstrip("，。") + "。"


def zh_scene_header(scene: Dict[str, object]) -> str:
    time_label = scene.get("time_range_label") or scene.get("scene_id", "")
    sequence_label = scene.get("sequence_label", "")
    title = scene.get("display_title") or scene.get("summary", "")
    if sequence_label and title:
        body = f"{sequence_label}：{title}"
    else:
        body = sequence_label or title
    return f"【{time_label}｜{body}】" if body else f"【{time_label}】"


def zh_shot_labels(shot: Dict[str, object]) -> str:
    custom_labels = shot.get("display_labels", [])
    if custom_labels:
        return "".join(f"[{label}]" for label in custom_labels[:2] if label)

    labels = [zh_term(shot["shot_size"])]
    angle = shot.get("angle")
    if angle and angle != "eye_level":
        labels.append(zh_term(angle))
    return "".join(f"[{label}]" for label in labels if label)


def zh_movement_phrase(shot: Dict[str, object]) -> str:
    movement = shot.get("camera_movement")
    if not movement:
        return ""
    movement_map = {
        "slow_push_in": "镜头缓慢推进",
        "follow": "镜头跟住动作",
        "locked_off": "镜头保持稳定",
        "lateral_track": "镜头轻轻横移",
        "orbit": "镜头轻微环绕",
        "dolly_in": "镜头向前推近",
        "dolly_out": "镜头缓缓后拉",
        "crane_up": "镜头向上升起",
        "crane_down": "镜头向下压低",
        "tilt": "镜头轻轻向上摇",
        "pan": "镜头轻轻转向",
        "whip_pan": "镜头快速甩摇",
        "rack_focus": "镜头做焦点切换",
        "handheld_subtle": "镜头保持轻微手持感",
        "handheld_urgent": "镜头急促手持跟进",
    }
    return movement_map.get(str(movement), f"镜头{zh_term(str(movement))}")


def zh_shot_sentence(shot: Dict[str, object], beat_description: str | None = None) -> str:
    parts = [shot["subject"], shot["setting"]]
    if beat_description:
        parts.append(beat_description)
    else:
        angle = shot.get("angle")
        lens = shot.get("lens")
        movement_phrase = zh_movement_phrase(shot)
        if angle:
            parts.append(f"{zh_term(angle)}视角")
        if lens:
            parts.append(f"{zh_term(lens)}")
        if movement_phrase:
            parts.append(movement_phrase)
        parts.append(shot["action"])
    if shot.get("foreground"):
        parts.append(shot["foreground"])
    if shot.get("lighting"):
        parts.append(f"光线{zh_csv_terms(shot['lighting'])}")
    return "，".join([part for part in parts if part]).rstrip("，。") + "。"


def zh_action_timing_line(shot: Dict[str, object]) -> str:
    timing = shot.get("action_timing_validation", {})
    if not timing:
        return ""
    parts = []
    if timing.get("primary_action_chain"):
        parts.append(f"主动作链：{timing['primary_action_chain']}")
    if timing.get("secondary_action_chain"):
        parts.append(f"次动作链：{timing['secondary_action_chain']}")
    if timing.get("available_seconds") is not None and timing.get("estimated_required_seconds") is not None:
        parts.append(
            f"可用时长：{float(timing['available_seconds']):.1f}s，预计所需：{float(timing['estimated_required_seconds']):.1f}s"
        )
    stage_parts = []
    for key, label in (
        ("setup_seconds", "准备"),
        ("execution_seconds", "执行"),
        ("result_seconds", "结果"),
        ("reaction_seconds", "反应"),
    ):
        value = timing.get(key)
        if isinstance(value, (int, float)) and float(value) > 0:
            stage_parts.append(f"{label}{float(value):.1f}s")
    if stage_parts:
        parts.append("动作预算：" + "，".join(stage_parts))
    if timing.get("timing_pressure"):
        parts.append(f"时长压力：{timing['timing_pressure']}")
    if timing.get("readability_verdict"):
        parts.append(f"可读性结论：{timing['readability_verdict']}")
    if timing.get("adjustment"):
        parts.append(f"调整建议：{timing['adjustment']}")
    return "；".join(parts)


def project_output_mode(project: Dict[str, object]) -> str:
    output_mode = str(project.get("output_mode") or "").strip()
    if output_mode in OUTPUT_MODES:
        return output_mode
    if project.get("prompt_language") == "zh":
        return "storyboard_script"
    return "final_prompt_only"


def render_zh_storyboard(plan: Dict[str, object], include_review: bool) -> str:
    project = plan["project"]
    audio_profile = project.get("audio_profile", {})
    out_lines: List[str] = []

    global_style = zh_global_style(project)
    if global_style and global_style != "。":
        out_lines.append("全局风格：")
        out_lines.append(global_style)
        out_lines.append("")

    for scene in plan["scenes"]:
        scene_profile = merge_profiles(project.get("style_profile", {}), scene.get("style_overrides", {}))
        out_lines.append(zh_scene_header(scene))
        shot_counter = 1
        for shot in scene["shots"]:
            effective_profile = merge_profiles(scene_profile, shot.get("style_overrides", {}))
            labels = zh_shot_labels(shot)
            beats = shot.get("timecoded_beats", [])
            if beats:
                for beat in beats:
                    out_lines.append(
                        f"镜头{shot_counter}：{beat_range(beat)} {labels} {zh_shot_sentence(shot, beat['description'])}"
                    )
                    shot_counter += 1
            else:
                out_lines.append(
                    f"镜头{shot_counter}：{labels} {zh_shot_sentence(shot)}"
                )
                shot_counter += 1
            if include_review:
                lighting_line = zh_lighting_line(shot, effective_profile)
                decision_line = zh_decision_line(shot)
                timing_line = zh_action_timing_line(shot)
                critique_line = zh_critique_line(shot)
                evaluation_line = zh_evaluation_line(shot)
                if lighting_line:
                    out_lines.append(f"灯光设计：{lighting_line}")
                if decision_line:
                    out_lines.append(f"导演决策：{decision_line}")
                if timing_line:
                    out_lines.append(f"动作时长校验：{timing_line}")
                if critique_line:
                    out_lines.append(f"批判校正：{critique_line}")
                if evaluation_line:
                    out_lines.append(f"评分：{evaluation_line}")

        scene_sound_line = zh_scene_sound_line(scene, audio_profile)
        if scene_sound_line:
            out_lines.append(f"音效：{scene_sound_line}")
        out_lines.append("")

    return "\n".join(out_lines).rstrip() + "\n"


def render_zh_prompt_only(plan: Dict[str, object]) -> str:
    project = plan["project"]
    audio_profile = project.get("audio_profile", {})
    out_lines: List[str] = []

    global_style = zh_global_style(project)
    if global_style and global_style != "。":
        out_lines.append("全局风格：")
        out_lines.append(global_style)
        out_lines.append("")

    for scene in plan["scenes"]:
        scene_profile = merge_profiles(project.get("style_profile", {}), scene.get("style_overrides", {}))
        out_lines.append(zh_scene_header(scene))
        for shot in scene["shots"]:
            effective_profile = merge_profiles(scene_profile, shot.get("style_overrides", {}))
            out_lines.append(zh_prompt(shot, effective_profile, shot.get("style_mode", project.get("style_mode", ""))))
        scene_sound_line = zh_scene_sound_line(scene, audio_profile)
        if scene_sound_line:
            out_lines.append(f"音效：{scene_sound_line}")
        out_lines.append("")

    return "\n".join(out_lines).rstrip() + "\n"


def render_block(
    shot: Dict[str, object],
    profile: Dict[str, object],
    audio_profile: Dict[str, object],
    language: str,
    mode: str,
) -> List[str]:
    visual_prompt = zh_prompt(shot, profile, mode) if language == "zh" else en_prompt(shot, profile, mode)
    sound_line = zh_sound_line(shot, audio_profile) if language == "zh" else en_sound_line(shot, audio_profile)
    lighting_line = zh_lighting_line(shot, profile) if language == "zh" else en_lighting_line(shot, profile)
    decision_line = zh_decision_line(shot) if language == "zh" else en_decision_line(shot)
    critique_line = zh_critique_line(shot) if language == "zh" else en_critique_line(shot)
    evaluation_line = zh_evaluation_line(shot) if language == "zh" else en_evaluation_line(shot)
    anchors = format_anchors(shot, profile, language)
    lines = [f"[{shot['shot_id']}]"]
    if language == "zh":
        lines.append("画面提示词：")
        lines.append(visual_prompt)
        if decision_line:
            lines.append("")
            lines.append("导演决策：")
            lines.append(decision_line)
        if lighting_line:
            lines.append("")
            lines.append("灯光设计：")
            lines.append(lighting_line)
        if critique_line:
            lines.append("")
            lines.append("批判校正：")
            lines.append(critique_line)
        if evaluation_line:
            lines.append("")
            lines.append("评分：")
            lines.append(evaluation_line)
        if shot.get("timecoded_beats"):
            lines.append("")
            lines.append("分段动作：")
            for beat in shot["timecoded_beats"]:
                lines.append(f"[{beat['start']:g}s-{beat['end']:g}s] {beat['description']}")
        if anchors:
            lines.append("")
            lines.append("一致性锚点：")
            lines.append(anchors)
        if sound_line:
            lines.append("")
            lines.append("声音提示：")
            lines.append(sound_line)
        if shot.get("negative"):
            lines.append("")
            lines.append("避免：")
            lines.append(shot["negative"])
    else:
        lines.append("Visual Prompt:")
        lines.append(visual_prompt)
        if decision_line:
            lines.append("")
            lines.append("Director Decision:")
            lines.append(decision_line)
        if lighting_line:
            lines.append("")
            lines.append("Lighting Design:")
            lines.append(lighting_line)
        if critique_line:
            lines.append("")
            lines.append("Critique-Correct-Verify:")
            lines.append(critique_line)
        if evaluation_line:
            lines.append("")
            lines.append("Evaluation:")
            lines.append(evaluation_line)
        if shot.get("timecoded_beats"):
            lines.append("")
            lines.append("Timed Beats:")
            for beat in shot["timecoded_beats"]:
                lines.append(f"[{beat['start']:g}s-{beat['end']:g}s] {beat['description']}")
        if anchors:
            lines.append("")
            lines.append("Consistency Anchors:")
            lines.append(anchors)
        if sound_line:
            lines.append("")
            lines.append("Sound Prompt:")
            lines.append(sound_line)
        if shot.get("negative"):
            lines.append("")
            lines.append("Avoid:")
            lines.append(shot["negative"])
    lines.append("")
    return lines


def render(plan: Dict[str, object]) -> str:
    project = plan["project"]
    language = project["prompt_language"]
    if language == "zh":
        output_mode = project_output_mode(project)
        if output_mode == "director_review":
            return render_zh_storyboard(plan, include_review=True)
        if output_mode == "final_prompt_only":
            return render_zh_prompt_only(plan)
        return render_zh_storyboard(plan, include_review=False)
    out_lines: List[str] = []
    audio_profile = project.get("audio_profile", {})

    for scene in plan["scenes"]:
        scene_profile = merge_profiles(project.get("style_profile", {}), scene.get("style_overrides", {}))
        out_lines.append(f"# {scene['scene_id']} {scene['summary']}")
        for shot in scene["shots"]:
            mode = shot.get("style_mode", project["style_mode"])
            effective_profile = merge_profiles(scene_profile, shot.get("style_overrides", {}))
            out_lines.extend(render_block(shot, effective_profile, audio_profile, language, mode))
    return "\n".join(out_lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render Seedance prompts from shot plan JSON.")
    parser.add_argument("--input", required=True, help="Path to shot plan JSON")
    parser.add_argument("--output", help="Optional output text file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = json.loads(Path(args.input).read_text())
    output = render(plan)
    if args.output:
        Path(args.output).write_text(output)
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
