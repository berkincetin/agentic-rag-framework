#!/usr/bin/env python
"""
Test script for the SQL query tool.

This script tests the SQLQueryTool with a sample SQLite database.
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
from app.models.bot_config import ToolConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Test database path - look in both the tests directory and the project root
TEST_DIR_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "test_db.sqlite"
)
ROOT_DIR_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test_db.sqlite"
)

# Use the database file that exists
if os.path.exists(TEST_DIR_PATH):
    DB_PATH = TEST_DIR_PATH
elif os.path.exists(ROOT_DIR_PATH):
    DB_PATH = ROOT_DIR_PATH
else:
    DB_PATH = ROOT_DIR_PATH  # Default to root path if neither exists

# Test SQL queries
TEST_QUERIES = [
    # Basic SELECT queries
    "SELECT * FROM staff LIMIT 3",
    "SELECT name, position FROM staff WHERE department_id = 1",
    "SELECT * FROM departments",
    "SELECT * FROM budgets WHERE fiscal_year = 2023",
    "SELECT * FROM facilities WHERE type = 'Laboratory'",
    # JOIN queries
    "SELECT s.name, d.name as department FROM staff s JOIN departments d ON s.department_id = d.id",
    "SELECT d.name, b.amount FROM departments d JOIN budgets b ON d.id = b.department_id WHERE b.fiscal_year = 2023",
    # Aggregate queries
    "SELECT department_id, COUNT(*) as staff_count FROM staff GROUP BY department_id",
    "SELECT fiscal_year, SUM(amount) as total_budget FROM budgets GROUP BY fiscal_year",
    # Complex queries
    """
    SELECT d.name as department, s.name as head, b.amount as budget
    FROM departments d
    JOIN staff s ON d.head_id = s.id
    JOIN budgets b ON d.budget_id = b.id
    WHERE b.fiscal_year = 2023
    ORDER BY b.amount DESC
    """,
]

# Test queries with Turkish characters
TEST_TURKISH_QUERIES = [
    # Simple queries with Turkish characters
    "SELECT * FROM staff WHERE name LIKE '%Öztürk%'",
    "SELECT * FROM staff WHERE name LIKE '%Yılmaz%'",
    "SELECT * FROM departments WHERE name = 'Bilgisayar Mühendisliği'",
]


async def test_sql_query_tool():
    """Test the SQL query tool with various queries."""

    # Check if the test database exists
    if not os.path.exists(DB_PATH):
        logger.error(
            f"Test database not found at {DB_PATH}. Please run create_test_db.py first."
        )
        return False

    # Create a tool config
    tool_config = {
        "connection_string": f"sqlite:///{DB_PATH}",
        "max_results": 10,
        "allowed_tables": ["staff", "departments", "budgets", "facilities"],
    }

    # Initialize the SQL query tool
    sql_tool = SQLQueryTool(tool_config)
    sql_tool.initialize()

    # Test each query
    success = True
    for i, query in enumerate(TEST_QUERIES):
        logger.info(f"\n\n=== Testing query {i+1}/{len(TEST_QUERIES)} ===")
        logger.info(f"Query: {query}")

        # Execute the query
        result = await sql_tool.execute("", sql_query=query)

        # Check if the query was successful
        if result["success"]:
            logger.info(f"Query successful!")
            logger.info(f"Found {result['count']} results")

            # Print the column names
            logger.info(f"Columns: {', '.join(result['columns'])}")

            # Print a sample of the results if any were found
            if result["count"] > 0:
                logger.info(
                    f"Sample result: {json.dumps(result['results'][0], indent=2)}"
                )
        else:
            logger.error(f"Query failed: {result.get('error', 'Unknown error')}")
            success = False

    # Test Turkish queries if there are any
    for i, query in enumerate(TEST_TURKISH_QUERIES):
        logger.info(
            f"\n\n=== Testing Turkish query {i+1}/{len(TEST_TURKISH_QUERIES)} ==="
        )
        logger.info(f"Query: {query}")

        # Execute the query
        result = await sql_tool.execute("", sql_query=query)

        # Check if the query was successful
        if result["success"]:
            logger.info(f"Query successful!")
            logger.info(f"Found {result['count']} results")

            # Print the column names
            logger.info(f"Columns: {', '.join(result['columns'])}")

            # Print a sample of the results if any were found
            if result["count"] > 0:
                logger.info(
                    f"Sample result: {json.dumps(result['results'][0], indent=2)}"
                )
        else:
            logger.error(f"Query failed: {result.get('error', 'Unknown error')}")
            success = False

    return success


async def main():
    """Main test function."""
    print("Testing SQL Query Tool")
    print("=====================")

    # Run the tests
    success = await test_sql_query_tool()

    if success:
        print("\nAll tests completed successfully!")
    else:
        print("\nSome tests failed. Check the logs for details.")


if __name__ == "__main__":
    asyncio.run(main())
