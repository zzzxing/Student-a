from __future__ import annotations

from core.rules import verify_modal_consistency


class VerificationAgent:
    """检查多模态证据是否一致，并给出可信度说明。"""

    def verify(self, evidence: dict) -> dict:
        # 中文注释：直接依据三个模态的规则级别进行一致性判断
        result = verify_modal_consistency(
            evidence["vision"]["level"],
            evidence["audio"]["level"],
            evidence["text"]["level"],
        )
        result["modal_levels"] = {
            "vision": evidence["vision"]["level"],
            "audio": evidence["audio"]["level"],
            "text": evidence["text"]["level"],
        }
        return result
