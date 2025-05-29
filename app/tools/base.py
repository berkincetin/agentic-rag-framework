"""
Base tool interface for the Agentic RAG system.
All tools must implement this interface.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseTool(ABC):
    """Base class for all tools in the Agentic RAG system."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the tool with configuration.
        
        Args:
            config: Tool-specific configuration dictionary
        """
        self.config = config
        self.name = self.__class__.__name__
        self.initialize()
    
    def initialize(self) -> None:
        """
        Initialize the tool with the provided configuration.
        Override this method to perform tool-specific initialization.
        """
        pass
    
    @abstractmethod
    async def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with the given query.
        
        Args:
            query: The user query or a processed version of it
            **kwargs: Additional arguments specific to the tool
            
        Returns:
            A dictionary containing the tool's response
        """
        pass
    
    @classmethod
    def get_tool_description(cls) -> str:
        """
        Get a description of what this tool does.
        
        Returns:
            A string describing the tool's functionality
        """
        return cls.__doc__ or "No description available"
