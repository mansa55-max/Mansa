from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AvatarOut(BaseModel):
    avatar_id: str
    name: Optional[str] = None
    preview_image_url: Optional[str] = None
    default_voice_id: Optional[str] = None


class VoiceOut(BaseModel):
    voice_id: str
    name: Optional[str] = None
    language: Optional[str] = None
    gender: Optional[str] = None
    preview_audio_url: Optional[str] = None


class GenerateScriptRequest(BaseModel):
    product_name: str
    product_description: str


class GenerateScriptResponse(BaseModel):
    script: str


class CreateAdRequest(BaseModel):
    product_name: str
    script_text: str
    avatar_id: str
    voice_id: str
    aspect: str = "vertical"
    captions_enabled: bool = True


class AdOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_name: str
    script_text: str
    avatar_id: str
    avatar_name: Optional[str] = None
    voice_id: str
    voice_name: Optional[str] = None
    aspect: str
    captions_enabled: bool
    status: str
    error: Optional[str] = None
    video_available: bool = False
    created_at: datetime


class AdListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_name: str
    aspect: str
    status: str
    video_available: bool = False
    created_at: datetime
