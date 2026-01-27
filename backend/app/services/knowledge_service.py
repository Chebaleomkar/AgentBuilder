from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
import os
import uuid

from app.core.database import knowledge_collection
from app.models.knowledge import KnowledgeBase, KnowledgeSource, KnowledgeSourceType
from app.services.rag_service import rag_service

UPLOAD_DIR = "data/knowledge"

class KnowledgeService:
    """Service for managing agent knowledge bases"""

    def __init__(self):
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR, exist_ok=True)

    async def get_by_agent_id(self, agent_id: str) -> Optional[KnowledgeBase]:
        """Get or create knowledge base for an agent"""
        doc = await knowledge_collection().find_one({"agent_id": agent_id})
        if not doc:
            # Create a new one
            doc = {
                "agent_id": agent_id,
                "sources": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            result = await knowledge_collection().insert_one(doc)
            doc["_id"] = result.inserted_id
        
        doc["_id"] = str(doc["_id"])
        return KnowledgeBase(**doc)

    async def add_source(self, agent_id: str, source: KnowledgeSource) -> KnowledgeBase:
        """Add a source to the agent's knowledge base and index in Pinecone"""
        await knowledge_collection().update_one(
            {"agent_id": agent_id},
            {
                "$push": {"sources": source.model_dump()},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        # Index in Pinecone for semantic search
        if source.content:
            await rag_service.index_document(
                agent_id=agent_id,
                source_id=source.id,
                text=source.content,
                metadata={
                    "name": source.name,
                    "type": source.type.value
                }
            )
        
        return await self.get_by_agent_id(agent_id)

    async def remove_source(self, agent_id: str, source_id: str) -> KnowledgeBase:
        """Remove a source from the knowledge base and Pinecone"""
        await knowledge_collection().update_one(
            {"agent_id": agent_id},
            {
                "$pull": {"sources": {"id": source_id}},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        # Remove from Pinecone
        await rag_service.delete_document(agent_id, source_id)
        
        return await self.get_by_agent_id(agent_id)

    async def get_source_content(self, agent_id: str, source_id: str) -> Optional[str]:
        """Get the full content of a specific source"""
        doc = await knowledge_collection().find_one(
            {"agent_id": agent_id, "sources.id": source_id},
            {"sources.$": 1}
        )
        if doc and doc.get("sources"):
            return doc["sources"][0].get("content")
        return None

    async def get_all_content(self, agent_id: str) -> str:
        """Compile all knowledge base content into a single string for simple RAG"""
        doc = await knowledge_collection().find_one({"agent_id": agent_id})
        if not doc or not doc.get("sources"):
            return ""
        
        compiled_text = []
        for source in doc["sources"]:
            if source["type"] == KnowledgeSourceType.TEXT:
                compiled_text.append(f"Source: {source['name']}\nContent: {source['content']}")
            elif source["type"] == KnowledgeSourceType.FILE:
                # In a real app we'd read the file. For now, if content is cached, use it.
                if source.get("content"):
                    compiled_text.append(f"Source: {source['name']}\nContent: {source['content']}")
        
        return "\n\n---\n\n".join(compiled_text)

knowledge_service = KnowledgeService()
