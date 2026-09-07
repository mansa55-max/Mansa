import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, Text

from .database import Base


class AdStatus(str, enum.Enum):
    pending = "pending"
    generating = "generating"
    downloading = "downloading"
    captioning = "captioning"
    done = "done"
    error = "error"


class Ad(Base):
    __tablename__ = "ads"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, nullable=False)
    script_text = Column(Text, nullable=False)
    avatar_id = Column(String, nullable=False)
    avatar_name = Column(String, nullable=True)
    voice_id = Column(String, nullable=False)
    voice_name = Column(String, nullable=True)
    aspect = Column(String, nullable=False, default="vertical")
    captions_enabled = Column(Boolean, nullable=False, default=True)
    status = Column(Enum(AdStatus), default=AdStatus.pending, nullable=False)
    error = Column(Text, nullable=True)
    heygen_video_id = Column(String, nullable=True)
    video_filename = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def video_available(self) -> bool:
        return bool(self.video_filename)
