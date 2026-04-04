"""SQLAlchemy models for data persistence."""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime, JSON, 
    Text, Index, Enum, ForeignKey
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
import uuid
from pydantic import BaseModel, Field


class Base(DeclarativeBase):
    pass


class PriorityEnum(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatusEnum(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Task(Base):
    __tablename__ = "tasks"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    priority: Mapped[PriorityEnum] = mapped_column(Enum(PriorityEnum), default=PriorityEnum.MEDIUM)
    status: Mapped[TaskStatusEnum] = mapped_column(Enum(TaskStatusEnum), default=TaskStatusEnum.PENDING)
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)
    assignee: Mapped[Optional[str]] = mapped_column(String(200))
    due_date: Mapped[Optional[datetime]]
    completed_at: Mapped[Optional[datetime]]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_tasks_status', 'status'),
        Index('idx_tasks_priority', 'priority'),
        Index('idx_tasks_assignee', 'assignee'),
        Index('idx_tasks_due_date', 'due_date'),
    )


class Note(Base):
    __tablename__ = "notes"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text)
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)
    folder: Mapped[Optional[str]] = mapped_column(String(200))
    embedding: Mapped[Optional[List[float]]] = mapped_column(JSON)  # For semantic search
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_notes_tags', 'tags', postgresql_using='gin'),
        Index('idx_notes_folder', 'folder'),
    )


# Pydantic models for validation
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    priority: PriorityEnum = PriorityEnum.MEDIUM
    tags: List[str] = Field(default_factory=list)
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    priority: Optional[PriorityEnum] = None
    status: Optional[TaskStatusEnum] = None
    tags: Optional[List[str]] = None
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None


class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str
    tags: List[str] = Field(default_factory=list)
    folder: Optional[str] = None