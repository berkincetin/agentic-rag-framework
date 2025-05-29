"""
API request and response models for the Agentic RAG system.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for querying a bot."""

    query: str = Field(..., description="The user's query")
    session_id: Optional[str] = Field(
        None, description="Session ID for conversation context"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata for the query"
    )


class ToolResponse(BaseModel):
    """Response from a tool."""

    tool_name: str = Field(
        ..., description="The name of the tool that generated this response"
    )
    content: Any = Field(..., description="The content of the tool's response")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class QueryResponse(BaseModel):
    """Response model for a bot query."""

    bot_name: str = Field(
        ..., description="The name of the bot that processed the query"
    )
    query: str = Field(..., description="The original query")
    response: str = Field(..., description="The bot's response to the query")
    tool_responses: Optional[List[ToolResponse]] = Field(
        None, description="Responses from individual tools"
    )
    selected_tools: Optional[List[str]] = Field(
        None, description="List of tool names that were selected for this query"
    )
    tool_selection_reasoning: Optional[str] = Field(
        None, description="The reasoning behind the tool selection"
    )
    raw_llm_output: Optional[Dict[str, Any]] = Field(
        None, description="Raw output from the LLM tool selection process"
    )
    session_id: Optional[str] = Field(
        None, description="Session ID for conversation context"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )


class BotInfo(BaseModel):
    """Information about a bot."""

    name: str = Field(..., description="The name of the bot")
    description: str = Field("", description="A description of the bot")
    tools: List[str] = Field(
        default_factory=list, description="The tools available to the bot"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class BotsListResponse(BaseModel):
    """Response model for listing available bots."""

    bots: List[BotInfo] = Field(..., description="List of available bots")
