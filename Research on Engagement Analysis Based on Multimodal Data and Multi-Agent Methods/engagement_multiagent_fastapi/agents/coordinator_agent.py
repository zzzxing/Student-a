from __future__ import annotations

from copy import deepcopy

from core.rules import analyze_audio, analyze_text, analyze_vision, score_to_level


class CoordinatorAgent:
    """负责整理输入样本，生成统一证据包。"""

    def prepare(self, sample: dict) -> dict:
        # 中文注释：复制原始样本，避免后续 agent 修改源数据
        sample_copy = deepcopy(sample)
        vision_result = analyze_vision(sample_copy.get("vision", {}))
        audio_result = analyze_audio(sample_copy.get("audio", {}))
        text_result = analyze_text(sample_copy.get("text", {}))
        evidence = {
            "sample_id": sample_copy.get("sample_id"),
            "time_block": sample_copy.get("time_block", 1),
            "pred_label": sample_copy.get("pred_label"),
            "pred_score": sample_copy.get("pred_score", 0.0),
            "score_level": score_to_level(sample_copy.get("pred_score", 0.0)),
            "raw": sample_copy,
            "vision": vision_result,
            "audio": audio_result,
            "text": text_result,
        }
        return evidence
