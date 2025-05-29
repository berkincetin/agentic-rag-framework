"""
Test script for the Self-RAG implementation.
"""

import asyncio
import logging
import os
import sys
from unittest.mock import MagicMock, patch

# Import the QueryRouter class for patching
from app.core.query_router import QueryRouter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Mock environment variables
os.environ["OPENAI_API_KEY"] = "mock-api-key"
os.environ["TAVILY_API_KEY"] = "mock-api-key"


# This function is not used but kept for reference
async def mock_execute(query: str, **kwargs):
    """Mock execute method for tools."""
    return {"success": True, "results": [f"Mock result for query: {query}"]}


async def test_query_router():
    """Test the QueryRouter's tool selection logic."""
    from app.models.bot_config import BotConfig, AgentConfig, ToolConfig

    # Create a mock bot config
    bot_config = BotConfig(
        name="TestBot",
        description="A test bot",
        prompts={
            "system_prompt_path": "test/system.txt",
            "query_prompt_path": "test/query.txt",
        },
        agent=AgentConfig(model="gpt-4", type="langgraph"),
        tools=[
            ToolConfig(type="DocumentSearchTool", enabled=True, config={}),
            ToolConfig(type="MongoDBQueryTool", enabled=True, config={}),
            ToolConfig(type="SQLQueryTool", enabled=True, config={}),
            ToolConfig(type="WebSearchTool", enabled=True, config={}),
        ],
    )

    # Create mock tools with async execute methods
    tools = {}
    for tool_name in [
        "DocumentSearchTool",
        "MongoDBQueryTool",
        "SQLQueryTool",
        "WebSearchTool",
    ]:
        mock_tool = MagicMock()
        mock_tool.get_tool_description.return_value = (
            f"Mock description for {tool_name}"
        )

        # Create a proper async execute method for each tool
        async def make_execute(name):
            async def execute(query, **kwargs):
                return {
                    "success": True,
                    "results": [f"Mock result for {name} with query: {query}"],
                }

            return execute

        # Assign the async method to the mock
        mock_tool.execute = await make_execute(tool_name)
        tools[tool_name] = mock_tool

    # Create the query router
    query_router = QueryRouter(bot_config, tools)

    # Define a custom _select_tools method to replace the LLM-based one
    async def mock_select_tools(query):
        """Mock implementation of tool selection based on query keywords."""
        selected_tools = []

        if "course" in query.lower() or "semester" in query.lower():
            selected_tools.append("MongoDBQueryTool")

        if "document" in query.lower() or "machine learning" in query.lower():
            selected_tools.append("DocumentSearchTool")

        if (
            "web" in query.lower()
            or "search" in query.lower()
            or "atlas university" in query.lower()
        ):
            selected_tools.append("WebSearchTool")

        if "budget" in query.lower() or "department" in query.lower():
            selected_tools.append("SQLQueryTool")

        # If no tools were selected, use a default
        if not selected_tools:
            selected_tools.append("WebSearchTool")

        return selected_tools

    # Replace the _select_tools method with our mock
    with patch.object(QueryRouter, "_select_tools", side_effect=mock_select_tools):
        # Test queries that should trigger different tools
        test_queries = [
            "What courses are available for the fall semester?",
            "Find documents about machine learning",
            "Search the web for information about Atlas University",
            "What is the budget for the Computer Science department?",
            "Tell me about the history of Istanbul",
        ]

        for query in test_queries:
            print(f"\n\nTesting query: {query}")

            # Route the query
            result = await query_router.route_query(query)

            # Print the selected tools
            selected_tools = list(result["tool_responses"].keys())
            print(f"Selected tools: {selected_tools}")

            # Print which tools were executed
            for tool_name in tools:
                if tool_name in selected_tools:
                    print(f"  - {tool_name} was executed")
                else:
                    print(f"  - {tool_name} was NOT executed")

            # Reset all mocks for the next query
            for tool_mock in tools.values():
                tool_mock.reset_mock()


async def main():
    """Main test function."""
    print("Testing Self-RAG Query Router")
    print("=============================")
    await test_query_router()


if __name__ == "__main__":
    asyncio.run(main())
