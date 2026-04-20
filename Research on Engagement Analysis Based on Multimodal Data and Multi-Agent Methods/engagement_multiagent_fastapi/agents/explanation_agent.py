from __future__ import annotations

from core.rules import LABEL_TEXT


class ExplanationAgent:
    """根据多模态证据生成规则版解释文本。"""

    def explain(self, evidence: dict) -> dict:
        # 中文注释：分别提取三种模态的证据文本，再拼接为正式说明
        label_text = LABEL_TEXT.get(evidence.get("pred_label"), evidence.get("pred_label"))
        vision_text = "；".join(evidence["vision"]["evidence"])
        audio_text = "；".join(evidence["audio"]["evidence"])
        text_text = "；".join(evidence["text"]["evidence"])
        summary = (
            f"样本在当前时间片被判定为{label_text}。"
            f"视觉方面：{vision_text}。"
            f"音频方面：{audio_text}。"
            f"文本方面：{text_text}。"
            f"综合来看，该结论与模型得分 {evidence['pred_score']} 基本一致。"
        )
        highlights = [
            *evidence["vision"]["evidence"],
            *evidence["audio"]["evidence"],
            *evidence["text"]["evidence"],
        ]
        return {"summary": summary, "highlights": highlights[:5]}

    def future_llm_explain(self, evidence: dict) -> str:
        # 中文注释：该接口预留给未来接入大模型生成更自然的解释文本
        return "Future interface reserved for LLM-based explanation."
