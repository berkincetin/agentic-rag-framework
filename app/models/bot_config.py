"""
Bot configuration models for the Agentic RAG system.
"""

from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field


class ToolConfig(BaseModel):
    """Configuration for a tool."""

    type: str = Field(..., description="The type of tool to use")
    enabled: bool = Field(True, description="Whether this tool is enabled")
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Tool-specific configuration"
    )


class DatabaseConfig(BaseModel):
    """Configuration for database connections."""

    mongodb: Optional[Dict[str, Any]] = Field(
        None, description="MongoDB connection configuration"
    )
    sql: Optional[Dict[str, Any]] = Field(
        None, description="SQL database connection configuration"
    )


class PromptConfig(BaseModel):
    """Configuration for prompts."""

    system_prompt_path: str = Field(
        ..., description="Path to the system prompt template"
    )
    query_prompt_path: str = Field(..., description="Path to the query prompt template")
    additional_prompts: Optional[Dict[str, str]] = Field(
        None, description="Additional prompt templates"
    )


class AgentConfig(BaseModel):
    """Configuration for the LangGraph agent."""

    type: str = Field("langgraph", description="The type of agent to use")
    model: str = Field("gpt-4", description="The model to use for the agent")
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Agent-specific configuration"
    )


class BotConfig(BaseModel):
    """Configuration for a bot."""

    name: str = Field(..., description="The name of the bot")
    description: str = Field("", description="A description of the bot")
    tools: List[ToolConfig] = Field(
        default_factory=list, description="The tools available to the bot"
    )
    database: Optional[DatabaseConfig] = Field(
        None, description="Database configuration"
    )
    prompts: PromptConfig = Field(..., description="Prompt configuration")
    agent: AgentConfig = Field(
        default_factory=AgentConfig, description="Agent configuration"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
