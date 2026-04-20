from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

LabelType = Literal["HD", "DE", "EG", "HE"]


class VisionModel(BaseModel):
    gaze: str = Field(default="unknown")
    head_pose: str = Field(default="unknown")
    au_summary: str = Field(default="unknown")


class AudioModel(BaseModel):
    has_speech: bool = False
    volume_level: str = Field(default="unknown")
    pitch_change: str = Field(default="unknown")


class TextModel(BaseModel):
    has_transcript: bool = False
    text_len: int = 0
    summary: str = ""


class SampleModel(BaseModel):
    sample_id: str
    time_block: int = 1
    pred_label: LabelType
    pred_score: float
    vision: VisionModel
    audio: AudioModel
    text: TextModel


class TimelineRequestModel(BaseModel):
    samples: list[SampleModel]
