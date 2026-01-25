"""
Execution Models
Pydantic schemas for MongoDB execution tracking and logs
"""
from datetime import datetime
from typing import Optional, List, Any, Dict
from enum import Enum
from pydantic import BaseModel, Field
from bson import ObjectId
import uuid


# ========== Enums ==========

class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


# ========== Pydantic Schemas ==========

class TokenUsage(BaseModel):
    """Token usage tracking"""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class ToolCall(BaseModel):
    """Represents a single tool call during execution"""
    tool_name: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    duration_ms: int = 0
    success: bool = True
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExecutionStep(BaseModel):
    """Schema for an execution step"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    step_name: str
    step_type: str  # agent, tool, condition, etc.
    agent_id: Optional[str] = None
    tool_name: Optional[str] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    status: StepStatus = StepStatus.PENDING
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    sequence_number: int = 0
    tool_calls: List[ToolCall] = Field(default_factory=list)


class ExecutionLog(BaseModel):
    """Schema for an execution log entry"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    level: LogLevel = LogLevel.INFO
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source: Optional[str] = None  # agent, tool, system
    step_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExecutionRequest(BaseModel):
    """Request to execute an agent or workflow"""
    input: Dict[str, Any] = Field(default_factory=dict)
    config: Dict[str, Any] = Field(default_factory=dict)


class ExecutionBase(BaseModel):
    """Base execution schema"""
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)


class ExecutionResponse(BaseModel):
    """Schema for execution responses"""
    id: str = Field(alias="_id")
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    cost_estimate: Optional[float] = None
    retry_count: int = 0
    trigger_type: str = "manual"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class ExecutionDetailResponse(ExecutionResponse):
    """Detailed execution response with steps and logs"""
    steps: List[ExecutionStep] = Field(default_factory=list)
    logs: List[ExecutionLog] = Field(default_factory=list)


class ExecutionListResponse(BaseModel):
    """Paginated execution list response"""
    executions: List[ExecutionResponse]
    total: int
    page: int
    per_page: int


# ========== MongoDB Document Helpers ==========

def execution_to_doc(
    agent_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    input_data: Dict[str, Any] = None,
    trigger_type: str = "manual",
    triggered_by: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new execution document"""
    now = datetime.utcnow()
    
    return {
        "agent_id": agent_id,
        "workflow_id": workflow_id,
        "status": ExecutionStatus.PENDING.value,
        "input_data": input_data or {},
        "output_data": None,
        "error_message": None,
        "started_at": None,
        "completed_at": None,
        "duration_ms": None,
        "token_usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
        "cost_estimate": None,
        "retry_count": 0,
        "trigger_type": trigger_type,
        "triggered_by": triggered_by,
        "created_at": now
    }


def doc_to_execution(doc: Dict[str, Any]) -> ExecutionResponse:
    """Convert MongoDB document to ExecutionResponse"""
    doc["_id"] = str(doc["_id"])
    doc["status"] = ExecutionStatus(doc.get("status", "pending"))
    
    # Handle token_usage
    token_usage = doc.get("token_usage", {})
    doc["token_usage"] = TokenUsage(**token_usage) if isinstance(token_usage, dict) else TokenUsage()
    
    return ExecutionResponse(**doc)


def execution_step_to_doc(step: ExecutionStep, execution_id: str) -> Dict[str, Any]:
    """Convert ExecutionStep to MongoDB document"""
    return {
        "id": step.id,
        "execution_id": execution_id,
        "step_name": step.step_name,
        "step_type": step.step_type,
        "agent_id": step.agent_id,
        "tool_name": step.tool_name,
        "input_data": step.input_data,
        "output_data": step.output_data,
        "status": step.status.value,
        "error_message": step.error_message,
        "started_at": step.started_at,
        "completed_at": step.completed_at,
        "duration_ms": step.duration_ms,
        "sequence_number": step.sequence_number,
        "tool_calls": [tc.model_dump() for tc in step.tool_calls]
    }


def doc_to_execution_step(doc: Dict[str, Any]) -> ExecutionStep:
    """Convert MongoDB document to ExecutionStep"""
    doc["status"] = StepStatus(doc.get("status", "pending"))
    
    # Convert tool_calls
    tool_calls = []
    for tc in doc.get("tool_calls", []):
        tool_calls.append(ToolCall(**tc))
    doc["tool_calls"] = tool_calls
    
    return ExecutionStep(**doc)


def execution_log_to_doc(log: ExecutionLog, execution_id: str) -> Dict[str, Any]:
    """Convert ExecutionLog to MongoDB document"""
    return {
        "id": log.id,
        "execution_id": execution_id,
        "level": log.level.value,
        "message": log.message,
        "metadata": log.metadata,
        "source": log.source,
        "step_id": log.step_id,
        "timestamp": log.timestamp
    }


def doc_to_execution_log(doc: Dict[str, Any]) -> ExecutionLog:
    """Convert MongoDB document to ExecutionLog"""
    doc["level"] = LogLevel(doc.get("level", "info"))
    return ExecutionLog(**doc)
