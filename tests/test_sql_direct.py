#!/usr/bin/env python
"""
Direct test of the SQL tool with the test database.
"""

import asyncio
import json
import logging
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tools.sql_query import SQLQueryTool

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Test database path
TEST_DB_PATH = os.path.abspath("test_db.sqlite")


async def test_sql_direct():
    """Test the SQL tool directly."""
    # Check if the test database exists
    if not os.path.exists(TEST_DB_PATH):
        logger.error(f"Test database not found at {TEST_DB_PATH}")
        return False
    
    # Create a tool config
    tool_config = {
        "connection_string": f"sqlite:///{TEST_DB_PATH}",
        "max_results": 10,
        "allowed_tables": ["staff", "departments", "budgets", "facilities"]
    }
    
    # Initialize the SQL query tool
    sql_tool = SQLQueryTool(tool_config)
    sql_tool.initialize()
    
    # Test a direct SQL query
    sql_query = "SELECT * FROM staff WHERE department_id = 1"
    logger.info(f"Executing SQL query: {sql_query}")
    
    result = await sql_tool.execute("", sql_query=sql_query)
    
    if result["success"]:
        logger.info(f"Query successful!")
        logger.info(f"Found {result['count']} results")
        logger.info(f"Columns: {result['columns']}")
        
        # Check if columns is JSON serializable
        try:
            json_str = json.dumps(result["columns"])
            logger.info(f"Columns are JSON serializable: {json_str}")
        except Exception as e:
            logger.error(f"Columns are NOT JSON serializable: {str(e)}")
            return False
        
        if result["count"] > 0:
            # Check if results are JSON serializable
            try:
                json_str = json.dumps(result["results"])
                logger.info(f"Results are JSON serializable")
            except Exception as e:
                logger.error(f"Results are NOT JSON serializable: {str(e)}")
                return False
            
            logger.info(f"Results: {json.dumps(result['results'], indent=2)}")
    else:
        logger.error(f"Query failed: {result.get('error', 'Unknown error')}")
        return False
    
    return True


async def main():
    """Main function."""
    print("Direct SQL Tool Test")
    print("===================")
    
    success = await test_sql_direct()
    
    if success:
        print("\nAll tests completed successfully!")
    else:
        print("\nTests failed. Check the logs for details.")


if __name__ == "__main__":
    asyncio.run(main())
