"""
Memory manager for the Agentic RAG system.
Provides ephemeral conversation memory using Langchain's ConversationBufferMemory.
"""

import logging
from typing import Dict, List, Optional, Any
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain.memory import ConversationBufferMemory

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Memory manager for the Agentic RAG system.
    Provides ephemeral conversation memory using Langchain's ConversationBufferMemory.
    """

    def __init__(self):
        """Initialize the memory manager."""
        # Dictionary to store conversation memories by session_id
        self.memories: Dict[str, ConversationBufferMemory] = {}

    def get_memory(self, session_id: str) -> ConversationBufferMemory:
        """
        Get or create a memory for a session.

        Args:
            session_id: The session ID

        Returns:
            The conversation memory for the session
        """
        if session_id not in self.memories:
            logger.info(f"Creating new memory for session: {session_id}")
            self.memories[session_id] = ConversationBufferMemory(
                return_messages=True,
                memory_key="chat_history",
                input_key="query",
                output_key="response",
            )
        return self.memories[session_id]

    def add_user_message(self, session_id: str, message: str) -> None:
        """
        Add a user message to the conversation history.

        Args:
            session_id: The session ID
            message: The user message
        """
        memory = self.get_memory(session_id)
        memory.chat_memory.add_user_message(message)
        logger.debug(f"Added user message to session {session_id}: {message[:50]}...")

    def add_ai_message(self, session_id: str, message: str) -> None:
        """
        Add an AI message to the conversation history.

        Args:
            session_id: The session ID
            message: The AI message
        """
        memory = self.get_memory(session_id)
        memory.chat_memory.add_ai_message(message)
        logger.debug(f"Added AI message to session {session_id}: {message[:50]}...")

    def get_chat_history(self, session_id: str) -> List[BaseMessage]:
        """
        Get the chat history for a session.

        Args:
            session_id: The session ID

        Returns:
            The chat history as a list of messages
        """
        memory = self.get_memory(session_id)
        return memory.chat_memory.messages

    def get_chat_history_str(self, session_id: str) -> str:
        """
        Get the chat history for a session as a formatted string.

        Args:
            session_id: The session ID

        Returns:
            The chat history as a formatted string
        """
        messages = self.get_chat_history(session_id)
        if not messages:
            return ""

        history_str = ""
        for message in messages:
            if isinstance(message, HumanMessage):
                history_str += f"Human: {message.content}\n"
            elif isinstance(message, AIMessage):
                history_str += f"AI: {message.content}\n"
            else:
                history_str += f"{message.type}: {message.content}\n"

        return history_str

    def clear_memory(self, session_id: str) -> None:
        """
        Clear the memory for a session.

        Args:
            session_id: The session ID
        """
        if session_id in self.memories:
            logger.info(f"Clearing memory for session: {session_id}")
            del self.memories[session_id]
