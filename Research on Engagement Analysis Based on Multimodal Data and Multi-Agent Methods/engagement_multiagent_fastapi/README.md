# 基于多模态数据与多智能体的专注度分析系统

这是一个适合毕业设计展示的原型系统，采用 **FastAPI + Jinja2 Templates + Bootstrap 5 + 本地 JSON + Python 多智能体类** 的轻量技术路线实现。

系统特点：

- 不接数据库，直接读取本地 JSON 样本数据
- 不依赖外部 API，方便本地演示与论文截图
- 将多模态证据处理封装为 4 个独立 Agent
- 支持单样本分析与时间序列分析
- 支持教师建议、学生建议、一致性校验与解释文本输出
- 预留未来扩展到 LLM 的接口

## 项目目录

```text
engagement_multiagent_fastapi/
├─ app.py
├─ requirements.txt
├─ README.md
├─ data/
│  ├─ example_sample.json
│  └─ example_timeline.json
├─ agents/
│  ├─ coordinator_agent.py
│  ├─ explanation_agent.py
│  ├─ verification_agent.py
│  ├─ report_agent.py
│  └─ review_agent.py
├─ core/
│  ├─ rules.py
│  ├─ schemas.py
│  └─ pipeline.py
├─ templates/
│  ├─ base.html
│  ├─ index.html
│  ├─ analyze.html
│  └─ timeline.html
├─ static/
│  ├─ css/
│  │  └─ style.css
│  └─ js/
│     └─ main.js
└─ utils/
   └─ io_utils.py
```

## 功能说明

### 1. 首页 `/`
- 展示系统标题、项目简介与功能概览
- 可跳转到样本分析页和时间序列分析页

### 2. 样本分析页 `/analyze`
- 支持内置示例、上传 JSON 文件、直接粘贴 JSON
- 展示样本编号、预测标签、得分、多模态解释、一致性结果、教师建议、学生建议

### 3. 时间序列分析页 `/timeline`
- 支持时间片序列输入
- 展示专注度折线图
- 展示平均分、最高/最低时间片
- 展示每个时间片的解释摘要与建议

### 4. API 接口
- `GET /`：首页 HTML
- `GET /analyze`：样本分析页 HTML
- `POST /api/analyze`：输入单个样本 JSON，返回分析结果 JSON
- `GET /timeline`：时间序列分析页 HTML
- `POST /api/timeline`：输入多个时间片样本，返回整体分析结果 JSON

## 规则版多智能体说明

### CoordinatorAgent
- 接收原始样本
- 整理为统一证据包 evidence

### ExplanationAgent
- 根据视觉、音频、文本证据生成正式解释文本
- 已预留 `future_llm_explain()` 接口，方便未来接入大模型

### VerificationAgent
- 对视觉、音频、文本证据进行跨模态一致性判断
- 输出：一致 / 部分一致 / 冲突、冲突点、可信度说明

### ReportAgent
- 汇总解释与校验结果
- 生成教师版和学生版反馈建议

### ReviewAgent（审核专家）
- 从输入完整性与跨模态一致性角度进行质量审查
- 输出风险等级、质量分、审核状态与风险提示

## 运行方式

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动项目

```bash
uvicorn app:app --reload
```

### 3. 打开浏览器

访问：

```text
http://127.0.0.1:8000
```

## 示例数据说明

### 单样本数据
文件：`data/example_sample.json`

适合演示单一时间片的规则分析结果。

### 时间序列数据
文件：`data/example_timeline.json`

适合演示一个视频样本在多个时间片上的专注度变化情况。

## 后续可扩展方向

- 接入真实多模态识别模型输出
- 增加更细粒度的规则设计
- 将 `future_llm_explain()` 替换为大模型解释模块
- 增加导出报告、批量分析、班级统计等功能
