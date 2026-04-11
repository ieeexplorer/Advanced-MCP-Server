"""Enterprise-grade MCP Server with advanced features."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from loguru import logger
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from src.storage.database import DatabaseManager
from src.storage.models import TaskCreate, TaskUpdate, NoteCreate
from src.tools import calculator_tools, task_tools, note_tools, advanced_tools
from src.resources import data_resources
from src.prompts import templates
from src.utils.logging_config import setup_logging
from src.utils.middleware import (
    performance_middleware,
    error_handler_middleware,
    auth_middleware,
)
from src.utils.validators import validate_input

# Configuration
from src.config import settings

setup_logging(settings.log_level)


class ServerContext:
    """Context manager for server resources."""
    
    def __init__(self):
        self.db: Optional[DatabaseManager] = None
        self.cache = None  # Add Redis cache here
        
    async def initialize(self):
        """Initialize database connections and external services."""
        logger.info("Initializing server resources...")
        self.db = DatabaseManager(settings.database_url)
        await self.db.initialize()
        logger.success("Server initialized successfully")
    
    async def cleanup(self):
        """Cleanup resources on shutdown."""
        logger.info("Cleaning up server resources...")
        if self.db:
            await self.db.close()
        logger.success("Cleanup complete")


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[ServerContext]:
    """Manage server startup and shutdown lifecycle."""
    context = ServerContext()
    try:
        await context.initialize()
        yield context
    finally:
        await context.cleanup()


# Create MCP server instance
mcp = FastMCP(
    "Farshad Enterprise MCP Server",
    lifespan=server_lifespan,
)


# Register calculator tools
@mcp.tool()
@performance_middleware
@error_handler_middleware
@validate_input
async def add(a: float, b: float) -> float:
    """
    Add two numbers with precision handling.
    
    Args:
        a: First number
        b: Second number
    
    Returns:
        Sum of a and b
    """
    result = await calculator_tools.add_with_precision(a, b)
    logger.debug(f"Addition: {a} + {b} = {result}")
    return result


@mcp.tool()
@performance_middleware
@error_handler_middleware
async def calculate_batch(expression: str) -> float:
    """
    Calculate complex mathematical expressions.
    
    Supports: +, -, *, /, **, sqrt, sin, cos, log
    
    Args:
        expression: Mathematical expression to evaluate
    
    Returns:
        Calculated result
    """
    return await calculator_tools.evaluate_expression(expression)


# Register task management tools
@mcp.tool()
@error_handler_middleware
@auth_middleware(required_role="user")
async def create_task(task: TaskCreate) -> dict:
    """
    Create a new task with full metadata support.
    
    Args:
        task: Task creation object with title, priority, due_date, tags, assignee
    
    Returns:
        Created task with unique ID and timestamps
    """
    ctx = mcp.request_context.lifespan_context
    return await task_tools.create_task(ctx.db, task)


@mcp.tool()
@error_handler_middleware
async def query_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    tags: Optional[list[str]] = None,
    assignee: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """
    Advanced task query with filtering and pagination.
    
    Args:
        status: Filter by status (pending, in_progress, completed, archived)
        priority: Filter by priority (low, medium, high, critical)
        tags: Filter by tags (AND logic)
        assignee: Filter by assignee name
        limit: Maximum number of tasks to return (1-100)
        offset: Number of tasks to skip for pagination
    
    Returns:
        List of matching tasks
    """
    ctx = mcp.request_context.lifespan_context
    return await task_tools.query_tasks(ctx.db, status, priority, tags, assignee, limit, offset)


@mcp.tool()
@error_handler_middleware
async def generate_task_report(
    start_date: str,
    end_date: str,
    group_by: str = "status",
) -> dict:
    """
    Generate analytical report on tasks.
    
    Args:
        start_date: ISO format start date (YYYY-MM-DD)
        end_date: ISO format end date (YYYY-MM-DD)
        group_by: Group by field (status, priority, assignee, day)
    
    Returns:
        Report with statistics, trends, and insights
    """
    ctx = mcp.request_context.lifespan_context
    return await task_tools.generate_report(ctx.db, start_date, end_date, group_by)


# Register note management tools
@mcp.tool()
@error_handler_middleware
async def create_note(note: NoteCreate) -> dict:
    """
    Create a rich-text note with metadata.
    
    Args:
        note: Note object with title, content, tags, and optional folder
    
    Returns:
        Created note with ID and timestamps
    """
    ctx = mcp.request_context.lifespan_context
    return await note_tools.create_note(ctx.db, note)


@mcp.tool()
@error_handler_middleware
async def semantic_search(query: str, limit: int = 10) -> list[dict]:
    """
    AI-powered semantic search across notes and tasks.
    
    Uses embeddings to find semantically similar content.
    
    Args:
        query: Search query
        limit: Maximum results to return
    
    Returns:
        List of relevant items with relevance scores
    """
    ctx = mcp.request_context.lifespan_context
    return await advanced_tools.semantic_search(ctx.db, query, limit)


# Register advanced tools
@mcp.tool()
@error_handler_middleware
async def export_data(format: str = "json", start_date: Optional[str] = None) -> str:
    """
    Export all data in various formats.
    
    Args:
        format: Export format (json, csv, markdown)
        start_date: Optional start date filter
    
    Returns:
        Exported data as string
    """
    ctx = mcp.request_context.lifespan_context
    return await advanced_tools.export_all_data(ctx.db, format, start_date)


@mcp.tool()
@error_handler_middleware
async def create_backup() -> dict:
    """
    Create a full backup of all server data.
    
    Returns:
        Backup information including location and size
    """
    return await advanced_tools.create_backup()


# Register resources
@mcp.resource("stats://summary")
async def get_statistics() -> str:
    """Get real-time server statistics and metrics."""
    ctx = mcp.request_context.lifespan_context
    stats = await data_resources.get_server_stats(ctx.db)
    return json.dumps(stats, indent=2)


@mcp.resource("export://{format}")
async def export_resource(format: str) -> str:
    """Resource endpoint for data export."""
    return await export_data(format)


# Register prompts
@mcp.prompt()
async def code_review_with_context(code: str, language: str = "python") -> str:
    """Enhanced code review prompt with language-specific guidance."""
    return await templates.code_review_prompt(code, language)


@mcp.prompt()
async def task_analysis_prompt(task_ids: list[str]) -> str:
    """Generate analysis prompt for specific tasks."""
    ctx = mcp.request_context.lifespan_context
    return await templates.task_analysis(ctx.db, task_ids)


def main() -> None:
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()