from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from core.contest_service import ContestService
from core.pipeline import EngagementPipeline
from core.schemas import SampleModel, TimelineRequestModel
from utils.io_utils import load_builtin_sample, load_builtin_timeline, parse_json_bytes

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="E-Focus 课堂专注度分析与可解释干预系统")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
pipeline = EngagementPipeline()
SAMPLE_PATH = BASE_DIR / "data" / "example_sample.json"
TIMELINE_PATH = BASE_DIR / "data" / "example_timeline.json"
CONTEST_DATA_PATH = BASE_DIR / "data" / "classroom_datasets.json"
contest_service = ContestService(CONTEST_DATA_PATH)
DEFAULT_DATASET = "normal_class"


def _default_sample() -> dict[str, Any]:
    return load_builtin_sample(SAMPLE_PATH)


def _default_timeline() -> list[dict[str, Any]]:
    return load_builtin_timeline(TIMELINE_PATH)


def _safe_sample_payload(raw_json: str | None, upload: UploadFile | None, builtin_name: str | None) -> dict[str, Any]:
    if raw_json and raw_json.strip():
        return parse_json_bytes(raw_json.encode("utf-8"))
    if upload and upload.filename:
        return parse_json_bytes(upload.file.read())
    if builtin_name in (None, "", "example_sample"):
        return _default_sample()
    raise ValueError("请提供 JSON 样本、上传文件，或选择内置样例。")


def _safe_timeline_payload(raw_json: str | None, upload: UploadFile | None, builtin_name: str | None) -> list[dict[str, Any]]:
    if raw_json and raw_json.strip():
        parsed = parse_json_bytes(raw_json.encode("utf-8"))
    elif upload and upload.filename:
        parsed = parse_json_bytes(upload.file.read())
    elif builtin_name in (None, "", "example_timeline"):
        parsed = _default_timeline()
    else:
        raise ValueError("请提供时间序列 JSON、上传文件，或选择内置样例。")
    return parsed["samples"] if isinstance(parsed, dict) and "samples" in parsed else parsed


def _contest_context(request: Request, active: str, dataset_id: str = DEFAULT_DATASET) -> dict[str, Any]:
    datasets = contest_service.datasets()
    selected = contest_service.get_dataset(dataset_id)
    return {
        "request": request,
        "active": active,
        "datasets": datasets,
        "selected_dataset": selected,
        "dataset_id": selected["dataset_id"],
    }


@app.get("/", response_class=HTMLResponse)
async def index() -> RedirectResponse:
    return RedirectResponse(url="/dashboard", status_code=303)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("login.html", {"request": request, "active": "login", "error": None})


@app.post("/login")
async def login_submit(username: str = Form(default="teacher"), password: str = Form(default="123456")) -> RedirectResponse:
    _ = (username, password)
    return RedirectResponse(url="/dashboard", status_code=303)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, dataset_id: str = DEFAULT_DATASET) -> HTMLResponse:
    analysis = contest_service.analyze_dataset(dataset_id)
    snapshot = contest_service.dashboard_snapshot(dataset_id)
    latest = analysis["frames"][-1] if analysis["frames"] else {}
    report = contest_service.generate_report(dataset_id)
    return templates.TemplateResponse(
        "dashboard.html",
        {
            **_contest_context(request, "dashboard", dataset_id),
            "snapshot": snapshot,
            "analysis": analysis,
            "latest": latest,
            "report": report,
            "recent_reports": [contest_service.generate_report(item["dataset_id"]) for item in contest_service.datasets()],
            "focus_labels": [f"片段{frame['time_block']}" for frame in analysis["frames"]],
            "focus_scores": [frame["avg_focus"] for frame in analysis["frames"]],
            "predict_scores": [frame["predicted_next_focus"] for frame in analysis["frames"]],
        },
    )


@app.get("/realtime", response_class=HTMLResponse)
async def realtime_page(request: Request, dataset_id: str = DEFAULT_DATASET) -> HTMLResponse:
    analysis = contest_service.analyze_dataset(dataset_id)
    return templates.TemplateResponse("realtime.html", {**_contest_context(request, "realtime", dataset_id), "analysis": analysis})


@app.get("/student/{student_id}", response_class=HTMLResponse)
async def student_page(request: Request, student_id: str, dataset_id: str = DEFAULT_DATASET) -> HTMLResponse:
    student = contest_service.student_timeline(dataset_id, student_id)
    return templates.TemplateResponse("student.html", {**_contest_context(request, "student", dataset_id), "student": student})


@app.get("/report", response_class=HTMLResponse)
async def report_page(request: Request, dataset_id: str = DEFAULT_DATASET) -> HTMLResponse:
    report = contest_service.generate_report(dataset_id)
    return templates.TemplateResponse("report.html", {**_contest_context(request, "report", dataset_id), "report": report})


@app.get("/data", response_class=HTMLResponse)
async def data_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "data.html",
        {
            "request": request,
            "active": "data",
            "datasets": contest_service.datasets(),
            "classes": contest_service.classes,
            "courses": contest_service.courses,
            "students": contest_service.students,
        },
    )


@app.post("/data/upload", response_class=HTMLResponse)
async def data_upload(request: Request, upload_file: UploadFile | None = File(default=None)) -> HTMLResponse:
    message = "未选择文件，当前仅展示内置演示数据。"
    if upload_file and upload_file.filename:
        try:
            _ = parse_json_bytes(upload_file.file.read())
            message = f"文件 {upload_file.filename} 解析成功（演示版未入库，仅校验结构）。"
        except Exception as exc:
            message = f"文件解析失败：{exc}"
    return templates.TemplateResponse(
        "data.html",
        {
            "request": request,
            "active": "data",
            "datasets": contest_service.datasets(),
            "classes": contest_service.classes,
            "courses": contest_service.courses,
            "students": contest_service.students,
            "upload_message": message,
        },
    )


@app.get("/demo", response_class=HTMLResponse)
async def demo_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("demo.html", {"request": request, "active": "demo"})


@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("about.html", {"request": request, "active": "about"})


@app.get("/analyze", response_class=HTMLResponse)
async def analyze_page(request: Request) -> HTMLResponse:
    sample = _default_sample()
    return templates.TemplateResponse(
        "analyze.html",
        {"request": request, "active": "analyze", "example_sample": sample, "initial_result": None, "error": None},
    )


@app.post("/api/analyze")
async def analyze_api(sample: SampleModel) -> JSONResponse:
    return JSONResponse(pipeline.analyze_sample(sample.model_dump()))


@app.post("/analyze/demo", response_class=HTMLResponse)
async def analyze_demo(
    request: Request,
    builtin_name: str = Form(default="example_sample"),
    raw_json: str = Form(default=""),
    upload_file: UploadFile | None = File(default=None),
) -> HTMLResponse:
    error = None
    try:
        sample = _safe_sample_payload(raw_json, upload_file, builtin_name)
        result = pipeline.analyze_sample(sample)
    except Exception as exc:
        sample = _default_sample()
        result = pipeline.analyze_sample(sample)
        error = f"输入解析失败，已回退到内置示例。{exc}"
    return templates.TemplateResponse(
        "analyze.html",
        {"request": request, "active": "analyze", "example_sample": sample, "initial_result": result, "error": error},
    )


@app.get("/timeline", response_class=HTMLResponse)
async def timeline_page(request: Request) -> HTMLResponse:
    timeline = _default_timeline()
    return templates.TemplateResponse(
        "timeline.html",
        {"request": request, "active": "timeline", "example_timeline": timeline, "timeline_result": None, "error": None},
    )


@app.post("/api/timeline")
async def timeline_api(payload: TimelineRequestModel) -> JSONResponse:
    samples = [item.model_dump() for item in payload.samples]
    return JSONResponse(pipeline.analyze_timeline(samples))


@app.post("/timeline/demo", response_class=HTMLResponse)
async def timeline_demo(
    request: Request,
    builtin_name: str = Form(default="example_timeline"),
    raw_json: str = Form(default=""),
    upload_file: UploadFile | None = File(default=None),
) -> HTMLResponse:
    error = None
    try:
        samples = _safe_timeline_payload(raw_json, upload_file, builtin_name)
        result = pipeline.analyze_timeline(samples)
    except Exception as exc:
        samples = _default_timeline()
        result = pipeline.analyze_timeline(samples)
        error = f"输入解析失败，已回退到内置示例。{exc}"
    return templates.TemplateResponse(
        "timeline.html",
        {"request": request, "active": "timeline", "example_timeline": samples, "timeline_result": result, "error": error},
    )


@app.get("/api/realtime/{dataset_id}")
async def realtime_api(dataset_id: str) -> JSONResponse:
    return JSONResponse(contest_service.analyze_dataset(dataset_id))


@app.get("/api/report/{dataset_id}")
async def report_api(dataset_id: str) -> JSONResponse:
    return JSONResponse(contest_service.generate_report(dataset_id))
