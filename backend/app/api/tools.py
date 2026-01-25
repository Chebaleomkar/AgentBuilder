"""
Tool API Routes
Tool registry operations
"""
from typing import Optional
from fastapi import APIRouter, HTTPException
from app.models.tool import (
    ToolCreate, ToolUpdate, ToolResponse, ToolListResponse, ToolCategory, ToolStatus
)
from app.services.tool_service import tool_service


router = APIRouter(prefix="/tools", tags=["Tools"])


@router.get("", response_model=ToolListResponse)
async def list_tools(
    category: Optional[ToolCategory] = None,
    status: Optional[ToolStatus] = None,
    include_builtin: bool = True
):
    """List all tools"""
    return await tool_service.get_all(
        category=category,
        status=status,
        include_builtin=include_builtin
    )


@router.get("/builtin")
async def list_builtin_tools():
    """List all built-in tools"""
    tools = await tool_service.get_builtin_tools()
    return {"tools": tools, "count": len(tools)}


@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool(tool_id: str):
    """Get tool by ID"""
    tool = await tool_service.get_by_id(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool


@router.get("/name/{name}", response_model=ToolResponse)
async def get_tool_by_name(name: str):
    """Get tool by name"""
    tool = await tool_service.get_by_name(name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool


@router.post("", response_model=ToolResponse, status_code=201)
async def create_tool(tool: ToolCreate):
    """Create a new custom tool"""
    try:
        return await tool_service.create(tool)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{tool_id}", response_model=ToolResponse)
async def update_tool(tool_id: str, update: ToolUpdate):
    """Update a tool"""
    tool = await tool_service.update(tool_id, update)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool


@router.delete("/{tool_id}")
async def delete_tool(tool_id: str):
    """Delete a custom tool (built-in tools cannot be deleted)"""
    try:
        success = await tool_service.delete(tool_id)
        if not success:
            raise HTTPException(status_code=404, detail="Tool not found")
        return {"message": "Tool deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
