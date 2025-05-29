"""
MongoDB query tool for the Agentic RAG system.
"""

import logging
import json
from bson import ObjectId
from typing import Any, Dict, List, Optional

import pymongo
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.tools.base import BaseTool

logger = logging.getLogger(__name__)


class MongoDBQueryTool(BaseTool):
    """Tool for querying MongoDB databases."""

    def initialize(self) -> None:
        """Initialize the MongoDB query tool."""
        self.connection_string = self.config.get(
            "connection_string", "mongodb://localhost:27017/"
        )
        self.database_name = self.config.get("database_name", "default")
        self.default_collection = self.config.get("default_collection", "documents")
        self.max_results = self.config.get("max_results", 10)
        self.model_name = self.config.get("model", "gpt-4.1-mini")
        self.temperature = self.config.get("temperature", 0.0)

        # Initialize MongoDB client
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]
            logger.info(
                f"Initialized MongoDB query tool for database: {self.database_name}"
            )
        except PyMongoError as e:
            logger.error(f"Error connecting to MongoDB: {str(e)}")
            self.client = None
            self.db = None

        # Initialize LLM for query conversion
        try:
            self.llm = ChatOpenAI(model=self.model_name, temperature=self.temperature)
            logger.info(
                f"Initialized LLM for MongoDB query conversion: {self.model_name}"
            )
        except Exception as e:
            logger.error(f"Error initializing LLM: {str(e)}")
            self.llm = None

    async def _convert_nl_to_mongodb_query(
        self, query: str, collection_name: str
    ) -> Dict[str, Any]:
        """
        Convert natural language query to MongoDB query using LLM.

        Args:
            query: The natural language query
            collection_name: The name of the collection to query

        Returns:
            A dictionary containing the MongoDB query and status
        """
        if self.llm is None:
            logger.warning("LLM not initialized, using fallback query")
            return {
                "success": False,
                "error": "LLM not initialized",
                "query_json": f'{{"$text": {{"$search": "{query}"}}}}',
            }

        try:
            # Get collection schema/structure
            collection_info = self._get_collection_info(collection_name)

            # Create the prompt template
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """
                        You are an expert in converting natural language queries to MongoDB queries.
                        Your task is to convert the user's natural language query into a valid MongoDB query in JSON format.

                        Collection information:
                        {collection_info}

                        Guidelines:
                        1. Return ONLY the MongoDB query in valid JSON format without any explanations or markdown formatting
                        2. Use appropriate MongoDB operators ($eq, $gt, $lt, $in, $regex, etc.) based on the query
                        3. Support both English and Turkish language queries
                        4. For text search, use $text and $search operators when appropriate
                        5. For partial matching, use $regex with case insensitivity
                        6. If the query is ambiguous, create a reasonable query that would return relevant results
                        7. Do not include any explanation, just return the JSON query
                        """,
                    ),
                    (
                        "user",
                        "Convert this natural language query to a MongoDB query for the collection: {query}",
                    ),
                ]
            )

            # Generate the MongoDB query
            messages = prompt.format_messages(
                query=query, collection_info=collection_info
            )
            response = self.llm.invoke(messages)
            response_text = response.content.strip()

            # Try to extract JSON from the response
            if (
                "```json" in response_text
                and "```" in response_text.split("```json", 1)[1]
            ):
                json_str = (
                    response_text.split("```json", 1)[1].split("```", 1)[0].strip()
                )
            elif "```" in response_text and "```" in response_text.split("```", 1)[1]:
                json_str = response_text.split("```", 1)[1].split("```", 1)[0].strip()
            else:
                json_str = response_text

            # Clean up the JSON string
            json_str = json_str.strip()
            if json_str.startswith("`") and json_str.endswith("`"):
                json_str = json_str[1:-1]

            # Parse the JSON
            try:
                mongo_query = json.loads(json_str)
                return {"success": True, "query_json": json_str, "query": mongo_query}
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing LLM response as JSON: {str(e)}")
                logger.error(f"Raw response: {response_text}")
                return {
                    "success": False,
                    "error": f"Invalid JSON in LLM response: {str(e)}",
                    "query_json": f'{{"$text": {{"$search": "{query}"}}}}',
                }

        except Exception as e:
            logger.error(f"Error converting query with LLM: {str(e)}")
            return {
                "success": False,
                "error": f"Error using LLM: {str(e)}",
                "query_json": f'{{"$text": {{"$search": "{query}"}}}}',
            }

    def _get_collection_info(self, collection_name: str) -> str:
        """
        Get information about the collection structure.

        Args:
            collection_name: The name of the collection

        Returns:
            A string containing information about the collection
        """
        try:
            if self.db is None:
                return "Collection information not available"

            collection = self.db[collection_name]

            # Get a sample document to infer schema
            sample_doc = collection.find_one()
            if not sample_doc:
                return f"Collection '{collection_name}' exists but is empty"

            # Format the sample document
            sample_doc_str = json.dumps(
                self._convert_objectid_to_str(sample_doc), indent=2
            )

            # Get collection stats
            stats = self.db.command("collStats", collection_name)
            doc_count = stats.get("count", 0)

            return f"""
            Collection name: {collection_name}
            Document count: {doc_count}
            Sample document structure:
            {sample_doc_str}
            """
        except Exception as e:
            logger.error(f"Error getting collection info: {str(e)}")
            return f"Error getting collection info: {str(e)}"

    def _convert_objectid_to_str(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert ObjectId to string for JSON serialization.

        Args:
            doc: The document to convert

        Returns:
            The converted document
        """
        if not isinstance(doc, dict):
            return doc
        result = {}
        for key, value in doc.items():
            try:
                if isinstance(value, ObjectId):
                    result[key] = str(value)
                elif isinstance(value, dict):
                    result[key] = self._convert_objectid_to_str(value)
                elif isinstance(value, list):
                    result[key] = [
                        (
                            self._convert_objectid_to_str(item)
                            if isinstance(item, dict)
                            else item
                        )
                        for item in value
                    ]
                else:
                    result[key] = value
            except Exception as e:
                logger.error(f"Error converting field '{key}': {e}")
                result[key] = value  # If there is an error, put the original value
        return result

        # result = {}
        # for key, value in doc.items():
        #     if isinstance(value, ObjectId):
        #         result[key] = str(value)
        #     elif isinstance(value, dict):
        #         result[key] = self._convert_objectid_to_str(value)
        #     elif isinstance(value, list):
        #         result[key] = [
        #             (
        #                 self._convert_objectid_to_str(item)
        #                 if isinstance(item, dict)
        #                 else item
        #             )
        #             for item in value
        #         ]
        #     else:
        #         result[key] = value
        # return result

    async def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a query against MongoDB.

        Args:
            query: The user query (will be processed to extract MongoDB query)
            **kwargs: Additional arguments
                - collection: The collection to query (optional)
                - query_json: JSON string representing the MongoDB query (optional)
                - max_results: Maximum number of results to return (optional)
                - use_llm: Whether to use LLM for query conversion (default: True)

        Returns:
            A dictionary containing the query results
        """
        if self.db is None:
            return {
                "success": False,
                "error": "MongoDB client not initialized",
                "results": [],
            }

        try:
            # Get the collection to query
            collection_name = kwargs.get("collection", self.default_collection)
            collection = self.db[collection_name]

            # Get the query to execute
            query_json = kwargs.get("query_json")
            use_llm = kwargs.get("use_llm", True)

            if not query_json and use_llm and self.llm is not None:
                # Use LLM to convert natural language to MongoDB query
                logger.info(f"Converting query to MongoDB query using LLM: {query}")
                conversion_result = await self._convert_nl_to_mongodb_query(
                    query, collection_name
                )

                if conversion_result["success"]:
                    query_json = conversion_result["query_json"]
                    logger.info(f"LLM generated MongoDB query: {query_json}")
                else:
                    logger.warning(
                        f"LLM conversion failed: {conversion_result['error']}"
                    )
                    query_json = conversion_result["query_json"]
            elif not query_json:
                # Fallback to simple text search if LLM is not available or disabled
                logger.info("Using fallback query method")
                query_json = f'{{"$text": {{"$search": "{query}"}}}}'

            # Parse the query JSON
            try:
                mongo_query = json.loads(query_json)
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": f"Invalid query JSON: {query_json}",
                    "results": [],
                }

            # Get the maximum number of results to return
            max_results = kwargs.get("max_results", self.max_results)

            # Execute the query
            cursor = collection.find(mongo_query).limit(max_results)

            # Format the results
            results = []
            for doc in cursor:
                if "_id" not in doc:
                    logger.warning(f"Document without _id found: {doc}")
                # Convert ObjectId to string for JSON serialization
                results.append(self._convert_objectid_to_str(doc))

            # Log the results
            result_count = len(results)
            logger.info(f"MongoDB query returned {result_count} results")

            if result_count > 0:
                # Log a sample of the first result (limited to avoid huge logs)
                sample_result = results[0]
                log_sample = {}

                # Always include _id if available
                if "_id" in sample_result:
                    log_sample["_id"] = sample_result["_id"]

                # Include page_content with truncation if it exists
                if "page_content" in sample_result:
                    content = sample_result["page_content"]
                    log_sample["page_content"] = (
                        (content[:200] + "...") if len(content) > 200 else content
                    )

                # Include metadata if it exists
                if "metadata" in sample_result:
                    log_sample["metadata"] = sample_result["metadata"]

                logger.info(
                    f"Sample result: {json.dumps(log_sample, ensure_ascii=False, indent=2)}"
                )

                # Log full results at debug level for detailed troubleshooting
                logger.debug(f"Full results: {json.dumps(results, ensure_ascii=False)}")
            else:
                logger.info("No results found for the query")

            return {
                "success": True,
                "collection": collection_name,
                "query": mongo_query,
                "query_json": query_json,
                "results": results,
                "count": result_count,
                "llm_used": use_llm and self.llm is not None,
            }
        except PyMongoError as e:
            logger.error(f"Error executing MongoDB query: {str(e)}")
            return {"success": False, "error": str(e), "results": []}

    @classmethod
    def get_tool_description(cls) -> str:
        return (
            "Queries MongoDB databases to retrieve information based on user queries. "
            "Uses an LLM to convert natural language queries to MongoDB queries for more accurate results."
        )
