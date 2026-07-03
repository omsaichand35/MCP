from mcp.server.fastmcp import FastMCP

from executor import classify_query, execute_sql, explain_query
from ollama_client import generate_sql
from database import get_live_schema
from history import get_query_history
from validator import validate_sql

mcp = FastMCP("SQL generator")

@mcp.tool()
def generate_sql_query(question: str) -> str:
    """Converts the natural language query to SQL server query."""
    return generate_sql(question)

@mcp.tool()
def get_database_schema() -> dict:
    """Returns the database tables and columns."""
    return get_live_schema()

@mcp.tool()
def validate_generated_query(sql: str):
    """Validates the generated SQL query against the database."""
    return validate_sql(sql)

@mcp.tool()
def execute_query(sql: str):
    """Executes the generated SQL query against the database."""
    return execute_sql(sql)


@mcp.tool()
def classify_generated_query(sql: str) -> str:
    """Classifies the generated SQL query as READ, WRITE, OTHER, or UNKNOWN."""
    return classify_query(sql)


@mcp.tool()
def explain_query_tool(sql: str):
    """Explains the SQL query by listing tables, columns, and the query purpose."""
    return explain_query(sql)


@mcp.tool()
def get_query_history_tool(limit: int = 25):
    """Returns the most recent query history entries."""
    return get_query_history(limit)


if __name__ == "__main__":
    mcp.run()