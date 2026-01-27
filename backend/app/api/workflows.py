"""
Workflow API Routes
CRUD operations and execution for workflows
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.models.workflow import (
    WorkflowCreate, WorkflowUpdate, WorkflowResponse, WorkflowListResponse, WorkflowStatus
)
from app.models.execution import ExecutionRequest, ExecutionDetailResponse, ExecutionStatus
from app.services.workflow_service import workflow_service
from app.services.agent_service import agent_service
from app.services.execution_service import execution_service, ExecutionContext
from app.engine.orchestrator import MultiAgentOrchestrator


router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.post("", response_model=WorkflowResponse, status_code=201)
async def create_workflow(workflow: WorkflowCreate):
    """Create a new workflow"""
    return await workflow_service.create(workflow)


@router.get("", response_model=WorkflowListResponse)
async def list_workflows(
    status: Optional[WorkflowStatus] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """List all workflows with pagination"""
    return await workflow_service.get_all(
        status=status,
        page=page,
        per_page=per_page
    )


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str):
    """Get workflow by ID"""
    workflow = await workflow_service.get_by_id(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(workflow_id: str, update: WorkflowUpdate):
    """Update a workflow"""
    workflow = await workflow_service.update(workflow_id, update)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow"""
    success = await workflow_service.delete(workflow_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"message": "Workflow deleted successfully"}


@router.post("/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, request: ExecutionRequest):
    """
    Execute a workflow (multi-agent orchestration).
    
    Returns detailed execution results including all agent outputs.
    """
    workflow = await workflow_service.get_by_id(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Create execution record
    execution = await execution_service.create_execution(
        workflow_id=workflow_id,
        input_data=request.input,
        trigger_type="manual"
    )
    
    context = ExecutionContext(execution.id)
    
    try:
        # Update status to running
        await execution_service.update_status(
            execution.id,
            ExecutionStatus.RUNNING
        )
        
        # Create orchestrator and execute
        orchestrator = MultiAgentOrchestrator(workflow, context)
        result = await orchestrator.execute(request.input)
        
        # Update status to results
        await execution_service.update_status(
            execution.id,
            ExecutionStatus.COMPLETED,
            output_data=result,
            token_usage=context.token_usage
        )
        
        # Save steps and logs
        await execution_service.save_context(execution.id, context)
        
        return await execution_service.get_detail(execution.id)
        
    except Exception as e:
        await execution_service.update_status(
            execution.id,
            ExecutionStatus.FAILED,
            error_message=str(e)
        )
        await execution_service.save_context(execution.id, context)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/activate")
async def activate_workflow(workflow_id: str):
    """Activate a workflow"""
    workflow = await workflow_service.activate(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"message": "Workflow activated", "workflow": workflow}


@router.post("/{workflow_id}/pause")
async def pause_workflow(workflow_id: str):
    """Pause a workflow"""
    workflow = await workflow_service.pause(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"message": "Workflow paused", "workflow": workflow}
