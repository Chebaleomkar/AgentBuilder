"""
Workflow Service
Business logic for workflow CRUD operations
"""
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from app.core.database import workflows_collection
from app.models.workflow import (
    WorkflowCreate, WorkflowUpdate, WorkflowResponse, WorkflowListResponse,
    workflow_to_doc, doc_to_workflow, WorkflowStatus
)


class WorkflowService:
    """Service for workflow operations"""
    
    async def create(
        self,
        workflow: WorkflowCreate,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> WorkflowResponse:
        """Create a new workflow"""
        doc = workflow_to_doc(workflow, user_id, project_id)
        result = await workflows_collection().insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc_to_workflow(doc)
    
    async def get_by_id(self, workflow_id: str) -> Optional[WorkflowResponse]:
        """Get workflow by ID"""
        try:
            doc = await workflows_collection().find_one({"_id": ObjectId(workflow_id)})
            if doc:
                return doc_to_workflow(doc)
            return None
        except Exception:
            return None
    
    async def get_all(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        page: int = 1,
        per_page: int = 20
    ) -> WorkflowListResponse:
        """Get all workflows with filtering and pagination"""
        query = {}
        if user_id:
            query["user_id"] = user_id
        if project_id:
            query["project_id"] = project_id
        if status:
            query["status"] = status.value
        
        total = await workflows_collection().count_documents(query)
        
        skip = (page - 1) * per_page
        cursor = workflows_collection().find(query).skip(skip).limit(per_page).sort("created_at", -1)
        
        workflows = []
        async for doc in cursor:
            workflows.append(doc_to_workflow(doc))
        
        return WorkflowListResponse(
            workflows=workflows,
            total=total,
            page=page,
            per_page=per_page
        )
    
    async def update(self, workflow_id: str, update: WorkflowUpdate) -> Optional[WorkflowResponse]:
        """Update a workflow"""
        update_data = update.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_by_id(workflow_id)
        
        update_data["updated_at"] = datetime.utcnow()
        
        # Convert enums to values
        if "coordination_strategy" in update_data and update_data["coordination_strategy"]:
            update_data["coordination_strategy"] = update_data["coordination_strategy"].value
        if "execution_mode" in update_data and update_data["execution_mode"]:
            update_data["execution_mode"] = update_data["execution_mode"].value
        if "status" in update_data and update_data["status"]:
            update_data["status"] = update_data["status"].value
        
        # Convert steps to dicts
        if "steps" in update_data and update_data["steps"]:
            update_data["steps"] = [step.model_dump() for step in update_data["steps"]]
        
        try:
            await workflows_collection().update_one(
                {"_id": ObjectId(workflow_id)},
                {"$set": update_data}
            )
            return await self.get_by_id(workflow_id)
        except Exception:
            return None
    
    async def delete(self, workflow_id: str) -> bool:
        """Delete a workflow"""
        try:
            result = await workflows_collection().delete_one({"_id": ObjectId(workflow_id)})
            return result.deleted_count > 0
        except Exception:
            return False
    
    async def set_status(self, workflow_id: str, status: WorkflowStatus) -> Optional[WorkflowResponse]:
        """Update workflow status"""
        return await self.update(workflow_id, WorkflowUpdate(status=status))
    
    async def activate(self, workflow_id: str) -> Optional[WorkflowResponse]:
        """Activate a workflow"""
        return await self.set_status(workflow_id, WorkflowStatus.ACTIVE)
    
    async def pause(self, workflow_id: str) -> Optional[WorkflowResponse]:
        """Pause a workflow"""
        return await self.set_status(workflow_id, WorkflowStatus.PAUSED)


# Global service instance
workflow_service = WorkflowService()
