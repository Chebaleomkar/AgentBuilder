"""
Execution Logs API Routes
Execution history and observability
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.models.execution import (
    ExecutionResponse, ExecutionDetailResponse, ExecutionListResponse, ExecutionStatus
)
from app.services.execution_service import execution_service


router = APIRouter(prefix="/executions", tags=["Executions"])


@router.get("", response_model=ExecutionListResponse)
async def list_executions(
    agent_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    status: Optional[ExecutionStatus] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """List all executions with filtering and pagination"""
    return await execution_service.get_all(
        agent_id=agent_id,
        workflow_id=workflow_id,
        status=status,
        page=page,
        per_page=per_page
    )


@router.get("/{execution_id}", response_model=ExecutionDetailResponse)
async def get_execution(execution_id: str):
    """Get execution details including steps and logs"""
    execution = await execution_service.get_detail(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


@router.get("/{execution_id}/summary", response_model=ExecutionResponse)
async def get_execution_summary(execution_id: str):
    """Get execution summary (without steps and logs)"""
    execution = await execution_service.get_by_id(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


@router.post("/{execution_id}/cancel")
async def cancel_execution(execution_id: str):
    """Cancel a running execution"""
    execution = await execution_service.get_by_id(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if execution.status not in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel execution with status: {execution.status}"
        )
    
    await execution_service.update_status(
        execution_id,
        ExecutionStatus.CANCELLED
    )
    
    return {"message": "Execution cancelled"}


@router.get("/{execution_id}/logs")
async def get_execution_logs(
    execution_id: str,
    level: Optional[str] = None
):
    """Get execution logs"""
    execution = await execution_service.get_detail(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    logs = execution.logs
    if level:
        logs = [log for log in logs if log.level.value == level]
    
    return {"logs": logs, "count": len(logs)}


@router.get("/{execution_id}/steps")
async def get_execution_steps(execution_id: str):
    """Get execution steps"""
    execution = await execution_service.get_detail(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return {"steps": execution.steps, "count": len(execution.steps)}


@router.get("/{execution_id}/tool-calls")
async def get_execution_tool_calls(execution_id: str):
    """Get all tool calls from an execution"""
    execution = await execution_service.get_detail(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    tool_calls = []
    for step in execution.steps:
        for tc in step.tool_calls:
            tool_calls.append({
                "step_name": step.step_name,
                "tool_call": tc
            })
    
    return {"tool_calls": tool_calls, "count": len(tool_calls)}
