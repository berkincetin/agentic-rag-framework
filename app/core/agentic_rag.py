"""
Main AgenticRAG class for the Agentic RAG system.
"""

import logging
import os
from typing import Dict, List, Optional, Any, Type

from app.models.bot_config import BotConfig
from app.models.api_models import QueryRequest, QueryResponse, ToolResponse
from app.core.config_loader import ConfigLoader
from app.core.query_router import QueryRouter
from app.tools.base import BaseTool
from app.tools.web_search import WebSearchTool

# Optional imports for database tools
try:
    from app.tools.document_search import DocumentSearchTool

    DOCUMENT_SEARCH_AVAILABLE = True
except ImportError:
    DOCUMENT_SEARCH_AVAILABLE = False
    DocumentSearchTool = None

try:
    from app.tools.mongodb_query import MongoDBQueryTool

    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    MongoDBQueryTool = None

try:
    from app.tools.sql_query import SQLQueryTool

    SQL_AVAILABLE = True
except ImportError:
    SQL_AVAILABLE = False
    SQLQueryTool = None
from app.agents.langgraph_agent import LangGraphAgent

logger = logging.getLogger(__name__)


class AgenticRAG:
    """
    Main class for the Agentic RAG system.
    Handles tool initialization, prompt loading, and query routing.
    """

    # Map of tool types to tool classes (with availability checks)
    @property
    def TOOL_CLASSES(self):
        tool_classes = {
            "WebSearchTool": WebSearchTool,
        }

        if DOCUMENT_SEARCH_AVAILABLE and DocumentSearchTool:
            tool_classes["DocumentSearchTool"] = DocumentSearchTool

        if MONGODB_AVAILABLE and MongoDBQueryTool:
            tool_classes["MongoDBQueryTool"] = MongoDBQueryTool

        if SQL_AVAILABLE and SQLQueryTool:
            tool_classes["SQLQueryTool"] = SQLQueryTool

        return tool_classes

    def __init__(self, config_dir: str = "configs", prompts_dir: str = "prompts"):
        """
        Initialize the AgenticRAG system.

        Args:
            config_dir: Directory containing bot configurations
            prompts_dir: Directory containing prompt templates
        """
        self.config_dir = config_dir
        self.prompts_dir = prompts_dir
        self.config_loader = ConfigLoader(config_dir)
        self.bots: Dict[str, Dict[str, Any]] = {}

        # Load all bot configurations
        self._load_bots()

    def _load_bots(self) -> None:
        """Load all bot configurations and initialize tools."""
        bot_configs = self.config_loader.get_all_configs()

        for bot_name, bot_config in bot_configs.items():
            try:
                # Initialize tools
                tools = self._initialize_tools(bot_config)

                # Load prompts
                system_prompt = self._load_prompt(bot_config.prompts.system_prompt_path)
                query_prompt = self._load_prompt(bot_config.prompts.query_prompt_path)

                # Initialize query router
                query_router = QueryRouter(bot_config, tools)

                # Initialize agent
                agent = LangGraphAgent(bot_config.agent, system_prompt, query_prompt)

                # Store bot components
                self.bots[bot_name] = {
                    "config": bot_config,
                    "tools": tools,
                    "query_router": query_router,
                    "agent": agent,
                }

                logger.info(f"Loaded bot: {bot_name}")
            except Exception as e:
                logger.error(f"Error loading bot {bot_name}: {str(e)}")

    def _initialize_tools(self, bot_config: BotConfig) -> Dict[str, BaseTool]:
        """
        Initialize tools for a bot.

        Args:
            bot_config: Bot configuration

        Returns:
            Dictionary of initialized tools
        """
        tools = {}

        for tool_config in bot_config.tools:
            if not tool_config.enabled:
                continue

            tool_class = self.TOOL_CLASSES.get(tool_config.type)
            if not tool_class:
                logger.warning(f"Unknown tool type: {tool_config.type}")
                continue

            try:
                tool = tool_class(tool_config.config)
                tools[tool_config.type] = tool
                logger.info(f"Initialized tool: {tool_config.type}")
            except Exception as e:
                logger.error(f"Error initializing tool {tool_config.type}: {str(e)}")

        return tools

    def _load_prompt(self, prompt_path: str) -> str:
        """
        Load a prompt template.

        Args:
            prompt_path: Path to the prompt template

        Returns:
            The prompt template as a string
        """
        # Check if the path is absolute
        if os.path.isabs(prompt_path):
            full_path = prompt_path
        else:
            # Assume the path is relative to the prompts directory
            full_path = os.path.join(self.prompts_dir, prompt_path)

        try:
            with open(full_path, "r") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading prompt from {full_path}: {str(e)}")
            return "No prompt template available."

    def _ensure_serializable(self, obj: Any) -> Any:
        """
        Ensure an object is JSON serializable.

        Args:
            obj: The object to make serializable

        Returns:
            A JSON serializable version of the object
        """
        if isinstance(obj, dict):
            return {k: self._ensure_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._ensure_serializable(item) for item in obj]
        elif hasattr(obj, "keys") and callable(obj.keys):
            # Convert dict-like objects (like ResultProxy.keys()) to lists
            return list(obj)
        else:
            return obj

    def get_bot_names(self) -> List[str]:
        """
        Get the names of all loaded bots.

        Returns:
            List of bot names
        """
        return list(self.bots.keys())

    def get_bot(self, bot_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a bot by name.

        Args:
            bot_name: Name of the bot

        Returns:
            Bot components or None if not found
        """
        return self.bots.get(bot_name)

    async def process_query(
        self, bot_name: str, request: QueryRequest
    ) -> QueryResponse:
        """
        Process a query for a specific bot.

        Args:
            bot_name: Name of the bot
            request: Query request

        Returns:
            Query response
        """
        bot = self.get_bot(bot_name)
        if not bot:
            raise ValueError(f"Bot not found: {bot_name}")

        try:
            # Route the query to tools
            query_router: QueryRouter = bot["query_router"]
            tool_results = await query_router.route_query(
                request.query, **request.metadata or {}
            )

            # Process the query with the agent
            agent: LangGraphAgent = bot["agent"]
            agent_response = await agent.process_query(
                request.query,
                tool_results["tool_responses"],
                session_id=request.session_id,
            )

            # Format tool responses
            tool_responses = []
            for tool_name, result in tool_results["tool_responses"].items():
                # Ensure the result is JSON serializable
                serializable_result = self._ensure_serializable(result)
                tool_responses.append(
                    ToolResponse(
                        tool_name=tool_name, content=serializable_result, metadata={}
                    )
                )

            # Create the response
            response = QueryResponse(
                bot_name=bot_name,
                query=request.query,
                response=agent_response["response"],
                tool_responses=tool_responses,
                selected_tools=tool_results.get("selected_tools"),
                tool_selection_reasoning=tool_results.get("tool_selection_reasoning"),
                raw_llm_output=tool_results.get("raw_llm_output"),
                session_id=request.session_id,
                metadata=(
                    {"error": agent_response.get("error")}
                    if agent_response.get("error")
                    else {}
                ),
            )

            return response
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise
