from __future__ import annotations

LABEL_TEXT = {
    "HD": "高度专注",
    "DE": "轻度分心",
    "EG": "积极参与",
    "HE": "高效投入",
}


def score_to_level(score: float) -> str:
    if score >= 0.6:
        return "high"
    if score >= 0:
        return "medium"
    return "low"


def analyze_vision(vision: dict) -> dict:
    evidence = []
    level = "medium"
    if vision.get("gaze") == "look_away" and vision.get("head_pose") == "head_down":
        evidence.append("视线偏离且低头，表现出低专注视觉特征")
        level = "low"
    if vision.get("gaze") == "focus_forward" and vision.get("head_pose") == "stable":
        evidence.append("视线面向前方且头部稳定，表现出较高专注")
        level = "high"
    if vision.get("au_summary") == "active_expression":
        evidence.append("面部表情活跃，反映出较高参与度")
        if level != "low":
            level = "high"
    if not evidence:
        evidence.append("视觉证据较为一般，未出现显著高低专注特征")
    return {"level": level, "evidence": evidence}


def analyze_audio(audio: dict) -> dict:
    evidence = []
    level = "medium"
    if audio.get("has_speech") is False:
        evidence.append("当前时间片没有检测到明显发言，语音参与偏弱")
    if audio.get("volume_level") == "high" and audio.get("pitch_change") == "moderate":
        evidence.append("音量较高且语调有变化，语音参与较积极")
        level = "high"
    elif audio.get("volume_level") == "low" and audio.get("pitch_change") == "small":
        evidence.append("音量较低且语调变化小，语音参与较弱")
        level = "low"
    if not evidence:
        evidence.append("音频证据中未观察到明显的积极或消极参与信号")
    return {"level": level, "evidence": evidence}


def analyze_text(text: dict) -> dict:
    evidence = []
    level = "medium"
    summary = (text.get("summary") or "").strip()
    if text.get("has_transcript") is False or text.get("text_len", 0) < 10:
        evidence.append("文本转写缺失或文本长度较短，文本证据偏弱")
        level = "low"
    if text.get("text_len", 0) >= 20 and summary:
        evidence.append("文本长度较长且摘要明确，语言参与较强")
        level = "high"
    if not evidence:
        evidence.append("文本信息有限，暂未体现明显语言参与强度")
    return {"level": level, "evidence": evidence}


def verify_modal_consistency(vision_level: str, audio_level: str, text_level: str) -> dict:
    if vision_level == "low" and audio_level == "low" and text_level == "low":
        return {
            "status": "一致",
            "conflicts": [],
            "credibility": "三模态同时指向低参与状态，当前判断可信度较高。",
        }
    if vision_level == "low" and audio_level == "high":
        return {
            "status": "部分一致",
            "conflicts": ["视觉呈现低专注，但音频表现出较积极参与。"],
            "credibility": "不同模态关注的行为维度不同，建议结合上下文进一步核验。",
        }
    if vision_level == "high" and audio_level == "low" and text_level == "low":
        return {
            "status": "部分一致",
            "conflicts": ["视觉较专注，但音频与文本证据偏弱，整体证据不充分。"],
            "credibility": "视觉模态较强，但缺少其他模态支撑，因此结论需谨慎解释。",
        }
    levels = {vision_level, audio_level, text_level}
    if len(levels) == 1:
        return {
            "status": "一致",
            "conflicts": [],
            "credibility": "三类模态整体趋势相近，判断具有较好稳定性。",
        }
    return {
        "status": "冲突",
        "conflicts": ["视觉、音频、文本给出的参与线索存在差异。"],
        "credibility": "当前样本存在跨模态冲突，建议结合更多时间片综合判断。",
    }
