"""
MongoDB Database Configuration
Async MongoDB setup using Motor
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from app.core.config import settings


class MongoDB:
    """MongoDB connection manager"""
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None


mongodb = MongoDB()


async def connect_db():
    """Connect to MongoDB"""
    mongodb.client = AsyncIOMotorClient(settings.MONGO_URI)
    mongodb.db = mongodb.client[settings.MONGO_DB_NAME]
    
    # Create indexes for better query performance
    await create_indexes()
    
    print(f"Connected to MongoDB: {settings.MONGO_DB_NAME}")


async def close_db():
    """Close MongoDB connection"""
    if mongodb.client:
        mongodb.client.close()
        print("MongoDB connection closed")


async def create_indexes():
    """Create database indexes for performance"""
    db = mongodb.db
    
    # Agents indexes
    await db.agents.create_index("name")
    await db.agents.create_index("user_id")
    await db.agents.create_index("project_id")
    await db.agents.create_index("status")
    await db.agents.create_index("created_at")
    
    # Workflows indexes
    await db.workflows.create_index("name")
    await db.workflows.create_index("user_id")
    await db.workflows.create_index("project_id")
    await db.workflows.create_index("status")
    
    # Executions indexes
    await db.executions.create_index("agent_id")
    await db.executions.create_index("workflow_id")
    await db.executions.create_index("status")
    await db.executions.create_index("created_at")
    await db.executions.create_index([("agent_id", 1), ("created_at", -1)])
    
    # Execution steps indexes
    await db.execution_steps.create_index("execution_id")
    await db.execution_steps.create_index([("execution_id", 1), ("sequence_number", 1)])
    
    # Execution logs indexes
    await db.execution_logs.create_index("execution_id")
    await db.execution_logs.create_index([("execution_id", 1), ("timestamp", 1)])
    
    # Tools indexes
    await db.tools.create_index("name", unique=True)
    await db.tools.create_index("category")
    
    # Users indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)
    
    # Projects indexes
    await db.projects.create_index("user_id")
    await db.projects.create_index("name")


def get_db() -> AsyncIOMotorDatabase:
    """Get database instance"""
    return mongodb.db


# Collection helpers
def agents_collection():
    return mongodb.db.agents


def workflows_collection():
    return mongodb.db.workflows


def executions_collection():
    return mongodb.db.executions


def execution_steps_collection():
    return mongodb.db.execution_steps


def execution_logs_collection():
    return mongodb.db.execution_logs


def tools_collection():
    return mongodb.db.tools


def users_collection():
    return mongodb.db.users


def projects_collection():
    return mongodb.db.projects


def knowledge_collection():
    return mongodb.db.knowledge
