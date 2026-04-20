from __future__ import annotations

from core.rules import LABEL_TEXT


class ReportAgent:
    """汇总解释与校验结果，输出中性化反馈建议。"""

    def generate(self, evidence: dict, explanation: dict, verification: dict) -> dict:
        label_text = LABEL_TEXT.get(evidence.get("pred_label"), evidence.get("pred_label"))
        primary_feedback = self._primary_feedback(label_text, evidence, verification)
        secondary_feedback = self._secondary_feedback(label_text, evidence, verification)
        return {
            "teacher_feedback": primary_feedback,
            "student_feedback": secondary_feedback,
            "brief": f"当前样本判定为{label_text}，一致性结果为{verification['status']}。",
            "explanation_digest": explanation["summary"],
        }

    def _primary_feedback(self, label_text: str, evidence: dict, verification: dict) -> str:
        if evidence["pred_score"] < 0:
            return (
                f"反馈建议：当前样本表现为{label_text}，建议在后续观察中重点关注视线、姿态与互动信号的变化，"
                f"并结合相邻时间片综合判断状态是否持续。当前一致性结果为{verification['status']}。"
            )
        return (
            f"反馈建议：当前样本表现为{label_text}，说明该时间片整体状态较为积极，"
            f"建议继续结合连续时间片变化进行综合解读。当前一致性结果为{verification['status']}。"
        )

    def _secondary_feedback(self, label_text: str, evidence: dict, verification: dict) -> str:
        if evidence["pred_score"] < 0:
            return (
                f"结果说明：该时间片更接近{label_text}状态，建议从视觉注意、语音参与和文本表达三个维度继续观察，"
                f"若一致性结果为{verification['status']}，说明当前多模态信号存在一定波动。"
            )
        return (
            f"结果说明：该时间片处于{label_text}状态，当前多模态证据整体较为协调，"
            f"可作为后续趋势分析与连续状态判断的参考。"
        )
