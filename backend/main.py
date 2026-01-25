"""
AgentBuilder Backend API
FastAPI application entry point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import connect_db, close_db
from app.services.tool_service import tool_service
from app.api import agents, workflows, tools, logs
from demo_agents.demo_api import router as demo_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await connect_db()
    
    # Initialize built-in tools
    await tool_service.initialize_builtin_tools()
    print("✅ Built-in tools initialized")
    
    yield
    
    # Shutdown
    await close_db()
    print("👋 Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    AgentBuilder - UI-first AI Agent Platform
    
    Build, run, and observe AI agents with ease.
    
    ## Features
    - 🤖 Agent Builder - Create agents via simple forms
    - 🔄 Workflow Orchestration - Multi-agent workflows
    - 🛠️ Tool Registry - Built-in and custom tools
    - 📊 Observability - Execution logs and monitoring
    """,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# API info
@app.get("/")
async def root():
    """API root - returns basic info"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "UI-first AI Agent Platform",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


# Include API routers
app.include_router(agents.router, prefix=settings.API_V1_PREFIX)
app.include_router(workflows.router, prefix=settings.API_V1_PREFIX)
app.include_router(tools.router, prefix=settings.API_V1_PREFIX)
app.include_router(logs.router, prefix=settings.API_V1_PREFIX)
app.include_router(demo_router, prefix=settings.API_V1_PREFIX)


# Demo agents endpoint
@app.get(f"{settings.API_V1_PREFIX}/demo")
async def list_demo_agents():
    """List available demo agents"""
    return {
        "demos": [
            {
                "id": "research_agent",
                "name": "Research & Insight Agent",
                "description": "Searches web + documents, produces structured reports",
                "endpoint": f"{settings.API_V1_PREFIX}/demo/research"
            },
            {
                "id": "automation_agent",
                "name": "Automation / Ops Agent",
                "description": "Executes operational tasks with deterministic outputs",
                "endpoint": f"{settings.API_V1_PREFIX}/demo/automation"
            },
            {
                "id": "multi_agent",
                "name": "Multi-Agent Orchestrator",
                "description": "Planner → Executor → Critic workflow",
                "endpoint": f"{settings.API_V1_PREFIX}/demo/multi-agent"
            }
        ]
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
