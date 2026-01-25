"""
Tool Service
Business logic for tool registry operations
"""
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from app.core.database import tools_collection
from app.models.tool import (
    ToolCreate, ToolUpdate, ToolResponse, ToolListResponse,
    tool_to_doc, doc_to_tool, ToolCategory, ToolStatus, BUILTIN_TOOLS
)


class ToolService:
    """Service for tool registry operations"""
    
    async def initialize_builtin_tools(self):
        """Initialize built-in tools in the database"""
        for tool_data in BUILTIN_TOOLS:
            existing = await tools_collection().find_one({"name": tool_data["name"]})
            if not existing:
                tool_data["created_at"] = datetime.utcnow()
                tool_data["updated_at"] = datetime.utcnow()
                await tools_collection().insert_one(tool_data)
    
    async def create(self, tool: ToolCreate) -> ToolResponse:
        """Create a new custom tool"""
        # Check if tool name already exists
        existing = await tools_collection().find_one({"name": tool.name})
        if existing:
            raise ValueError(f"Tool with name '{tool.name}' already exists")
        
        doc = tool_to_doc(tool)
        result = await tools_collection().insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc_to_tool(doc)
    
    async def get_by_id(self, tool_id: str) -> Optional[ToolResponse]:
        """Get tool by ID"""
        try:
            doc = await tools_collection().find_one({"_id": ObjectId(tool_id)})
            if doc:
                return doc_to_tool(doc)
            return None
        except Exception:
            return None
    
    async def get_by_name(self, name: str) -> Optional[ToolResponse]:
        """Get tool by name"""
        doc = await tools_collection().find_one({"name": name})
        if doc:
            return doc_to_tool(doc)
        return None
    
    async def get_all(
        self,
        category: Optional[ToolCategory] = None,
        status: Optional[ToolStatus] = None,
        include_builtin: bool = True
    ) -> ToolListResponse:
        """Get all tools with filtering"""
        query = {}
        if category:
            query["category"] = category.value
        if status:
            query["status"] = status.value
        if not include_builtin:
            query["is_builtin"] = False
        
        total = await tools_collection().count_documents(query)
        cursor = tools_collection().find(query).sort("name", 1)
        
        tools = []
        async for doc in cursor:
            tools.append(doc_to_tool(doc))
        
        return ToolListResponse(tools=tools, total=total)
    
    async def get_builtin_tools(self) -> List[ToolResponse]:
        """Get all built-in tools"""
        cursor = tools_collection().find({"is_builtin": True})
        
        tools = []
        async for doc in cursor:
            tools.append(doc_to_tool(doc))
        
        return tools
    
    async def get_active_tools(self) -> List[ToolResponse]:
        """Get all active tools"""
        cursor = tools_collection().find({"status": ToolStatus.ACTIVE.value})
        
        tools = []
        async for doc in cursor:
            tools.append(doc_to_tool(doc))
        
        return tools
    
    async def update(self, tool_id: str, update: ToolUpdate) -> Optional[ToolResponse]:
        """Update a tool"""
        update_data = update.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_by_id(tool_id)
        
        update_data["updated_at"] = datetime.utcnow()
        
        # Convert enums
        if "category" in update_data and update_data["category"]:
            update_data["category"] = update_data["category"].value
        if "status" in update_data and update_data["status"]:
            update_data["status"] = update_data["status"].value
        
        # Convert schemas
        if "input_schema" in update_data and update_data["input_schema"]:
            update_data["input_schema"] = update_data["input_schema"].model_dump()
        if "output_schema" in update_data and update_data["output_schema"]:
            update_data["output_schema"] = update_data["output_schema"].model_dump()
        
        try:
            await tools_collection().update_one(
                {"_id": ObjectId(tool_id)},
                {"$set": update_data}
            )
            return await self.get_by_id(tool_id)
        except Exception:
            return None
    
    async def delete(self, tool_id: str) -> bool:
        """Delete a custom tool (built-in tools cannot be deleted)"""
        try:
            # Check if it's a built-in tool
            tool = await self.get_by_id(tool_id)
            if tool and tool.is_builtin:
                raise ValueError("Cannot delete built-in tools")
            
            result = await tools_collection().delete_one({"_id": ObjectId(tool_id)})
            return result.deleted_count > 0
        except Exception:
            return False
    
    async def get_by_names(self, names: List[str]) -> List[ToolResponse]:
        """Get multiple tools by their names"""
        cursor = tools_collection().find({"name": {"$in": names}})
        
        tools = []
        async for doc in cursor:
            tools.append(doc_to_tool(doc))
        
        return tools


# Global service instance
tool_service = ToolService()
