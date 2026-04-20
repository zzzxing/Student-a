from __future__ import annotations

import math
from pathlib import Path
from statistics import mean
from typing import Any

from utils.io_utils import parse_json_bytes


class ContestService:
    """Competition-oriented classroom engagement analysis service."""

    def __init__(self, data_path: Path) -> None:
        self.data_path = data_path
        self._payload = self._load_data()

    def _load_data(self) -> dict[str, Any]:
        raw = self.data_path.read_bytes()
        parsed = parse_json_bytes(raw)
        if not isinstance(parsed, dict):
            raise ValueError("classroom_datasets.json 格式错误")
        return parsed

    @property
    def classes(self) -> list[dict[str, Any]]:
        return self._payload.get("classes", [])

    @property
    def courses(self) -> list[dict[str, Any]]:
        return self._payload.get("courses", [])

    @property
    def students(self) -> list[dict[str, Any]]:
        return self._payload.get("students", [])

    def datasets(self) -> list[dict[str, Any]]:
        return self._payload.get("datasets", [])

    def get_dataset(self, dataset_id: str) -> dict[str, Any]:
        for item in self.datasets():
            if item.get("dataset_id") == dataset_id:
                return item
        return self.datasets()[0]

    def dashboard_snapshot(self, dataset_id: str) -> dict[str, Any]:
        analysis = self.analyze_dataset(dataset_id)
        latest = analysis["frames"][-1] if analysis["frames"] else {}
        return {
            "dataset_id": dataset_id,
            "class_id": analysis["class_id"],
            "course_id": analysis["course_id"],
            "avg_focus": round(analysis["avg_focus"], 2),
            "risk_students": len(analysis["risk_students"]),
            "low_phase_count": len([p for p in analysis["phase_summary"] if p["avg_focus"] < 60]),
            "best_intervention": latest.get("recommended_action", "维持当前教学节奏"),
        }

    def analyze_dataset(self, dataset_id: str) -> dict[str, Any]:
        dataset = self.get_dataset(dataset_id)
        students_meta = {item["student_id"]: item for item in self.students}
        frames: list[dict[str, Any]] = []
        student_focus_history: dict[str, list[float]] = {}

        for idx, frame in enumerate(dataset.get("frames", []), start=1):
            student_rows = []
            class_focus_scores = []
            for student in frame.get("students", []):
                focus, factors = self._score_student(student, frame.get("phase", "lecture"))
                class_focus_scores.append(focus)
                student_focus_history.setdefault(student["student_id"], []).append(focus)
                student_rows.append(
                    {
                        **student,
                        "focus_score": round(focus, 2),
                        "focus_state": self._focus_state(focus),
                        "explanation_factors": factors,
                        "student_name": students_meta.get(student["student_id"], {}).get("name", student["student_id"]),
                    }
                )

            avg_focus = mean(class_focus_scores) if class_focus_scores else 0
            trend_state = "稳定"
            if len(frames) >= 1:
                prev = frames[-1]["avg_focus"]
                if avg_focus - prev >= 2.0:
                    trend_state = "上升"
                elif prev - avg_focus >= 2.0:
                    trend_state = "下滑"

            recommended_action = self._recommended_action(avg_focus, frame.get("phase", "lecture"), trend_state)
            frames.append(
                {
                    "time_block": idx,
                    "timestamp": frame.get("timestamp", f"T{idx}"),
                    "phase": frame.get("phase", "lecture"),
                    "avg_focus": round(avg_focus, 2),
                    "trend_state": trend_state,
                    "intervention_needed": avg_focus < 63 or trend_state == "下滑",
                    "recommended_action": recommended_action,
                    "students": student_rows,
                }
            )

        risk_students = self._risk_students(student_focus_history, students_meta)
        phase_summary = self._phase_summary(frames)
        return {
            "dataset_id": dataset["dataset_id"],
            "dataset_name": dataset.get("name", dataset["dataset_id"]),
            "class_id": dataset.get("class_id"),
            "course_id": dataset.get("course_id"),
            "frames": frames,
            "avg_focus": mean([f["avg_focus"] for f in frames]) if frames else 0,
            "risk_students": risk_students,
            "phase_summary": phase_summary,
        }

    def student_timeline(self, dataset_id: str, student_id: str) -> dict[str, Any]:
        analyzed = self.analyze_dataset(dataset_id)
        series = []
        for frame in analyzed["frames"]:
            for student in frame["students"]:
                if student["student_id"] == student_id:
                    series.append(
                        {
                            "time_block": frame["time_block"],
                            "phase": frame["phase"],
                            "focus_score": student["focus_score"],
                            "focus_state": student["focus_state"],
                            "factors": student["explanation_factors"],
                        }
                    )
                    break

        if not series:
            return {"student_id": student_id, "series": []}

        min_idx = min(range(len(series)), key=lambda i: series[i]["focus_score"])
        max_idx = max(range(len(series)), key=lambda i: series[i]["focus_score"])
        return {
            "student_id": student_id,
            "student_name": next((s["student_name"] for s in analyzed["frames"][0]["students"] if s["student_id"] == student_id), student_id),
            "dataset_name": analyzed["dataset_name"],
            "series": series,
            "avg_focus": round(mean(item["focus_score"] for item in series), 2),
            "events": [
                {"label": "低谷", "time_block": series[min_idx]["time_block"], "value": series[min_idx]["focus_score"]},
                {"label": "峰值", "time_block": series[max_idx]["time_block"], "value": series[max_idx]["focus_score"]},
            ],
            "recommendation": self._student_recommendation(series),
        }

    def generate_report(self, dataset_id: str) -> dict[str, Any]:
        analyzed = self.analyze_dataset(dataset_id)
        low_frames = [f for f in analyzed["frames"] if f["avg_focus"] < 60]
        top_risk = analyzed["risk_students"][:3]
        return {
            "dataset_name": analyzed["dataset_name"],
            "class_id": analyzed["class_id"],
            "course_id": analyzed["course_id"],
            "avg_focus": round(analyzed["avg_focus"], 2),
            "phase_summary": analyzed["phase_summary"],
            "low_frames": low_frames,
            "risk_students": top_risk,
            "teacher_advice": self._teacher_advice(analyzed["avg_focus"], len(low_frames)),
            "student_advice": "建议在课堂中段增加互动问答，并对连续低迷学生进行轻量点名引导。",
            "narrative": self._narrative(analyzed, low_frames, top_risk),
        }

    def _score_student(self, student: dict[str, Any], phase: str) -> tuple[float, dict[str, float]]:
        posture = max(0.0, min(1.0, float(student.get("posture_score", 0))))
        face = max(0.0, min(1.0, float(student.get("face_orientation_score", 0))))
        interaction = max(0.0, min(1.0, float(student.get("interaction_score", 0))))
        speech = max(0.0, min(1.0, float(student.get("speech_activity_score", 0))))
        distraction_duration = max(0.0, float(student.get("distraction_duration", 0)))
        recent_gap = max(0.0, float(student.get("recent_engagement_gap", 0)))

        phase_factor = 1.0
        if phase == "review":
            phase_factor = 1.04
        elif phase == "lecture":
            phase_factor = 0.98

        base_focus = 100 * (0.32 * posture + 0.28 * face + 0.24 * interaction + 0.16 * speech)
        decay = math.exp(-0.08 * distraction_duration)
        focus_t = base_focus * decay * phase_factor + max(0, 8 - recent_gap)
        focus_t = max(0, min(100, focus_t))

        factors = {
            "姿态变化": round(posture * 45, 1),
            "互动活跃度": round(interaction * 25, 1),
            "持续低头时长": round(max(0, 20 - distraction_duration * 2), 1),
            "音频活跃度": round(speech * 10, 1),
        }
        return focus_t, factors

    def _focus_state(self, score: float) -> str:
        if score >= 75:
            return "专注"
        if score >= 55:
            return "波动"
        return "分神"

    def _recommended_action(self, avg_focus: float, phase: str, trend_state: str) -> str:
        if avg_focus < 55:
            return "立即发起快速提问并点名互动"
        if trend_state == "下滑":
            return "插入案例讨论，打断认知衰减"
        if phase == "lecture":
            return "每 8 分钟增加一次互动投票"
        return "维持节奏并关注边缘学生"

    def _risk_students(self, history: dict[str, list[float]], students_meta: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        ranked = []
        for student_id, scores in history.items():
            avg = mean(scores)
            volatility = max(scores) - min(scores) if scores else 0
            risk = 100 - avg + volatility * 0.6
            ranked.append(
                {
                    "student_id": student_id,
                    "student_name": students_meta.get(student_id, {}).get("name", student_id),
                    "avg_focus": round(avg, 2),
                    "volatility": round(volatility, 2),
                    "risk_index": round(risk, 2),
                }
            )
        return sorted(ranked, key=lambda x: x["risk_index"], reverse=True)

    def _phase_summary(self, frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
        bucket: dict[str, list[float]] = {}
        for frame in frames:
            bucket.setdefault(frame["phase"], []).append(frame["avg_focus"])
        return [{"phase": phase, "avg_focus": round(mean(scores), 2), "count": len(scores)} for phase, scores in bucket.items()]

    def _student_recommendation(self, series: list[dict[str, Any]]) -> str:
        avg = mean(item["focus_score"] for item in series)
        if avg < 55:
            return "建议课前预习+课堂短反馈循环，优先减少长时分神。"
        if avg < 70:
            return "建议在讲授阶段增加主动记录与举手互动频次。"
        return "当前状态较好，建议保持互动并承担课堂示例任务。"

    def _teacher_advice(self, avg_focus: float, low_frame_count: int) -> list[str]:
        advice = ["每 10 分钟安排一次 30 秒互动提问，防止认知衰减。"]
        if avg_focus < 60:
            advice.append("建议将长讲授切分为‘讲解-提问-反馈’微循环。")
        if low_frame_count >= 2:
            advice.append("在低谷时段插入案例或投票，提升群体注意力。")
        return advice

    def _narrative(self, analyzed: dict[str, Any], low_frames: list[dict[str, Any]], top_risk: list[dict[str, Any]]) -> str:
        low_desc = "、".join([f"第{f['time_block']}片段" for f in low_frames]) if low_frames else "无明显低谷"
        risk_desc = "、".join([item["student_name"] for item in top_risk]) if top_risk else "暂无"
        return (
            f"本次课堂（{analyzed['dataset_name']}）整体平均专注度为 {analyzed['avg_focus']:.1f} 分。"
            f"其中重点波动时段为 {low_desc}；建议教师在该区间实施快速提问或案例切换。"
            f"重点关注学生包括：{risk_desc}。"
        )
