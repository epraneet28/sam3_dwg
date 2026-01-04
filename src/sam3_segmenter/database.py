"""Database models and setup for SAM3 Drawing Segmenter.

This module provides SQLAlchemy models for storing:
- Exemplar metadata (images used for visual reference during segmentation)
- Drawing metadata (uploaded drawings and their segmentation results)
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, Generator

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    Boolean,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from .config import settings

# Base class for all models
Base = declarative_base()


class Exemplar(Base):
    """Exemplar image metadata.

    Exemplars are visual references that help SAM3 better identify specific zone types.
    They are stored as PNG files in the exemplars directory, with metadata tracked here.
    """

    __tablename__ = "exemplars"

    id = Column(Integer, primary_key=True, autoincrement=True)
    zone_type = Column(String(50), nullable=False, index=True)
    filename = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    upload_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    source_drawing_id = Column(Integer, nullable=True)  # FK to Drawing, optional

    # Effectiveness metrics (computed from test results)
    effectiveness_score = Column(Float, nullable=True)
    times_used = Column(Integer, default=0, nullable=False)
    avg_confidence_improvement = Column(Float, nullable=True)

    # Metadata
    file_size_bytes = Column(Integer, nullable=True)
    image_width = Column(Integer, nullable=True)
    image_height = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "zone_type": self.zone_type,
            "filename": self.filename,
            "name": self.name,
            "description": self.description,
            "upload_date": self.upload_date.isoformat() if self.upload_date else None,
            "source_drawing_id": self.source_drawing_id,
            "effectiveness_score": self.effectiveness_score,
            "times_used": self.times_used,
            "avg_confidence_improvement": self.avg_confidence_improvement,
            "file_size_bytes": self.file_size_bytes,
            "image_width": self.image_width,
            "image_height": self.image_height,
            "is_active": self.is_active,
        }


class PromptConfig(Base):
    """Zone prompt configuration.

    Stores customizable prompt configurations for each zone type.
    These override the default prompts in STRUCTURAL_ZONE_PROMPTS.
    """

    __tablename__ = "prompt_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    zone_type = Column(String(50), nullable=False, unique=True, index=True)
    primary_prompt = Column(String(500), nullable=False)
    alternate_prompts = Column(Text, nullable=True)  # JSON array
    typical_location = Column(String(50), default="any", nullable=False)
    priority = Column(Integer, default=5, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(timezone.utc), nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        alternate = []
        if self.alternate_prompts:
            try:
                alternate = json.loads(self.alternate_prompts)
            except json.JSONDecodeError:
                alternate = []

        return {
            "zone_type": self.zone_type,
            "primary_prompt": self.primary_prompt,
            "alternate_prompts": alternate,
            "typical_location": self.typical_location,
            "priority": self.priority,
            "enabled": self.enabled,
        }


class InferenceConfig(Base):
    """Inference settings configuration.

    Stores global inference settings like confidence threshold.
    Only one row should exist (singleton pattern).
    """

    __tablename__ = "inference_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    confidence_threshold = Column(Float, default=0.3, nullable=False)
    return_masks = Column(Boolean, default=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(timezone.utc), nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "confidence_threshold": self.confidence_threshold,
            "return_masks": self.return_masks,
        }


class Drawing(Base):
    """Uploaded drawing metadata and segmentation results.

    Stores information about drawings that have been processed through the service,
    including their segmentation results for reference and testing.
    """

    __tablename__ = "drawings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)
    upload_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # File metadata
    file_size_bytes = Column(Integer, nullable=True)
    image_width = Column(Integer, nullable=True)
    image_height = Column(Integer, nullable=True)
    file_format = Column(String(10), nullable=True)  # PNG, JPEG, PDF

    # Processing metadata
    processing_date = Column(DateTime, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    page_type = Column(String(50), nullable=True)
    page_type_confidence = Column(Float, nullable=True)

    # Segmentation results (stored as JSON)
    zones_json = Column(Text, nullable=True)  # JSON array of ZoneResult objects

    # Configuration used
    confidence_threshold = Column(Float, nullable=True)
    used_exemplars = Column(Boolean, default=False, nullable=False)

    # User notes
    notes = Column(Text, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        zones = None
        if self.zones_json:
            try:
                zones = json.loads(self.zones_json)
            except json.JSONDecodeError:
                zones = None

        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "upload_date": self.upload_date.isoformat() if self.upload_date else None,
            "file_size_bytes": self.file_size_bytes,
            "image_width": self.image_width,
            "image_height": self.image_height,
            "file_format": self.file_format,
            "processing_date": self.processing_date.isoformat() if self.processing_date else None,
            "processing_time_ms": self.processing_time_ms,
            "page_type": self.page_type,
            "page_type_confidence": self.page_type_confidence,
            "zones": zones,
            "confidence_threshold": self.confidence_threshold,
            "used_exemplars": self.used_exemplars,
            "notes": self.notes,
        }


# Database engine and session management
_engine = None
_SessionLocal = None


def get_database_url() -> str:
    """Get database URL from settings or use default SQLite."""
    db_path = Path("data/sam3.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path}"


def init_db() -> None:
    """Initialize database engine and create tables if they don't exist."""
    global _engine, _SessionLocal

    database_url = get_database_url()
    _engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},  # Needed for SQLite
        echo=False,  # Set to True for SQL query debugging
    )

    # Create tables
    Base.metadata.create_all(bind=_engine)

    # Create session factory
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def get_db() -> Generator[Session, None, None]:
    """Get database session for FastAPI dependency injection.

    This is a generator-based FastAPI dependency that manages database sessions.
    Use with the Depends() function in route parameters.

    Example:
        @app.get("/items")
        async def read_items(db: Session = Depends(get_db)):
            items = db.query(Item).all()
            return items

    The session is automatically closed after the request is complete.
    """
    if _SessionLocal is None:
        init_db()

    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def reset_db() -> None:
    """Drop all tables and recreate. WARNING: Deletes all data!"""
    if _engine is None:
        init_db()

    Base.metadata.drop_all(bind=_engine)
    Base.metadata.create_all(bind=_engine)


def seed_prompt_config(db: Session) -> None:
    """Seed default prompt configurations from STRUCTURAL_ZONE_PROMPTS.

    This is called when the database is first initialized or when resetting to defaults.
    Only inserts rows that don't already exist.
    """
    from .prompts.structural import STRUCTURAL_ZONE_PROMPTS

    for zone_type, config in STRUCTURAL_ZONE_PROMPTS.items():
        # Check if already exists
        existing = db.query(PromptConfig).filter(PromptConfig.zone_type == zone_type).first()
        if existing:
            continue

        prompt_config = PromptConfig(
            zone_type=zone_type,
            primary_prompt=config.get("primary_prompt", zone_type.replace("_", " ")),
            alternate_prompts=json.dumps(config.get("alternate_prompts", [])),
            typical_location=config.get("typical_location", "any"),
            priority=config.get("priority", 5),
            enabled=True,
        )
        db.add(prompt_config)

    db.commit()


def seed_inference_config(db: Session) -> None:
    """Seed default inference configuration.

    Creates the singleton inference config row if it doesn't exist.
    """
    existing = db.query(InferenceConfig).first()
    if existing:
        return

    inference_config = InferenceConfig(
        confidence_threshold=0.3,
        return_masks=True,
        version=1,
    )
    db.add(inference_config)
    db.commit()


def get_or_seed_configs(db: Session) -> None:
    """Ensure prompt and inference configs exist, seeding defaults if needed."""
    seed_prompt_config(db)
    seed_inference_config(db)
