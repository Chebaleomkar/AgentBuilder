"""
Agent Models
Pydantic schemas for MongoDB agent documents
"""
from datetime import datetime
from typing import Optional, List, Any, Dict
from enum import Enum
from pydantic import BaseModel, Field
from bson import ObjectId


# ========== Custom Types ==========

class PyObjectId(str):
    """Custom ObjectId type for Pydantic"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str):
            return v
        raise ValueError("Invalid ObjectId")


# ========== Enums ==========

class AgentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    RUNNING = "running"
    ERROR = "error"


class MemoryType(str, Enum):
    SESSION = "session"  # Per-run memory
    PERSISTENT = "persistent"  # Per-agent persistent memory
    KNOWLEDGE = "knowledge"  # Vector-store backed


# ========== Pydantic Schemas ==========

class ToolReference(BaseModel):
    """Reference to a tool in the registry"""
    id: str
    name: str
    config: Optional[Dict[str, Any]] = None


class MemoryConfig(BaseModel):
    """Memory configuration for an agent"""
    type: MemoryType = MemoryType.SESSION
    ttl_seconds: Optional[int] = None
    max_turns: int = 50
    knowledge_base_id: Optional[str] = None


class AgentBase(BaseModel):
    """Base agent schema"""
    name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., min_length=1, max_length=255)
    goal: Optional[str] = None
    instructions: Optional[str] = None
    model: str = "gpt-4"
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    tools: List[str] = Field(default_factory=list)
    memory_type: MemoryType = MemoryType.SESSION
    memory_config: Optional[MemoryConfig] = None


class AgentCreate(AgentBase):
    """Schema for creating an agent"""
    pass


class AgentUpdate(BaseModel):
    """Schema for updating an agent"""
    name: Optional[str] = None
    role: Optional[str] = None
    goal: Optional[str] = None
    instructions: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    tools: Optional[List[str]] = None
    memory_type: Optional[MemoryType] = None
    memory_config: Optional[MemoryConfig] = None
    status: Optional[AgentStatus] = None


class AgentResponse(AgentBase):
    """Schema for agent responses"""
    id: str = Field(alias="_id")
    status: AgentStatus = AgentStatus.ACTIVE
    system_prompt: Optional[str] = None
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class AgentListResponse(BaseModel):
    """Paginated agent list response"""
    agents: List[AgentResponse]
    total: int
    page: int
    per_page: int


# ========== MongoDB Document Helpers ==========

def agent_to_doc(agent: AgentCreate, user_id: Optional[str] = None, project_id: Optional[str] = None) -> Dict[str, Any]:
    """Convert AgentCreate to MongoDB document"""
    now = datetime.utcnow()
    
    # Build system prompt from instructions/goal
    system_prompt = agent.instructions or agent.goal or f"You are {agent.role}."
    
    return {
        "name": agent.name,
        "role": agent.role,
        "goal": agent.goal,
        "instructions": agent.instructions,
        "model": agent.model,
        "temperature": agent.temperature,
        "tools": agent.tools,
        "memory_type": agent.memory_type.value,
        "memory_config": agent.memory_config.model_dump() if agent.memory_config else None,
        "system_prompt": system_prompt,
        "status": AgentStatus.ACTIVE.value,
        "user_id": user_id,
        "project_id": project_id,
        "created_at": now,
        "updated_at": now
    }


def doc_to_agent(doc: Dict[str, Any]) -> AgentResponse:
    """Convert MongoDB document to AgentResponse"""
    doc["_id"] = str(doc["_id"])
    doc["status"] = AgentStatus(doc.get("status", "active"))
    doc["memory_type"] = MemoryType(doc.get("memory_type", "session"))
    return AgentResponse(**doc)


# ========== Framework Mapping ==========

def to_framework_config(agent: AgentResponse) -> Dict[str, Any]:
    """Convert AgentBuilder config to agenticaiframework Agent config"""
    return {
        "name": agent.name,
        "role": agent.role,
        "capabilities": agent.tools,
        "config": {
            "model": agent.model,
            "temperature": agent.temperature,
            "system_prompt": agent.system_prompt or agent.instructions or agent.goal or f"You are {agent.role}.",
        }
    }
