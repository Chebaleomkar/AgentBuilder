"""
Agent Service
Business logic for agent CRUD operations
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from app.core.database import agents_collection
from app.models.agent import (
    AgentCreate, AgentUpdate, AgentResponse, AgentListResponse,
    agent_to_doc, doc_to_agent, AgentStatus
)


class AgentService:
    """Service for agent operations"""
    
    async def create(
        self,
        agent: AgentCreate,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> AgentResponse:
        """Create a new agent"""
        doc = agent_to_doc(agent, user_id, project_id)
        result = await agents_collection().insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc_to_agent(doc)
    
    async def get_by_id(self, agent_id: str) -> Optional[AgentResponse]:
        """Get agent by ID"""
        try:
            doc = await agents_collection().find_one({"_id": ObjectId(agent_id)})
            if doc:
                return doc_to_agent(doc)
            return None
        except Exception:
            return None
    
    async def get_all(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        status: Optional[AgentStatus] = None,
        page: int = 1,
        per_page: int = 20
    ) -> AgentListResponse:
        """Get all agents with filtering and pagination"""
        # Build query
        query = {}
        if user_id:
            query["user_id"] = user_id
        if project_id:
            query["project_id"] = project_id
        if status:
            query["status"] = status.value
        
        # Get total count
        total = await agents_collection().count_documents(query)
        
        # Get paginated results
        skip = (page - 1) * per_page
        cursor = agents_collection().find(query).skip(skip).limit(per_page).sort("created_at", -1)
        
        agents = []
        async for doc in cursor:
            agents.append(doc_to_agent(doc))
        
        return AgentListResponse(
            agents=agents,
            total=total,
            page=page,
            per_page=per_page
        )
    
    async def update(self, agent_id: str, update: AgentUpdate) -> Optional[AgentResponse]:
        """Update an agent"""
        update_data = update.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_by_id(agent_id)
        
        update_data["updated_at"] = datetime.utcnow()
        
        # Convert enums to values
        if "memory_type" in update_data and update_data["memory_type"]:
            update_data["memory_type"] = update_data["memory_type"].value
        if "status" in update_data and update_data["status"]:
            update_data["status"] = update_data["status"].value
        
        try:
            await agents_collection().update_one(
                {"_id": ObjectId(agent_id)},
                {"$set": update_data}
            )
            return await self.get_by_id(agent_id)
        except Exception:
            return None
    
    async def delete(self, agent_id: str) -> bool:
        """Delete an agent"""
        try:
            result = await agents_collection().delete_one({"_id": ObjectId(agent_id)})
            return result.deleted_count > 0
        except Exception:
            return False
    
    async def set_status(self, agent_id: str, status: AgentStatus) -> Optional[AgentResponse]:
        """Update agent status"""
        return await self.update(agent_id, AgentUpdate(status=status))
    
    async def get_by_ids(self, agent_ids: List[str]) -> List[AgentResponse]:
        """Get multiple agents by their IDs"""
        try:
            object_ids = [ObjectId(aid) for aid in agent_ids]
            cursor = agents_collection().find({"_id": {"$in": object_ids}})
            
            agents = []
            async for doc in cursor:
                agents.append(doc_to_agent(doc))
            
            return agents
        except Exception:
            return []
    
    async def search(self, query: str, user_id: Optional[str] = None) -> List[AgentResponse]:
        """Search agents by name or role"""
        search_query = {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"role": {"$regex": query, "$options": "i"}}
            ]
        }
        if user_id:
            search_query["user_id"] = user_id
        
        cursor = agents_collection().find(search_query).limit(20)
        
        agents = []
        async for doc in cursor:
            agents.append(doc_to_agent(doc))
        
        return agents


# Global service instance
agent_service = AgentService()
