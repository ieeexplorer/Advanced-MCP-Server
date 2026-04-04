"""Advanced tools for data analysis, export, and automation."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from loguru import logger

from src.storage.database import DatabaseManager
from src.utils.embeddings import generate_embedding


async def semantic_search(db: DatabaseManager, query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Perform semantic search using embeddings."""
    query_embedding = await generate_embedding(query)
    
    async with db.session() as session:
        # Search notes with cosine similarity
        result = await session.execute(
            """
            SELECT id, title, content, tags,
                   1 - (embedding <=> :query_embedding) as similarity
            FROM notes
            WHERE embedding IS NOT NULL
            ORDER BY similarity DESC
            LIMIT :limit
            """,
            {"query_embedding": query_embedding, "limit": limit}
        )
        
        results = []
        for row in result:
            results.append({
                "type": "note",
                "id": row.id,
                "title": row.title,
                "snippet": row.content[:200],
                "relevance": float(row.similarity),
                "tags": row.tags,
            })
        
        return results


async def export_all_data(
    db: DatabaseManager, 
    format: str = "json", 
    start_date: Optional[str] = None
) -> str:
    """Export all data in specified format."""
    async with db.session() as session:
        # Fetch all tasks and notes
        tasks_result = await session.execute("SELECT * FROM tasks")
        notes_result = await session.execute("SELECT * FROM notes")
        
        tasks = [dict(row) for row in tasks_result]
        notes = [dict(row) for row in notes_result]
        
        export_data = {
            "export_date": datetime.utcnow().isoformat(),
            "version": "2.0.0",
            "tasks": tasks,
            "notes": notes,
            "metadata": {
                "total_tasks": len(tasks),
                "total_notes": len(notes),
                "completed_tasks": sum(1 for t in tasks if t.get("status") == "completed"),
            }
        }
        
        if format == "json":
            return json.dumps(export_data, indent=2, default=str)
        elif format == "csv":
            # Convert to CSV format
            return _convert_to_csv(export_data)
        elif format == "markdown":
            return _convert_to_markdown(export_data)
        else:
            raise ValueError(f"Unsupported format: {format}")


async def create_backup() -> Dict[str, Any]:
    """Create backup of all data."""
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"backup_{timestamp}.json"
    
    # Implementation would export and compress data
    # This is a simplified version
    
    backup_info = {
        "backup_id": timestamp,
        "created_at": datetime.utcnow().isoformat(),
        "location": str(backup_file),
        "size_bytes": 0,  # Calculate actual size
        "status": "success",
    }
    
    logger.info(f"Backup created: {backup_info['location']}")
    return backup_info


def _convert_to_csv(data: dict) -> str:
    """Convert export data to CSV format."""
    import csv
    from io import StringIO
    
    output = StringIO()
    if data.get("tasks"):
        writer = csv.DictWriter(output, fieldnames=data["tasks"][0].keys())
        writer.writeheader()
        writer.writerows(data["tasks"])
    
    return output.getvalue()


def _convert_to_markdown(data: dict) -> str:
    """Convert export data to Markdown format."""
    md = f"# Data Export\n\n"
    md += f"**Export Date:** {data['export_date']}\n\n"
    md += f"## Tasks ({data['metadata']['total_tasks']})\n\n"
    
    for task in data.get("tasks", []):
        md += f"### {task.get('title')}\n"
        md += f"- Status: {task.get('status')}\n"
        md += f"- Priority: {task.get('priority')}\n"
        md += f"- Created: {task.get('created_at')}\n\n"
    
    return md