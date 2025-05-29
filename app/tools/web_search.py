"""
Web search tool for the Agentic RAG system using TavilySearch API.
"""
import logging
import os
from typing import Any, Dict, List, Optional

from tavily import TavilyClient

from app.tools.base import BaseTool

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """Tool for searching the web using TavilySearch API."""
    
    def initialize(self) -> None:
        """Initialize the web search tool."""
        self.api_key = self.config.get("api_key", os.getenv("TAVILY_API_KEY"))
        self.search_depth = self.config.get("search_depth", "basic")  # basic or comprehensive
        self.max_results = self.config.get("max_results", 5)
        self.include_domains = self.config.get("include_domains", [])
        self.exclude_domains = self.config.get("exclude_domains", [])
        
        # Initialize TavilyClient
        if not self.api_key:
            logger.error("Tavily API key not provided")
            self.client = None
        else:
            try:
                self.client = TavilyClient(api_key=self.api_key)
                logger.info("Initialized web search tool with TavilySearch API")
            except Exception as e:
                logger.error(f"Error initializing TavilySearch client: {str(e)}")
                self.client = None
    
    async def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Search the web for information related to the query.
        
        Args:
            query: The user query
            **kwargs: Additional arguments
                - max_results: Maximum number of results to return (optional)
                - search_depth: Search depth (basic or comprehensive) (optional)
            
        Returns:
            A dictionary containing the search results
        """
        if not self.client:
            return {
                "success": False,
                "error": "TavilySearch client not initialized",
                "results": []
            }
        
        try:
            # Get search parameters
            max_results = kwargs.get("max_results", self.max_results)
            search_depth = kwargs.get("search_depth", self.search_depth)
            
            # Execute the search
            response = self.client.search(
                query=query,
                search_depth=search_depth,
                max_results=max_results,
                include_domains=self.include_domains or None,
                exclude_domains=self.exclude_domains or None
            )
            
            # Extract and format the results
            results = response.get("results", [])
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            logger.error(f"Error executing web search: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    @classmethod
    def get_tool_description(cls) -> str:
        return "Searches the web for information using the TavilySearch API."
