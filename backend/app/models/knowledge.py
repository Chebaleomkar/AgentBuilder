from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
import uuid

class KnowledgeSourceType(str, Enum):
    FILE = "file"
    URL = "url"
    TEXT = "text"

class KnowledgeSource(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: KnowledgeSourceType
    content: Optional[str] = None
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    size_bytes: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class KnowledgeBase(BaseModel):
    id: str = Field(alias="_id")
    agent_id: str
    sources: List[KnowledgeSource] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class TextSourceCreate(BaseModel):
    name: str
    content: str
