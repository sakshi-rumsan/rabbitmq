# SQLAlchemy mixins for common functionality
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import Column, DateTime, func

class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class TableNameMixin:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()