"""
Query routing logic for the Agentic RAG system.
"""

import logging
import json
import traceback
from typing import Dict, List, Any, Optional, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.tools.base import BaseTool
from app.models.bot_config import BotConfig

logger = logging.getLogger(__name__)


class QueryRouter:
    """
    Routes queries to appropriate tools based on the query content and bot configuration.
    Uses an LLM to determine which tools to use (Self-RAG approach).
    """

    # Tool-specific keywords for keyword-based selection
    TOOL_KEYWORDS = {
        "SQLQueryTool": [
            "database",
            "record",
            "data",
            "table",
            "sql",
            "course",
            "semester",
            "query",
            "select",
            "insert",
            "update",
            "delete",
            "join",
        ],
        "MongoDBQueryTool": [
            "database",
            "record",
            "data",
            "document",
            "collection",
            "mongo",
            "nosql",
            "field",
            "query",
        ],
        "DocumentSearchTool": [
            "document",
            "file",
            "text",
            "content",
            "article",
            "machine learning",
            "paper",
            "pdf",
            "search",
            "find",
        ],
        "WebSearchTool": [
            "web",
            "internet",
            "online",
            "search",
            "website",
            "atlas university",
            "google",
            "browser",
            "url",
            "link",
        ],
    }

    def __init__(self, bot_config: BotConfig, tools: Dict[str, BaseTool]):
        """
        Initialize the query router.

        Args:
            bot_config: The bot configuration
            tools: Dictionary of initialized tools
        """
        self.bot_config = bot_config
        self.tools = tools

        # Initialize the LLM for tool selection
        self.llm = ChatOpenAI(model=bot_config.agent.model, temperature=0.0)

    async def route_query(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Route a query to the appropriate tools.

        Args:
            query: The user query
            **kwargs: Additional arguments

        Returns:
            A dictionary containing the combined results from all tools
        """
        # Use the LLM to determine which tools to use
        tool_selection_result = await self._select_tools_with_reasoning(query)
        tools_to_use = tool_selection_result["selected_tools"]
        logger.info(f"Selected tools: {tools_to_use}")

        # Log the reasoning for tool selection
        reasoning = tool_selection_result.get("reasoning", "No reasoning provided")
        logger.info(f"Tool selection reasoning: {reasoning}")

        # Execute each tool
        tool_responses = await self._execute_tools(tools_to_use, query, **kwargs)

        return {
            "query": query,
            "tool_responses": tool_responses,
            "selected_tools": tools_to_use,
            "tool_selection_reasoning": tool_selection_result.get("reasoning"),
            "raw_llm_output": tool_selection_result.get("raw_llm_output"),
        }

    async def _execute_tools(
        self, tool_names: List[str], query: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Execute the selected tools with the given query.

        Args:
            tool_names: List of tool names to execute
            query: The user query
            **kwargs: Additional arguments

        Returns:
            Dictionary mapping tool names to their responses
        """
        tool_responses = {}

        for tool_name in tool_names:
            if tool_name in self.tools:
                try:
                    tool = self.tools[tool_name]
                    response = await tool.execute(query, **kwargs)
                    tool_responses[tool_name] = response
                except Exception as e:
                    logger.error(f"Error executing tool {tool_name}: {str(e)}")
                    tool_responses[tool_name] = {"success": False, "error": str(e)}
            else:
                logger.warning(f"Tool {tool_name} not found")

        return tool_responses

    def _get_tool_descriptions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get descriptions of available tools.

        Returns:
            Dictionary mapping tool names to their descriptions and configurations
        """
        tool_descriptions = {}

        for tool_config in self.bot_config.tools:
            if tool_config.enabled and tool_config.type in self.tools:
                tool = self.tools[tool_config.type]
                tool_descriptions[tool_config.type] = {
                    "description": tool.get_tool_description(),
                    "config": tool_config.config,
                }

        return tool_descriptions

    def _get_keyword_selected_tools(self, query: str) -> List[str]:
        """
        Select tools based on keywords in the query.

        Args:
            query: The user query

        Returns:
            List of tool names selected based on keywords
        """
        keyword_selected_tools = []
        query_lower = query.lower()

        # Check each tool type and its keywords
        for tool_type, keywords in self.TOOL_KEYWORDS.items():
            if any(keyword in query_lower for keyword in keywords):
                # Check if this tool is enabled in the bot config
                if any(
                    tool.type == tool_type
                    for tool in self.bot_config.tools
                    if tool.enabled
                ):
                    keyword_selected_tools.append(tool_type)

        return keyword_selected_tools

    def _extract_json_from_response(
        self, response_text: str
    ) -> Tuple[Optional[str], str]:
        """
        Extract JSON string from LLM response text.

        Args:
            response_text: The raw response text from the LLM

        Returns:
            Tuple of (extracted JSON string or None, method used)
        """
        # Method 1: Look for ```json blocks
        if "```json" in response_text and "```" in response_text.split("```json", 1)[1]:
            return (
                response_text.split("```json", 1)[1].split("```", 1)[0].strip(),
                "json_code_block",
            )

        # Method 2: Look for ``` blocks (language might not be specified)
        if "```" in response_text and "```" in response_text.split("```", 1)[1]:
            return (
                response_text.split("```", 1)[1].split("```", 1)[0].strip(),
                "code_block",
            )

        # Method 3: Look for { } directly
        if "{" in response_text and "}" in response_text:
            # Find the outermost { and } pair
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start >= 0 and end > start:
                return (response_text[start:end], "json_brackets")

        # Method 4: Use the whole response as a last resort
        return (response_text, "full_text")

    def _parse_llm_response(
        self, response_text: str, keyword_selected_tools: List[str]
    ) -> Dict[str, Any]:
        """
        Parse the LLM response and extract tool selection information.

        Args:
            response_text: The raw response text from the LLM
            keyword_selected_tools: List of tools selected by keyword matching (fallback)

        Returns:
            Dictionary containing selected tools, reasoning, and raw LLM output
        """
        # Extract JSON from the response
        json_str, extraction_method = self._extract_json_from_response(response_text)

        # If we couldn't extract a JSON string, use the keyword-based selection
        if not json_str or json_str.isspace():
            logger.warning(
                "Could not extract JSON from LLM response, using keyword-based selection"
            )
            selected_tools = self._get_fallback_tools(keyword_selected_tools)
            return {
                "selected_tools": selected_tools,
                "reasoning": "Could not extract JSON from LLM response, using keyword-based or all enabled tools selection",
                "raw_llm_output": {
                    "response_text": response_text,
                    "error": "Could not extract JSON",
                    "extraction_method": extraction_method,
                },
            }

        try:
            # Try to parse the JSON
            result = json.loads(json_str)
            selected_tools = result.get("selected_tools", [])
            reasoning = result.get("reasoning", "No reasoning provided")

            logger.info(f"Tool selection reasoning: {reasoning}")

            # Filter out any tools that don't exist
            selected_tools = [
                tool_name for tool_name in selected_tools if tool_name in self.tools
            ]

            # Check if the LLM explicitly returned an empty list of tools
            if "selected_tools" in result and result["selected_tools"] == []:
                logger.info("LLM explicitly decided to use no tools for this query")
                return {
                    "selected_tools": [],
                    "reasoning": reasoning
                    or "The query can be answered without using any tools",
                    "raw_llm_output": {
                        "response_text": response_text,
                        "parsed_json": result,
                        "extraction_method": extraction_method,
                    },
                }

            # If no tools were selected (due to filtering or other reasons), use the keyword-based selection
            if not selected_tools:
                logger.info(
                    "No specific tools selected by LLM, using keyword-based selection"
                )
                selected_tools = self._get_fallback_tools(keyword_selected_tools)
                return {
                    "selected_tools": selected_tools,
                    "reasoning": "No specific tools selected by LLM, using keyword-based or all enabled tools selection",
                    "raw_llm_output": {
                        "response_text": response_text,
                        "parsed_json": result,
                        "extraction_method": extraction_method,
                    },
                }

            return {
                "selected_tools": selected_tools,
                "reasoning": reasoning,
                "raw_llm_output": {
                    "response_text": response_text,
                    "parsed_json": result,
                    "extraction_method": extraction_method,
                },
            }

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing LLM response as JSON: {str(e)}")
            logger.error(f"Attempted to parse: '{json_str}'")
            logger.error(f"Full response: '{response_text}'")

            # Fallback to keyword-based selection
            logger.info("Falling back to keyword-based selection")
            selected_tools = self._get_fallback_tools(keyword_selected_tools)
            return {
                "selected_tools": selected_tools,
                "reasoning": f"Error parsing LLM response as JSON: {str(e)}. Using keyword-based or all enabled tools selection.",
                "raw_llm_output": {
                    "response_text": response_text,
                    "error": f"JSON decode error: {str(e)}",
                    "extraction_method": extraction_method,
                },
            }

    def _get_fallback_tools(self, keyword_selected_tools: List[str]) -> List[str]:
        """
        Get fallback tools when LLM selection fails.

        Args:
            keyword_selected_tools: List of tools selected by keyword matching

        Returns:
            List of tool names to use as fallback
        """
        # Use keyword-selected tools if available, otherwise use all enabled tools
        if keyword_selected_tools:
            return keyword_selected_tools
        else:
            return [tool.type for tool in self.bot_config.tools if tool.enabled]

    def _get_tool_selection_prompt(
        self, query: str, tool_descriptions: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """
        Create the prompt for tool selection.

        Args:
            query: The user query
            tool_descriptions: Dictionary of tool descriptions

        Returns:
            List of message dictionaries for the LLM
        """
        # Format the tool descriptions for the prompt
        tool_desc_str = ""
        for tool_name, info in tool_descriptions.items():
            tool_desc_str += f"- {tool_name}: {info['description']}\n"

        # Create a system message
        system_message = """
You are an AI assistant that decides which tools to use to answer a user's query.
You will be given a user query and a list of available tools with their descriptions.
Your task is to select the most appropriate tools to use to answer the query.

Follow these guidelines:
1. Only select tools that are directly relevant to answering the query
2. Consider the capabilities and limitations of each tool
3. You can select multiple tools if needed
4. You can select no tools if you believe the query can be answered without any tools
   - For simple greetings, casual conversation, or questions that don't require external data, return an empty list []
   - This is an important feature of the system - only use tools when necessary
5. Respond in JSON format with a list of tool names and a brief explanation for each selection

Example response formats:
For queries requiring tools:
```json
{
  "selected_tools": ["ToolName1", "ToolName2"],
  "reasoning": "I selected ToolName1 because... I selected ToolName2 because..."
}
```

For queries that don't require tools:
```json
{
  "selected_tools": [],
  "reasoning": "This query is a simple greeting that doesn't require any external data or tools."
}
```
"""

        # Create a user message
        user_message = f"""
User Query: {query}

Available Tools:
{tool_desc_str}

Select the most appropriate tools to answer this query.
"""

        return [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

    async def _select_tools_with_reasoning(self, query: str) -> Dict[str, Any]:
        """
        Select which tools to use for a query using an LLM and return the reasoning.

        Args:
            query: The user query

        Returns:
            Dictionary containing selected tools, reasoning, and raw LLM output
        """
        # Get descriptions of available tools
        tool_descriptions = self._get_tool_descriptions()

        if not tool_descriptions:
            # If no tools are available, return an empty list
            logger.warning("No tools available for selection")
            return {
                "selected_tools": [],
                "reasoning": "No tools available for selection",
            }

        # Get keyword-based tool selection (fallback mechanism)
        keyword_selected_tools = self._get_keyword_selected_tools(query)

        try:
            # Create the prompt for tool selection
            messages = self._get_tool_selection_prompt(query, tool_descriptions)

            # Generate the tool selection
            response = self.llm.invoke(messages)

            # Parse the response
            response_text = response.content.strip()
            logger.info(f"Raw LLM response: {response_text}")

            # Parse the LLM response
            return self._parse_llm_response(response_text, keyword_selected_tools)

        except Exception as e:
            logger.error(f"Error selecting tools with LLM: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception traceback: {traceback.format_exc()}")

            # Fallback to keyword-based selection
            logger.info("Falling back to keyword-based selection due to exception")
            selected_tools = self._get_fallback_tools(keyword_selected_tools)
            return {
                "selected_tools": selected_tools,
                "reasoning": f"Error selecting tools with LLM: {str(e)}. Using keyword-based or all enabled tools selection.",
                "raw_llm_output": {"error": f"Exception: {str(e)}"},
            }
