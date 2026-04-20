from __future__ import annotations

from agents.coordinator_agent import CoordinatorAgent
from agents.explanation_agent import ExplanationAgent
from agents.report_agent import ReportAgent
from agents.review_agent import ReviewAgent
from agents.verification_agent import VerificationAgent
from core.rules import LABEL_TEXT


class EngagementPipeline:
    def __init__(self) -> None:
        self.coordinator = CoordinatorAgent()
        self.explainer = ExplanationAgent()
        self.verifier = VerificationAgent()
        self.reporter = ReportAgent()
        self.reviewer = ReviewAgent()

    def analyze_sample(self, sample: dict) -> dict:
        evidence = self.coordinator.prepare(sample)
        explanation = self.explainer.explain(evidence)
        verification = self.verifier.verify(evidence)
        report = self.reporter.generate(evidence, explanation, verification)
        review = self.reviewer.review(evidence, verification)
        pred_label = sample.get("pred_label", "DE")
        return {
            "sample_id": sample.get("sample_id", "sample_demo"),
            "time_block": sample.get("time_block", 1),
            "pred_label": pred_label,
            "pred_label_text": LABEL_TEXT.get(pred_label, pred_label),
            "pred_score": sample.get("pred_score", 0),
            "evidence": evidence,
            "explanation": explanation,
            "verification": verification,
            "report": report,
            "review": review,
        }

    def analyze_timeline(self, samples: list[dict]) -> dict:
        results = [self.analyze_sample(sample) for sample in samples] if samples else []
        avg_score = round(sum(item["pred_score"] for item in results) / len(results), 3) if results else 0
        score_series = [item["pred_score"] for item in results]
        labels = [item["time_block"] for item in results]
        summary = {
            "total_blocks": len(results),
            "average_score": avg_score,
            "highest_block": max(results, key=lambda x: x["pred_score"], default=None),
            "lowest_block": min(results, key=lambda x: x["pred_score"], default=None),
            "consistency_overview": self._consistency_overview(results),
            "timeline_comment": self._timeline_comment(avg_score, score_series),
        }
        return {"summary": summary, "chart": {"labels": labels, "scores": score_series}, "results": results}

    def _consistency_overview(self, results: list[dict]) -> dict:
        counter = {"一致": 0, "部分一致": 0, "冲突": 0}
        for item in results:
            status = item.get("verification", {}).get("status", "部分一致")
            counter[status] = counter.get(status, 0) + 1
        return counter

    def _timeline_comment(self, avg_score: float, scores: list[float]) -> str:
        if not scores:
            return "暂无时间序列数据。"
        trend = "整体较稳定"
        if len(scores) >= 2 and scores[-1] > scores[0]:
            trend = "后期专注度呈上升趋势"
        elif len(scores) >= 2 and scores[-1] < scores[0]:
            trend = "后期专注度呈下降趋势"
        if avg_score >= 0.4:
            return f"该样本平均专注水平较好，{trend}。"
        if avg_score >= -0.1:
            return f"该样本整体处于中等专注水平，{trend}。"
        return f"该样本整体专注水平偏低，{trend}。"
