from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional
import os
import uuid
import shutil

from app.services.knowledge_service import knowledge_service, UPLOAD_DIR
from app.services.rag_service import rag_service
from app.models.knowledge import KnowledgeBase, KnowledgeSource, KnowledgeSourceType, TextSourceCreate

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])

@router.get("/{agent_id}", response_model=KnowledgeBase)
async def get_knowledge_base(agent_id: str):
    """Get the knowledge base for an agent"""
    return await knowledge_service.get_by_agent_id(agent_id)

@router.post("/{agent_id}/upload")
async def upload_file(
    agent_id: str,
    file: UploadFile = File(...),
    name: Optional[str] = Form(None)
):
    """Upload a file to the agent's knowledge base"""
    file_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    safe_filename = f"{agent_id}_{file_id}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    # Save the file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Extract text content for preview and vector search
    content = await rag_service.extract_text(file_path, file.content_type)
    
    source = KnowledgeSource(
        id=file_id,
        name=name or file.filename,
        type=KnowledgeSourceType.FILE,
        file_path=file_path,
        file_type=file.content_type,
        size_bytes=os.path.getsize(file_path),
        content=content # Store content in DB for preview
    )
    
    await knowledge_service.add_source(agent_id, source)
    return {"message": "File uploaded successfully", "source": source}

@router.get("/{agent_id}/{source_id}/content")
async def get_source_content(agent_id: str, source_id: str):
    """Retrieve the full content of a specific knowledge source"""
    content = await knowledge_service.get_source_content(agent_id, source_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return {"content": content}

@router.post("/{agent_id}/text")
async def add_text_source(
    agent_id: str,
    data: TextSourceCreate
):
    """Add a text snippet to the agent's knowledge base"""
    source = KnowledgeSource(
        name=data.name,
        type=KnowledgeSourceType.TEXT,
        content=data.content
    )
    await knowledge_service.add_source(agent_id, source)
    return {"message": "Text source added successfully", "source": source}

@router.delete("/{agent_id}/{source_id}")
async def delete_source(agent_id: str, source_id: str):
    """Remove a source from the knowledge base"""
    return await knowledge_service.remove_source(agent_id, source_id)
