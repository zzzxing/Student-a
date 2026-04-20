from __future__ import annotations


class ReviewAgent:
    """审核专家：评估样本质量、结论风险与复核优先级。"""

    def review(self, evidence: dict, verification: dict) -> dict:
        warnings: list[str] = []

        raw = evidence.get("raw", {})
        vision_raw = raw.get("vision", {})
        audio_raw = raw.get("audio", {})
        text_raw = raw.get("text", {})

        if vision_raw.get("gaze", "unknown") == "unknown" or vision_raw.get("head_pose", "unknown") == "unknown":
            warnings.append("视觉输入字段存在 unknown，建议复核采集或预处理流程。")

        if audio_raw.get("has_speech") is False:
            warnings.append("当前时间片未检测到语音，音频证据可能不足。")

        if text_raw.get("has_transcript") is False or text_raw.get("text_len", 0) < 10:
            warnings.append("文本转写偏少或缺失，文本证据可信度受限。")

        status = verification.get("status", "部分一致")
        risk_level = self._risk_level(status, len(warnings), float(evidence.get("pred_score", 0)))
        quality_score = self._quality_score(warnings, status)

        return {
            "risk_level": risk_level,
            "quality_score": quality_score,
            "review_status": "需人工复核" if risk_level in {"高", "中"} else "自动通过",
            "review_summary": self._summary(risk_level, status, quality_score),
            "warnings": warnings,
        }

    def _risk_level(self, status: str, warning_count: int, pred_score: float) -> str:
        if status == "冲突" or warning_count >= 3:
            return "高"
        if status == "部分一致" or warning_count >= 2:
            return "中"
        if pred_score < -0.1:
            return "中"
        return "低"

    def _quality_score(self, warnings: list[str], status: str) -> int:
        base = 100
        base -= min(len(warnings) * 12, 48)
        if status == "部分一致":
            base -= 10
        elif status == "冲突":
            base -= 24
        return max(base, 20)

    def _summary(self, risk_level: str, status: str, quality_score: int) -> str:
        return (
            f"审核专家判断当前样本风险等级为{risk_level}，"
            f"跨模态一致性为{status}，样本质量分为 {quality_score} 分。"
            "建议结合前后时间片进行复核，以提高结论稳定性。"
        )
