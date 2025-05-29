#!/usr/bin/env python
"""
Test script for the LLM-based MongoDB query conversion.

This script demonstrates how the MongoDBQueryTool converts natural language queries
to MongoDB queries using an LLM.
"""

import asyncio
import json
import logging
import sys
import os
from dotenv import load_dotenv
from app.tools.mongodb_query import MongoDBQueryTool
from app.models.bot_config import ToolConfig

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Test queries in English and Turkish
TEST_QUERIES = [
    "Find all documents about artificial intelligence",
    "Show me documents with page content containing the word 'university'",
    "Get documents where the metadata field 'source' contains 'research paper'",
    "Find documents from 2023 about machine learning",
    "Yapay zeka hakkında tüm belgeleri bul",  # Turkish: Find all documents about artificial intelligence
    "Üniversite kelimesini içeren belgeleri göster",  # Turkish: Show documents containing the word university
]


async def test_mongodb_llm_query():
    """Test the LLM-based MongoDB query conversion."""

    # Create a tool config
    tool_config = {
        "connection_string": "mongodb://localhost:27017/",
        "database_name": "vector_db",
        "default_collection": "usul_ve_esaslar-rag-chroma",
        "max_results": 5,
        "model": "gpt-4.1-mini",
        "temperature": 0.0,
    }

    # Initialize the MongoDB query tool
    mongodb_tool = MongoDBQueryTool(
        ToolConfig(type="MongoDBQueryTool", enabled=True, config=tool_config)
    )
    mongodb_tool.initialize()

    # Test each query
    for query in TEST_QUERIES:
        logger.info(f"\n\n=== Testing query: {query} ===")

        # Execute the query with LLM conversion
        result = await mongodb_tool.execute(query, use_llm=True)

        # Print the results
        if result["success"]:
            logger.info(f"LLM used: {result.get('llm_used', False)}")
            logger.info(f"MongoDB query: {json.dumps(result['query'], indent=2)}")
            logger.info(f"Found {result['count']} results")

            # Print a sample of the results if any were found
            if result["count"] > 0:
                sample = result["results"][0]
                logger.info(
                    f"Sample result: {json.dumps({k: sample[k] for k in ['_id'] if k in sample}, indent=2)}"
                )
                if "page_content" in sample:
                    content_preview = (
                        sample["page_content"][:100] + "..."
                        if len(sample["page_content"]) > 100
                        else sample["page_content"]
                    )
                    logger.info(f"Content preview: {content_preview}")
        else:
            logger.error(f"Query failed: {result.get('error', 'Unknown error')}")

        # Also test without LLM for comparison
        fallback_result = await mongodb_tool.execute(query, use_llm=False)
        if fallback_result["success"]:
            logger.info(
                f"Fallback query: {json.dumps(fallback_result['query'], indent=2)}"
            )
            logger.info(f"Fallback found {fallback_result['count']} results")

        # Add a separator between queries
        logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_mongodb_llm_query())
