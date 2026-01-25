"""
Workflow Models
Pydantic schemas for MongoDB workflow documents
"""
from datetime import datetime
from typing import Optional, List, Any, Dict
from enum import Enum
from pydantic import BaseModel, Field
from bson import ObjectId
import uuid


# ========== Enums ==========

class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class ExecutionMode(str, Enum):
    ON_DEMAND = "on_demand"
    SCHEDULED = "scheduled"
    WEBHOOK = "webhook"


class CoordinationStrategy(str, Enum):
    SEQUENTIAL = "sequential"  # Execute agents in order
    SUPERVISOR = "supervisor"  # One agent coordinates others
    PEER = "peer"  # Agents collaborate as peers
    CONDITIONAL = "conditional"  # Branch based on conditions


class StepType(str, Enum):
    AGENT = "agent"  # Execute an agent
    CONDITION = "condition"  # Evaluate a condition
    PARALLEL = "parallel"  # Execute multiple steps in parallel
    LOOP = "loop"  # Loop over items
    HANDOFF = "handoff"  # Hand off to another agent


# ========== Pydantic Schemas ==========

class WorkflowStep(BaseModel):
    """A single step in a workflow"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: StepType
    agent_id: Optional[str] = None  # For AGENT and HANDOFF types
    condition: Optional[str] = None  # For CONDITION type (expression)
    config: Dict[str, Any] = Field(default_factory=dict)
    next_steps: List[str] = Field(default_factory=list)  # IDs of next steps
    on_success: Optional[str] = None  # Step ID on success
    on_failure: Optional[str] = None  # Step ID on failure


class WorkflowBase(BaseModel):
    """Base workflow schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    coordination_strategy: CoordinationStrategy = CoordinationStrategy.SEQUENTIAL
    execution_mode: ExecutionMode = ExecutionMode.ON_DEMAND
    steps: List[WorkflowStep] = Field(default_factory=list)
    agents: List[str] = Field(default_factory=list)  # Agent IDs
    config: Dict[str, Any] = Field(default_factory=dict)


class WorkflowCreate(WorkflowBase):
    """Schema for creating a workflow"""
    schedule_cron: Optional[str] = None


class WorkflowUpdate(BaseModel):
    """Schema for updating a workflow"""
    name: Optional[str] = None
    description: Optional[str] = None
    coordination_strategy: Optional[CoordinationStrategy] = None
    execution_mode: Optional[ExecutionMode] = None
    steps: Optional[List[WorkflowStep]] = None
    agents: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[WorkflowStatus] = None
    schedule_cron: Optional[str] = None


class WorkflowResponse(WorkflowBase):
    """Schema for workflow responses"""
    id: str = Field(alias="_id")
    status: WorkflowStatus = WorkflowStatus.DRAFT
    schedule_cron: Optional[str] = None
    next_run_at: Optional[datetime] = None
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class WorkflowListResponse(BaseModel):
    """Paginated workflow list response"""
    workflows: List[WorkflowResponse]
    total: int
    page: int
    per_page: int


# ========== Multi-Agent Orchestration Config ==========

class AgentTeamConfig(BaseModel):
    """Configuration for a team of agents"""
    name: str
    agents: List[str]  # Agent IDs
    coordination_strategy: CoordinationStrategy
    supervisor_agent_id: Optional[str] = None  # For supervisor strategy
    shared_context: Dict[str, Any] = Field(default_factory=dict)


# ========== MongoDB Document Helpers ==========

def workflow_to_doc(workflow: WorkflowCreate, user_id: Optional[str] = None, project_id: Optional[str] = None) -> Dict[str, Any]:
    """Convert WorkflowCreate to MongoDB document"""
    now = datetime.utcnow()
    
    return {
        "name": workflow.name,
        "description": workflow.description,
        "coordination_strategy": workflow.coordination_strategy.value,
        "execution_mode": workflow.execution_mode.value,
        "steps": [step.model_dump() for step in workflow.steps],
        "agents": workflow.agents,
        "config": workflow.config,
        "status": WorkflowStatus.DRAFT.value,
        "schedule_cron": workflow.schedule_cron,
        "next_run_at": None,
        "user_id": user_id,
        "project_id": project_id,
        "created_at": now,
        "updated_at": now
    }


def doc_to_workflow(doc: Dict[str, Any]) -> WorkflowResponse:
    """Convert MongoDB document to WorkflowResponse"""
    doc["_id"] = str(doc["_id"])
    doc["status"] = WorkflowStatus(doc.get("status", "draft"))
    doc["coordination_strategy"] = CoordinationStrategy(doc.get("coordination_strategy", "sequential"))
    doc["execution_mode"] = ExecutionMode(doc.get("execution_mode", "on_demand"))
    
    # Convert step dicts to WorkflowStep objects
    steps = []
    for step in doc.get("steps", []):
        step["type"] = StepType(step.get("type", "agent"))
        steps.append(WorkflowStep(**step))
    doc["steps"] = steps
    
    return WorkflowResponse(**doc)


def to_framework_team_config(workflow: WorkflowResponse, agents: List[Any]) -> Dict[str, Any]:
    """Convert WorkflowBuilder config to agenticaiframework AgentTeam config"""
    return {
        "name": workflow.name,
        "agents": agents,
        "coordination_strategy": workflow.coordination_strategy.value
    }
