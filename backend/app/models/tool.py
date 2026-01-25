"""
Tool Models
Pydantic schemas for MongoDB tool registry documents
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from bson import ObjectId


# ========== Enums ==========

class ToolCategory(str, Enum):
    WEB = "web"
    RAG = "rag"
    FILE = "file"
    API = "api"
    DATA = "data"
    CUSTOM = "custom"


class ToolStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    DEPRECATED = "deprecated"


# ========== Pydantic Schemas ==========

class ToolParameter(BaseModel):
    """Schema for tool parameter definition"""
    name: str
    type: str  # string, integer, boolean, array, object
    description: Optional[str] = None
    required: bool = False
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None


class ToolInputSchema(BaseModel):
    """JSON Schema-like input definition for tools"""
    type: str = "object"
    properties: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)


class ToolOutputSchema(BaseModel):
    """JSON Schema-like output definition for tools"""
    type: str = "object"
    properties: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class ToolBase(BaseModel):
    """Base tool schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str
    category: ToolCategory = ToolCategory.CUSTOM
    input_schema: ToolInputSchema = Field(default_factory=ToolInputSchema)
    output_schema: Optional[ToolOutputSchema] = None
    config: Dict[str, Any] = Field(default_factory=dict)


class ToolCreate(ToolBase):
    """Schema for creating a custom tool"""
    handler_code: Optional[str] = None  # Optional Python code for custom tools


class ToolUpdate(BaseModel):
    """Schema for updating a tool"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[ToolCategory] = None
    input_schema: Optional[ToolInputSchema] = None
    output_schema: Optional[ToolOutputSchema] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[ToolStatus] = None


class ToolResponse(ToolBase):
    """Schema for tool responses"""
    id: str = Field(alias="_id")
    status: ToolStatus = ToolStatus.ACTIVE
    is_builtin: bool = False
    version: str = "1.0.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class ToolListResponse(BaseModel):
    """Tool list response"""
    tools: List[ToolResponse]
    total: int


# ========== Built-in Tool Definitions ==========

BUILTIN_TOOLS = [
    {
        "name": "web_search",
        "description": "Search the web using DuckDuckGo and return relevant results",
        "category": ToolCategory.WEB.value,
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Maximum number of results", "default": 5}
            },
            "required": ["query"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "results": {"type": "array", "items": {"type": "object"}}
            }
        },
        "is_builtin": True,
        "version": "1.0.0",
        "status": ToolStatus.ACTIVE.value
    },
    {
        "name": "rag_search",
        "description": "Search a vector database knowledge base for relevant documents",
        "category": ToolCategory.RAG.value,
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "knowledge_base_id": {"type": "string", "description": "ID of the knowledge base"},
                "top_k": {"type": "integer", "description": "Number of results to return", "default": 5}
            },
            "required": ["query", "knowledge_base_id"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "documents": {"type": "array", "items": {"type": "object"}}
            }
        },
        "is_builtin": True,
        "version": "1.0.0",
        "status": ToolStatus.ACTIVE.value
    },
    {
        "name": "file_reader",
        "description": "Read and parse file contents (supports text, CSV, JSON, PDF)",
        "category": ToolCategory.FILE.value,
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file"},
                "file_type": {"type": "string", "description": "Type of file (auto-detected if not specified)"}
            },
            "required": ["file_path"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "metadata": {"type": "object"}
            }
        },
        "is_builtin": True,
        "version": "1.0.0",
        "status": ToolStatus.ACTIVE.value
    },
    {
        "name": "api_caller",
        "description": "Make HTTP API calls to external services",
        "category": ToolCategory.API.value,
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "API endpoint URL"},
                "method": {"type": "string", "description": "HTTP method", "default": "GET"},
                "headers": {"type": "object", "description": "Request headers"},
                "body": {"type": "object", "description": "Request body for POST/PUT"},
                "params": {"type": "object", "description": "Query parameters"}
            },
            "required": ["url"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "status_code": {"type": "integer"},
                "response": {"type": "object"}
            }
        },
        "is_builtin": True,
        "version": "1.0.0",
        "status": ToolStatus.ACTIVE.value
    },
    {
        "name": "data_analyzer",
        "description": "Analyze data and generate insights from structured data",
        "category": ToolCategory.DATA.value,
        "input_schema": {
            "type": "object",
            "properties": {
                "data": {"type": "array", "description": "Data to analyze (array of objects)"},
                "analysis_type": {"type": "string", "description": "Type of analysis (summary, trends, correlations)"}
            },
            "required": ["data"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "insights": {"type": "array"},
                "statistics": {"type": "object"}
            }
        },
        "is_builtin": True,
        "version": "1.0.0",
        "status": ToolStatus.ACTIVE.value
    },
    {
        "name": "text_summarizer",
        "description": "Summarize long text into concise summaries",
        "category": ToolCategory.DATA.value,
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to summarize"},
                "max_length": {"type": "integer", "description": "Maximum summary length in words", "default": 200}
            },
            "required": ["text"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"}
            }
        },
        "is_builtin": True,
        "version": "1.0.0",
        "status": ToolStatus.ACTIVE.value
    }
]


# ========== MongoDB Document Helpers ==========

def tool_to_doc(tool: ToolCreate) -> Dict[str, Any]:
    """Convert ToolCreate to MongoDB document"""
    now = datetime.utcnow()
    
    return {
        "name": tool.name,
        "description": tool.description,
        "category": tool.category.value,
        "input_schema": tool.input_schema.model_dump(),
        "output_schema": tool.output_schema.model_dump() if tool.output_schema else None,
        "config": tool.config,
        "handler_code": getattr(tool, 'handler_code', None),
        "status": ToolStatus.ACTIVE.value,
        "is_builtin": False,
        "version": "1.0.0",
        "created_at": now,
        "updated_at": now
    }


def doc_to_tool(doc: Dict[str, Any]) -> ToolResponse:
    """Convert MongoDB document to ToolResponse"""
    doc["_id"] = str(doc["_id"])
    doc["category"] = ToolCategory(doc.get("category", "custom"))
    doc["status"] = ToolStatus(doc.get("status", "active"))
    
    # Convert schemas
    if doc.get("input_schema"):
        doc["input_schema"] = ToolInputSchema(**doc["input_schema"])
    if doc.get("output_schema"):
        doc["output_schema"] = ToolOutputSchema(**doc["output_schema"])
    
    return ToolResponse(**doc)
