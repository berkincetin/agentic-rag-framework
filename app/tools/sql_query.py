"""
SQL query tool for the Agentic RAG system.
"""

import logging
import json
import os
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.tools.base import BaseTool

logger = logging.getLogger(__name__)


class SQLQueryTool(BaseTool):
    """Tool for querying SQL databases."""

    def initialize(self) -> None:
        """Initialize the SQL query tool."""
        self.connection_string = self.config.get(
            "connection_string", "sqlite:///default.db"
        )
        self.max_results = self.config.get("max_results", 100)
        self.allowed_tables = self.config.get("allowed_tables", [])
        self.model_name = self.config.get("model", "gpt-4.1-mini")
        self.temperature = self.config.get("temperature", 0.0)

        # Initialize SQLAlchemy engine
        try:
            self.engine = create_engine(self.connection_string)
            logger.info(
                f"Initialized SQL query tool with connection: {self.connection_string}"
            )

            # Get table schemas for better query generation
            self.table_schemas = self._get_table_schemas()
        except SQLAlchemyError as e:
            logger.error(f"Error connecting to SQL database: {str(e)}")
            self.engine = None
            self.table_schemas = {}

        # Initialize LLM for query conversion
        try:
            self.llm = ChatOpenAI(model=self.model_name, temperature=self.temperature)
            logger.info(f"Initialized LLM for SQL query conversion: {self.model_name}")
        except Exception as e:
            logger.error(f"Error initializing LLM: {str(e)}")
            self.llm = None

    async def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a SQL query.

        Args:
            query: The user query (will be processed to extract SQL query)
            **kwargs: Additional arguments
                - sql_query: The SQL query to execute (optional)
                - max_results: Maximum number of results to return (optional)
                - use_llm: Whether to use LLM for query conversion (default: True)

        Returns:
            A dictionary containing the query results
        """
        if not self.engine:
            return {
                "success": False,
                "error": "SQL engine not initialized",
                "results": [],
            }

        try:
            # Get the SQL query to execute
            sql_query = kwargs.get("sql_query")
            use_llm = kwargs.get("use_llm", True)

            # If no SQL query is provided, try to convert natural language to SQL
            if not sql_query and use_llm and self.llm is not None:
                logger.info(f"Converting natural language to SQL query: {query}")
                conversion_result = await self._convert_nl_to_sql_query(query)

                if conversion_result["success"]:
                    sql_query = conversion_result["sql_query"]
                    logger.info(f"LLM generated SQL query: {sql_query}")
                else:
                    logger.warning(
                        f"LLM conversion failed: {conversion_result.get('error', 'Unknown error')}"
                    )

            # If we still don't have a SQL query, return an error
            if not sql_query:
                return {
                    "success": False,
                    "error": "Could not generate SQL query from natural language",
                    "results": [],
                }

            # Get the maximum number of results to return
            max_results = kwargs.get("max_results", self.max_results)

            # Execute the query
            with self.engine.connect() as connection:
                result = connection.execute(text(sql_query))

                # Get column names and convert to list for JSON serialization
                columns = list(result.keys())

                # Get results
                rows = result.fetchmany(max_results)

                # Format the results
                results = []
                for row in rows:
                    results.append(dict(zip(columns, row)))

            return {
                "success": True,
                "query": sql_query,
                "results": results,
                "count": len(results),
                "columns": columns,
                "llm_used": use_llm
                and self.llm is not None
                and not kwargs.get("sql_query"),
            }
        except SQLAlchemyError as e:
            logger.error(f"Error executing SQL query: {str(e)}")
            return {"success": False, "error": str(e), "results": []}

    def _get_table_schemas(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the schema information for all tables in the database.

        Returns:
            A dictionary mapping table names to their schema information
        """
        if not self.engine:
            logger.error("Cannot get table schemas: SQL engine not initialized")
            return {}

        try:
            inspector = inspect(self.engine)
            schemas = {}

            # Get all table names
            table_names = inspector.get_table_names()

            # Filter tables if allowed_tables is specified
            if self.allowed_tables:
                table_names = [t for t in table_names if t in self.allowed_tables]

            # Get schema for each table
            for table_name in table_names:
                columns = []
                for column in inspector.get_columns(table_name):
                    columns.append(
                        {
                            "name": column["name"],
                            "type": str(column["type"]),
                            "nullable": column.get("nullable", True),
                        }
                    )

                # Get primary key information
                pk_columns = inspector.get_pk_constraint(table_name).get(
                    "constrained_columns", []
                )

                # Get foreign key information
                foreign_keys = []
                for fk in inspector.get_foreign_keys(table_name):
                    foreign_keys.append(
                        {
                            "referred_table": fk["referred_table"],
                            "referred_columns": fk["referred_columns"],
                            "constrained_columns": fk["constrained_columns"],
                        }
                    )

                schemas[table_name] = {
                    "columns": columns,
                    "primary_key": pk_columns,
                    "foreign_keys": foreign_keys,
                }

            logger.info(f"Retrieved schema information for {len(schemas)} tables")
            return schemas
        except SQLAlchemyError as e:
            logger.error(f"Error getting table schemas: {str(e)}")
            return {}

    async def _convert_nl_to_sql_query(self, query: str) -> Dict[str, Any]:
        """
        Convert natural language query to SQL query using LLM.

        Args:
            query: The natural language query

        Returns:
            A dictionary containing the SQL query and status
        """
        if self.llm is None:
            logger.warning(
                "LLM not initialized, cannot convert natural language to SQL"
            )
            return {
                "success": False,
                "error": "LLM not initialized",
                "sql_query": None,
            }

        try:
            # Format table schemas for the prompt
            schema_str = ""
            for table_name, schema in self.table_schemas.items():
                schema_str += f"Table: {table_name}\n"
                schema_str += "Columns:\n"

                for column in schema["columns"]:
                    pk_marker = (
                        " (Primary Key)"
                        if column["name"] in schema["primary_key"]
                        else ""
                    )
                    schema_str += f"  - {column['name']}: {column['type']}{pk_marker}\n"

                if schema["foreign_keys"]:
                    schema_str += "Foreign Keys:\n"
                    for fk in schema["foreign_keys"]:
                        schema_str += f"  - {', '.join(fk['constrained_columns'])} -> {fk['referred_table']}({', '.join(fk['referred_columns'])})\n"

                schema_str += "\n"

            # Create the prompt template
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """
                You are an expert in converting natural language queries to SQL queries.
                Your task is to convert the user's natural language query into a valid SQL query.

                Database schema information:
                {schema_info}

                Guidelines:
                1. Return ONLY the SQL query without any explanations or markdown formatting
                2. Use appropriate SQL syntax based on the query
                3. Support both English and Turkish language queries
                4. Use appropriate JOINs when querying across multiple tables
                5. Use appropriate WHERE clauses to filter results
                6. If the query is ambiguous, create a reasonable query that would return relevant results
                7. Do not include any explanation, just return the SQL query
                8. Make sure to handle Turkish characters properly
                9. Use LIKE with % wildcards for partial text matching
                10. Limit results to a reasonable number (e.g., LIMIT 10) for queries that might return many rows
                """,
                    ),
                    (
                        "user",
                        "Convert this natural language query to a SQL query: {query}",
                    ),
                ]
            )

            # Generate the SQL query
            messages = prompt.format_messages(query=query, schema_info=schema_str)
            response = self.llm.invoke(messages)
            response_text = response.content.strip()

            # Try to extract SQL from the response
            if (
                "```sql" in response_text
                and "```" in response_text.split("```sql", 1)[1]
            ):
                sql_query = (
                    response_text.split("```sql", 1)[1].split("```", 1)[0].strip()
                )
            elif "```" in response_text and "```" in response_text.split("```", 1)[1]:
                sql_query = response_text.split("```", 1)[1].split("```", 1)[0].strip()
            else:
                sql_query = response_text

            # Clean up the SQL query
            sql_query = sql_query.strip()
            if sql_query.startswith("`") and sql_query.endswith("`"):
                sql_query = sql_query[1:-1]

            logger.info(f"LLM generated SQL query: {sql_query}")
            return {
                "success": True,
                "sql_query": sql_query,
            }
        except Exception as e:
            logger.error(f"Error converting query with LLM: {str(e)}")
            return {
                "success": False,
                "error": f"Error using LLM: {str(e)}",
                "sql_query": None,
            }

    @classmethod
    def get_tool_description(cls) -> str:
        return (
            "Executes SQL queries against relational databases to retrieve information. "
            "Uses an LLM to convert natural language queries to SQL queries for more accurate results."
        )
