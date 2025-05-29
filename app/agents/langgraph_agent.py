"""
LangGraph agent implementation for the Agentic RAG system.
"""

import logging
import json
from typing import Dict, List, Optional, Any, TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

from app.models.bot_config import AgentConfig
from app.core.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


# Define the state for the agent
class AgentState(TypedDict):
    """State for the LangGraph agent."""

    query: str
    context: List[Dict[str, Any]]
    tool_results: Dict[str, Any]
    response: Optional[str]
    error: Optional[str]
    chat_history: Optional[str]


class LangGraphAgent:
    """LangGraph agent implementation for the Agentic RAG system."""

    def __init__(
        self, agent_config: AgentConfig, system_prompt: str, query_prompt: str
    ):
        """
        Initialize the LangGraph agent.

        Args:
            agent_config: Agent configuration
            system_prompt: System prompt template
            query_prompt: Query prompt template
        """
        self.agent_config = agent_config
        self.system_prompt = system_prompt
        self.query_prompt = query_prompt

        # Initialize the LLM
        self.llm = ChatOpenAI(
            model=agent_config.model,
            temperature=agent_config.config.get("temperature", 0.0),
        )

        # Initialize memory manager
        self.memory_manager = MemoryManager()

        # Initialize the graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph agent graph.

        Returns:
            The StateGraph for the agent
        """

        # Define the nodes
        def retrieve_context(state: AgentState) -> AgentState:
            """Retrieve context from tool results."""
            try:
                # Extract context from tool results
                context = []
                tool_results = state["tool_results"]

                # Process document search results
                if "DocumentSearchTool" in tool_results:
                    doc_results = tool_results["DocumentSearchTool"]
                    if doc_results.get("success", False):
                        for doc in doc_results.get("documents", []):
                            context.append(
                                {
                                    "source": "Document",
                                    "content": doc.get("content", ""),
                                    "metadata": doc.get("metadata", {}),
                                }
                            )

                # Process MongoDB results
                if "MongoDBQueryTool" in tool_results:
                    mongo_results = tool_results["MongoDBQueryTool"]
                    if mongo_results.get("success", False):
                        # Log MongoDB results being added to context
                        result_count = len(mongo_results.get("results", []))
                        logger.info(
                            f"Adding {result_count} MongoDB results to agent context"
                        )

                        # Log the MongoDB query that was used
                        if "query" in mongo_results:
                            logger.info(
                                f"MongoDB query used: {json.dumps(mongo_results['query'], ensure_ascii=False)}"
                            )

                        for i, result in enumerate(mongo_results.get("results", [])):
                            # Extract the most relevant content from the result
                            content = ""
                            if "page_content" in result:
                                content = result["page_content"]
                            elif "_id" in result:
                                # If there's no page_content, use the whole result but limit size
                                content = str(result)

                            # Add to context
                            context_item = {
                                "source": f"MongoDB ({mongo_results.get('collection', 'unknown')})",
                                "content": content,
                            }
                            context.append(context_item)

                            # Log the first few items being added to context
                            if (
                                i < 2
                            ):  # Only log the first 2 items to avoid excessive logging
                                content_preview = (
                                    content[:100] + "..."
                                    if len(content) > 100
                                    else content
                                )
                                log_data = {
                                    "source": context_item["source"],
                                    "content_preview": content_preview,
                                }
                                logger.info(
                                    f"MongoDB result {i+1} added to context: {json.dumps(log_data, ensure_ascii=False)}"
                                )
                    else:
                        # Log if MongoDB query was unsuccessful
                        logger.warning(
                            f"MongoDB query was unsuccessful: {mongo_results.get('error', 'Unknown error')}"
                        )

                # Process SQL results
                if "SQLQueryTool" in tool_results:
                    sql_results = tool_results["SQLQueryTool"]
                    if sql_results.get("success", False):
                        # Add the SQL query that was executed
                        if "query" in sql_results:
                            context.append(
                                {
                                    "source": "SQL Query",
                                    "content": f"Executed SQL query: {sql_results['query']}",
                                }
                            )

                        # Format SQL results in a more readable way
                        if (
                            sql_results.get("results")
                            and len(sql_results.get("results", [])) > 0
                        ):
                            # Create a formatted table-like representation of the results
                            columns = sql_results.get("columns", [])
                            results_str = "SQL Query Results:\n"

                            # Add column headers
                            if columns:
                                results_str += " | ".join(columns) + "\n"
                                results_str += (
                                    "-"
                                    * (
                                        sum(len(col) for col in columns)
                                        + (3 * (len(columns) - 1))
                                    )
                                    + "\n"
                                )

                            # Add rows
                            for result in sql_results.get("results", []):
                                if isinstance(result, dict):
                                    row_values = [
                                        str(result.get(col, "")) for col in columns
                                    ]
                                    results_str += " | ".join(row_values) + "\n"
                                else:
                                    results_str += str(result) + "\n"

                            context.append(
                                {
                                    "source": "SQL Database Results",
                                    "content": results_str,
                                }
                            )

                            # Also add individual results for more detailed processing
                            for result in sql_results.get("results", []):
                                context.append(
                                    {"source": "SQL Database", "content": str(result)}
                                )
                    else:
                        # Add error information if SQL query failed
                        context.append(
                            {
                                "source": "SQL Database Error",
                                "content": f"SQL query failed: {sql_results.get('error', 'Unknown error')}",
                            }
                        )

                # Process web search results
                if "WebSearchTool" in tool_results:
                    web_results = tool_results["WebSearchTool"]
                    if web_results.get("success", False):
                        for result in web_results.get("results", []):
                            context.append(
                                {
                                    "source": f"Web ({result.get('url', 'unknown')})",
                                    "content": result.get("content", ""),
                                }
                            )

                # Update the state with the processed context
                return {**state, "context": context}
            except Exception as e:
                logger.error(f"Error processing context in retrieve_context: {str(e)}")
                # Return the original state if there's an error
                return state

        def generate_response(state: AgentState) -> AgentState:
            """Generate a response using the LLM."""
            try:
                # Format the context
                context_str = ""
                context_sources = []

                # Log the number of context items
                logger.info(
                    f"Formatting {len(state['context'])} context items for response generation"
                )

                for item in state["context"]:
                    if isinstance(item, dict):
                        source = item.get("source", "Unknown")
                        context_sources.append(source)

                        context_str += f"Source: {source}\n"
                        context_str += f"Content: {item.get('content', '')}\n\n"
                    else:
                        context_str += f"{item}\n\n"

                # Log the sources used in context
                if context_sources:
                    logger.info(
                        f"Context sources used: {', '.join(context_sources[:5])}"
                        + (
                            f" and {len(context_sources) - 5} more..."
                            if len(context_sources) > 5
                            else ""
                        )
                    )

                # Log a preview of the context
                context_preview = (
                    context_str[:300] + "..." if len(context_str) > 300 else context_str
                )
                logger.info(
                    f"Context preview for response generation: {context_preview}"
                )

                # Create the prompt with chat history if available
                # Skip the ChatPromptTemplate and use a simple approach
                try:
                    # Create a simple system message
                    system_message = self.system_prompt

                    # Add chat history if available
                    if state.get("chat_history"):
                        chat_history = state["chat_history"]
                        logger.info(
                            f"Including chat history in prompt (length: {len(chat_history)})"
                        )
                        system_message += f"\n\nPrevious conversation history:\n{chat_history}\n\nPlease consider the above conversation history when responding."

                    # Create a simple user message with the context and query
                    # Include information about which tools were used
                    tool_info = ""
                    if state["tool_results"]:
                        used_tools = list(state["tool_results"].keys())
                        tool_info = f"\nTools used: {', '.join(used_tools)}\n"

                    user_message = f"Context:\n{context_str}\n{tool_info}\nQuestion: {state['query']}"

                    # Create the messages list
                    simple_messages = [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message},
                    ]

                    # Invoke the LLM with the simple messages
                    response = self.llm.invoke(simple_messages)

                    logger.info(
                        "Successfully generated response using simple messages approach"
                    )
                except Exception as format_error:
                    logger.error(
                        f"Error with simple messages approach: {str(format_error)}"
                    )

                    # Fallback to an even simpler prompt
                    fallback_prompt = f"Based on the following information:\n\n{context_str}\n\nPlease answer this question: {state['query']}"
                    response = self.llm.invoke(fallback_prompt)

                    logger.info("Used fallback prompt for response generation")

                # Log the generated response
                response_content = response.content
                response_preview = (
                    response_content[:200] + "..."
                    if len(response_content) > 200
                    else response_content
                )
                logger.info(f"Generated response: {response_preview}")

                # Log whether MongoDB results were used in the response
                if any("MongoDB" in source for source in context_sources):
                    logger.info("MongoDB results were used to generate the response")

                return {**state, "response": response_content, "error": None}
            except Exception as e:
                logger.error(f"Error generating response: {str(e)}")
                return {
                    **state,
                    "response": "I'm sorry, I encountered an error while generating a response.",
                    "error": str(e),
                }

        # Create the graph
        graph = StateGraph(AgentState)

        # Add the nodes
        graph.add_node("retrieve_context", retrieve_context)
        graph.add_node("generate_response", generate_response)

        # Add the edges
        graph.add_edge("retrieve_context", "generate_response")
        graph.add_edge("generate_response", END)

        # Set the entry point
        graph.set_entry_point("retrieve_context")

        # Compile the graph
        return graph.compile()

    async def process_query(
        self, query: str, tool_results: Dict[str, Any], session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a query using the LangGraph agent.

        Args:
            query: The user query
            tool_results: Results from the tools
            session_id: Optional session ID for conversation memory

        Returns:
            A dictionary containing the agent's response
        """
        try:
            # Log the tools that were used
            used_tools = list(tool_results.keys())
            if used_tools:
                logger.info(f"Processing query with tools: {', '.join(used_tools)}")

                # Log a preview of each tool's results
                for tool_name, result in tool_results.items():
                    result_preview = (
                        str(result)[:200] + "..."
                        if len(str(result)) > 200
                        else str(result)
                    )
                    logger.info(f"{tool_name} result preview: {result_preview}")
            else:
                logger.info("Processing query without any tool results")

            # Get chat history if session_id is provided
            chat_history = None
            if session_id:
                chat_history = self.memory_manager.get_chat_history_str(session_id)
                logger.info(f"Retrieved chat history for session {session_id}")

            # Initialize the state - context will be processed in retrieve_context
            initial_state: AgentState = {
                "query": query,
                "context": [],  # Empty context - will be filled by retrieve_context
                "tool_results": tool_results,
                "response": None,
                "error": None,
                "chat_history": chat_history,
            }

            # Run the graph
            result = self.graph.invoke(initial_state)

            # Save the conversation to memory if session_id is provided
            if session_id:
                # Add the user query to memory
                self.memory_manager.add_user_message(session_id, query)

                # Add the AI response to memory
                if result["response"]:
                    self.memory_manager.add_ai_message(session_id, result["response"])
                    logger.info(f"Updated conversation memory for session {session_id}")

            return {
                "query": query,
                "response": result["response"],
                "error": result["error"],
            }
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "query": query,
                "response": "I'm sorry, I encountered an error while processing your query.",
                "error": str(e),
            }
