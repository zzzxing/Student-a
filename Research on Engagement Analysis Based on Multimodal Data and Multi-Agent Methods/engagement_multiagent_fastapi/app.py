from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from core.pipeline import EngagementPipeline
from core.schemas import SampleModel, TimelineRequestModel
from utils.io_utils import load_builtin_sample, load_builtin_timeline, parse_json_bytes

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="基于多模态数据与多智能体的专注度分析系统")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
pipeline = EngagementPipeline()
SAMPLE_PATH = BASE_DIR / "data" / "example_sample.json"
TIMELINE_PATH = BASE_DIR / "data" / "example_timeline.json"


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


def _index_context(request: Request) -> dict[str, Any]:
    sample = _default_sample()
    timeline = _default_timeline()
    sample_result = pipeline.analyze_sample(sample)
    timeline_result = pipeline.analyze_timeline(timeline)
    return {
        "request": request,
        "active": "index",
        "sample_preview": sample_result,
        "timeline_preview": timeline_result,
    }


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", _index_context(request))


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
