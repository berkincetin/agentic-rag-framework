"""
FastAPI application for the Agentic RAG system.
"""

import logging
import os

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv

from app.core.agentic_rag import AgenticRAG
from app.agents.langgraph_agent import LangGraphAgent
from app.models.api_models import (
    QueryRequest,
    BotInfo,
    BotsListResponse,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize the AgenticRAG system
agentic_rag = AgenticRAG()

# Create the FastAPI application
app = FastAPI(
    title="Agentic RAG API",
    description="API for the Agentic RAG system",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to get the AgenticRAG instance
def get_agentic_rag() -> AgenticRAG:
    return agentic_rag


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint for health check."""
    return {"status": "ok", "message": "Agentic RAG API is running"}


@app.get("/bots", response_model=BotsListResponse, tags=["Bots"])
async def list_bots(rag: AgenticRAG = Depends(get_agentic_rag)):
    """List all available bots."""
    bot_names = rag.get_bot_names()
    bots = []

    for bot_name in bot_names:
        bot = rag.get_bot(bot_name)
        if bot:
            config = bot["config"]
            bots.append(
                BotInfo(
                    name=config.name,
                    description=config.description,
                    tools=[tool.type for tool in config.tools if tool.enabled],
                    metadata=config.metadata,
                )
            )

    return BotsListResponse(bots=bots)


@app.get("/bots/{bot_name}", response_model=BotInfo, tags=["Bots"])
async def get_bot_info(bot_name: str, rag: AgenticRAG = Depends(get_agentic_rag)):
    """Get information about a specific bot."""
    bot = rag.get_bot(bot_name)
    if not bot:
        raise HTTPException(status_code=404, detail=f"Bot not found: {bot_name}")

    config = bot["config"]
    return BotInfo(
        name=config.name,
        description=config.description,
        tools=[tool.type for tool in config.tools if tool.enabled],
        metadata=config.metadata,
    )


@app.post("/bots/{bot_name}/query", tags=["Queries"])
async def query_bot(
    bot_name: str, request: QueryRequest, rag: AgenticRAG = Depends(get_agentic_rag)
):
    """Query a specific bot."""
    try:
        bot = rag.get_bot(bot_name)
        if not bot:
            raise HTTPException(status_code=404, detail=f"Bot not found: {bot_name}")

        response = await rag.process_query(bot_name, request)

        # Convert to dict and then to JSON with ensure_ascii=False to preserve Turkish characters
        response_dict = response.dict()

        # Ensure all values are JSON serializable
        def ensure_serializable(obj):
            if isinstance(obj, dict):
                return {k: ensure_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [ensure_serializable(item) for item in obj]
            elif hasattr(obj, "keys") and callable(obj.keys):
                # Convert dict-like objects (like ResultProxy.keys()) to lists
                return list(obj)
            else:
                return obj

        # Apply the serialization fix to the response dictionary
        serializable_response = ensure_serializable(response_dict)

        # Return a custom JSONResponse with proper encoding
        return JSONResponse(
            content=serializable_response, media_type="application/json; charset=utf-8"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/bots/{bot_name}/clear-memory", tags=["Queries"])
async def clear_memory(
    bot_name: str, session_id: str = None, rag: AgenticRAG = Depends(get_agentic_rag)
):
    """Clear the memory for a specific session."""
    try:
        bot = rag.get_bot(bot_name)
        if not bot:
            raise HTTPException(status_code=404, detail=f"Bot not found: {bot_name}")

        agent: LangGraphAgent = bot["agent"]

        if session_id:
            # Clear memory for a specific session
            agent.memory_manager.clear_memory(session_id)
            return {
                "status": "ok",
                "message": f"Memory cleared for session: {session_id}",
            }
        else:
            # If no session_id is provided, return an error
            raise HTTPException(status_code=400, detail="session_id is required")
    except Exception as e:
        logger.error(f"Error clearing memory: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing memory: {str(e)}")


@app.post("/reload", tags=["Admin"])
async def reload_bots(rag: AgenticRAG = Depends(get_agentic_rag)):
    """Reload all bot configurations."""
    try:
        # Reload configurations
        rag.config_loader.reload_configs()

        # Reload bots
        rag._load_bots()

        return {"status": "ok", "message": "Bots reloaded successfully"}
    except Exception as e:
        logger.error(f"Error reloading bots: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reloading bots: {str(e)}")


def start():
    """Start the FastAPI application with Uvicorn."""
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "False").lower() == "true",
    )


if __name__ == "__main__":
    start()
