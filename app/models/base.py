"""Declarative Base configuration for SQLAlchemy models.

This module defines the shared `Base` class for all ORM models.
It attaches a custom `MetaData` instance, which can be used to
control naming conventions, schema-level options, or migrations.
"""
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


my_metadata = MetaData()

class Base(DeclarativeBase):
    """
    Base Model
    """
    metadata = my_metadata
