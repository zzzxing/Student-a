# 系统架构说明

- `app.py`：路由与页面编排
- `core/contest_service.py`：竞赛分析核心（动态衰减、风险识别、报告生成）
- `core/pipeline.py`：原有多智能体样本分析链路
- `templates/`：竞赛页面
- `data/classroom_datasets.json`：3 组课堂演示数据

采用 FastAPI + Jinja2 + Chart.js，保持轻量演示与可解释输出。
