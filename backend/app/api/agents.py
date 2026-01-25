"""
Agent API Routes
CRUD operations and execution for agents
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from app.models.agent import (
    AgentCreate, AgentUpdate, AgentResponse, AgentListResponse, AgentStatus
)
from app.models.execution import ExecutionRequest, ExecutionDetailResponse
from app.services.agent_service import agent_service
from app.services.execution_service import execution_service


router = APIRouter(prefix="/agents", tags=["Agents"])


@router.post("", response_model=AgentResponse, status_code=201)
async def create_agent(agent: AgentCreate):
    """Create a new agent"""
    return await agent_service.create(agent)


@router.get("", response_model=AgentListResponse)
async def list_agents(
    status: Optional[AgentStatus] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """List all agents with pagination"""
    return await agent_service.get_all(
        status=status,
        page=page,
        per_page=per_page
    )


@router.get("/search")
async def search_agents(q: str = Query(..., min_length=1)):
    """Search agents by name or role"""
    agents = await agent_service.search(q)
    return {"agents": agents, "count": len(agents)}


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get agent by ID"""
    agent = await agent_service.get_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, update: AgentUpdate):
    """Update an agent"""
    agent = await agent_service.update(agent_id, update)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent"""
    success = await agent_service.delete(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"message": "Agent deleted successfully"}


@router.post("/{agent_id}/execute", response_model=ExecutionDetailResponse)
async def execute_agent(agent_id: str, request: ExecutionRequest):
    """
    Execute an agent with the given input.
    
    Returns detailed execution results including steps and logs.
    """
    agent = await agent_service.get_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    try:
        result = await execution_service.execute_agent(
            agent_id=agent_id,
            input_data=request.input,
            trigger_type="manual"
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/execute/async")
async def execute_agent_async(
    agent_id: str,
    request: ExecutionRequest,
    background_tasks: BackgroundTasks
):
    """
    Execute an agent asynchronously.
    
    Returns execution ID immediately, use /executions/{id} to check status.
    """
    agent = await agent_service.get_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Create execution record
    execution = await execution_service.create_execution(
        agent_id=agent_id,
        input_data=request.input,
        trigger_type="manual"
    )
    
    # Queue execution in background
    background_tasks.add_task(
        execution_service.execute_agent,
        agent_id=agent_id,
        input_data=request.input,
        trigger_type="manual"
    )
    
    return {
        "execution_id": execution.id,
        "status": "pending",
        "message": "Execution started in background"
    }


@router.patch("/{agent_id}/status")
async def update_agent_status(agent_id: str, status: AgentStatus):
    """Update agent status"""
    agent = await agent_service.set_status(agent_id, status)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent
