"""
Document search tool for the Agentic RAG system.
"""

import logging
from typing import Any, Dict, List, Optional

from langchain_community.vectorstores import VectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_chroma import Chroma

from app.tools.base import BaseTool

logger = logging.getLogger(__name__)


class DocumentSearchTool(BaseTool):
    """Tool for searching documents using vector embeddings."""

    def initialize(self) -> None:
        """Initialize the document search tool."""
        self.collection_name = self.config.get("collection_name", "default")
        self.embedding_model = self.config.get(
            "embedding_model", "text-embedding-3-small"
        )
        self.persist_directory = self.config.get("persist_directory", "./chroma_db")
        self.top_k = self.config.get("top_k", 5)

        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(model=self.embedding_model)

        # Initialize vector store
        try:
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory,
            )
            logger.info(
                f"Initialized document search tool with collection: {self.collection_name}"
            )
        except Exception as e:
            logger.error(f"Error initializing vector store: {str(e)}")
            self.vector_store = None

    async def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Search for documents relevant to the query.

        Args:
            query: The user query
            **kwargs: Additional arguments

        Returns:
            A dictionary containing the search results
        """
        if not self.vector_store:
            return {
                "success": False,
                "error": "Vector store not initialized",
                "documents": [],
            }

        try:
            # Get the number of documents to return
            top_k = kwargs.get("top_k", self.top_k)

            # Search for documents
            docs = self.vector_store.similarity_search(query, k=top_k)

            # Format the results
            results = []
            for doc in docs:
                results.append({"content": doc.page_content, "metadata": doc.metadata})

            return {"success": True, "documents": results, "count": len(results)}
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return {"success": False, "error": str(e), "documents": []}

    @classmethod
    def get_tool_description(cls) -> str:
        return "Searches for documents relevant to a query using vector embeddings."
