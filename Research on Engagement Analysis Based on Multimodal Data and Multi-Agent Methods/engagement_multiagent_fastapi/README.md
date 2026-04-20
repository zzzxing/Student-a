# E-Focus：课堂动态专注度分析与可解释干预系统

本项目在原有“多模态 + 多智能体”原型基础上，升级为竞赛导向 MVP，覆盖课堂分析闭环：

> 课堂行为数据输入 → 多模态专注度分析 → 动态衰减预测 → AI 干预建议 → 课后可解释报告

## 功能页
- `/login` 登录页
- `/dashboard` 教师端仪表盘
- `/classes` 班级列表页
- `/courses` 课程列表页
- `/realtime` 课堂实时分析页
- `/student/{student_id}` 单学生分析页
- `/report` 报告生成页
- `/data` 数据管理页
- `/demo` 竞赛演示模式页
- `/about` 关于项目页

兼容保留：`/analyze`、`/timeline` 原型页面。

## 数据与模型
- 演示数据：`data/classroom_datasets.json`（正常课堂 / 中段下滑 / 干预回升）
- 动态衰减示意：

```python
focus_t = base_focus * exp(-lambda_ * disengagement_minutes) + interaction_boost
```

- 可解释因素：姿态变化、互动活跃度、持续低头时长、音频活跃度。

## 启动
```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

访问：`http://127.0.0.1:8000/login`

## 文档
- `docs/prd/product_spec.md`
- `docs/architecture/system_architecture.md`
- `docs/api/api_spec.md`
- `docs/contest/innovation_points.md`
- `docs/contest/demo_script.md`
- `docs/contest/answering_outline.md`
