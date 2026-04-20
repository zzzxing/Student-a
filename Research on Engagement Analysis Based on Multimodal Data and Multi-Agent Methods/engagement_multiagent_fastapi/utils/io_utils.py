from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def parse_json_bytes(raw_bytes: bytes) -> Any:
    text = raw_bytes.decode("utf-8").strip()
    if not text:
        raise ValueError("输入内容为空。")
    return json.loads(text)


def load_builtin_sample(path: Path) -> dict[str, Any]:
    data = read_json_file(path)
    if not isinstance(data, dict):
        raise ValueError("内置单样本数据格式不正确。")
    return data


def load_builtin_timeline(path: Path) -> list[dict[str, Any]]:
    data = read_json_file(path)
    samples = data["samples"] if isinstance(data, dict) and "samples" in data else data
    if not isinstance(samples, list):
        raise ValueError("内置时间序列数据格式不正确。")
    return samples
