#!/usr/bin/env python
"""
Test script for the natural language to SQL conversion.

This script tests the SQLQueryTool's ability to convert natural language queries to SQL queries.
"""

import asyncio
import json
import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tools.sql_query import SQLQueryTool

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Test database path - look in both the tests directory and the project root
TEST_DIR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_db.sqlite")
ROOT_DIR_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test_db.sqlite")

# Use the database file that exists
if os.path.exists(TEST_DIR_PATH):
    DB_PATH = TEST_DIR_PATH
elif os.path.exists(ROOT_DIR_PATH):
    DB_PATH = ROOT_DIR_PATH
else:
    DB_PATH = ROOT_DIR_PATH  # Default to root path if neither exists

# Test natural language queries
TEST_NL_QUERIES = [
    # Basic queries
    "Show me all staff members",
    "List the departments",
    "What is the budget for each department in 2023?",
    "Show me all laboratory facilities",
    
    # More complex queries
    "Who is the head of the Computer Science department?",
    "What is the total budget for all departments in 2023?",
    "Show me all staff members in the Computer Science department",
    "Which department has the highest budget in 2023?",
    
    # Queries with Turkish characters
    "Show me staff members with names containing Öztürk",
    "Find all staff members with Yılmaz in their name",
]


async def test_nl_to_sql_conversion():
    """Test the natural language to SQL conversion."""
    
    # Check if the test database exists
    if not os.path.exists(DB_PATH):
        logger.error(f"Test database not found at {DB_PATH}. Please run create_test_db.py first.")
        return False
    
    # Create a tool config
    tool_config = {
        "connection_string": f"sqlite:///{DB_PATH}",
        "max_results": 10,
        "allowed_tables": ["staff", "departments", "budgets", "facilities"],
        "model": "gpt-4.1-mini",
        "temperature": 0.0,
    }
    
    # Initialize the SQL query tool
    sql_tool = SQLQueryTool(tool_config)
    sql_tool.initialize()
    
    # Test each query
    success = True
    for i, query in enumerate(TEST_NL_QUERIES):
        logger.info(f"\n\n=== Testing natural language query {i+1}/{len(TEST_NL_QUERIES)} ===")
        logger.info(f"Query: {query}")
        
        # Execute the query
        result = await sql_tool.execute(query, use_llm=True)
        
        # Check if the query was successful
        if result["success"]:
            logger.info(f"Query successful!")
            logger.info(f"Generated SQL: {result['query']}")
            logger.info(f"LLM used: {result.get('llm_used', False)}")
            logger.info(f"Found {result['count']} results")
            
            # Print the column names
            logger.info(f"Columns: {', '.join(result['columns'])}")
            
            # Print a sample of the results if any were found
            if result["count"] > 0:
                logger.info(f"Sample result: {json.dumps(result['results'][0], indent=2)}")
        else:
            logger.error(f"Query failed: {result.get('error', 'Unknown error')}")
            success = False
    
    return success


async def main():
    """Main test function."""
    print("Testing Natural Language to SQL Conversion")
    print("=========================================")
    
    # Run the tests
    success = await test_nl_to_sql_conversion()
    
    if success:
        print("\nAll tests completed successfully!")
    else:
        print("\nSome tests failed. Check the logs for details.")


if __name__ == "__main__":
    asyncio.run(main())
