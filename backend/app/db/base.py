"""SQLAlchemy declarative base + registry."""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase, registry


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""

    registry = registry()
