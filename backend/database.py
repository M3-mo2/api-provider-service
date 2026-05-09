"""
Database models and schema for API Provider Service
"""

from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    Float,
    DateTime,
    Text,
    ForeignKey,
    Date,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

Base = declarative_base()


class APIKey(Base):
    """API Keys for Fireworks.ai"""

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    api_key = Column(Text, nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    total_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    success_rate = Column(Float, default=100.0)

    # Relationships
    request_logs = relationship("RequestLog", back_populates="api_key")
    usage_stats = relationship("UsageStats", back_populates="api_key")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "api_key": self.api_key[:10] + "..." if self.api_key else None,  # Masked
            "is_active": self.is_active,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_used_at": self.last_used_at.isoformat()
            if self.last_used_at
            else None,
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.success_rate,
        }


class Model(Base):
    """Models configuration"""

    __tablename__ = "models"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    fireworks_model_id = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    model_type = Column(
        String(50), nullable=True
    )  # 'chat', 'completion', 'embedding', 'image'
    context_length = Column(Integer, nullable=True)
    input_price = Column(Float, nullable=True)
    output_price = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "fireworks_model_id": self.fireworks_model_id,
            "display_name": self.display_name,
            "description": self.description,
            "is_active": self.is_active,
            "model_type": self.model_type,
            "context_length": self.context_length,
            "input_price": self.input_price,
            "output_price": self.output_price,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class RequestLog(Base):
    """Request logs for monitoring"""

    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(255), unique=True, nullable=False)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=True)
    model = Column(String(255), nullable=True)
    endpoint = Column(String(255), nullable=True)
    method = Column(String(10), nullable=True)
    status_code = Column(Integer, nullable=True)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    latency_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    client_ip = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    api_key = relationship("APIKey", back_populates="request_logs")

    def to_dict(self):
        return {
            "id": self.id,
            "request_id": self.request_id,
            "api_key_id": self.api_key_id,
            "model": self.model,
            "endpoint": self.endpoint,
            "method": self.method,
            "status_code": self.status_code,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "latency_ms": self.latency_ms,
            "error_message": self.error_message,
            "client_ip": self.client_ip,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Config(Base):
    """System configuration"""

    __tablename__ = "config"

    key = Column(String(255), primary_key=True)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "key": self.key,
            "value": self.value,
            "description": self.description,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class UsageStats(Base):
    """Aggregated usage statistics"""

    __tablename__ = "usage_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=True)
    model = Column(String(255), nullable=True)
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)

    # Relationships
    api_key = relationship("APIKey", back_populates="usage_stats")

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "api_key_id": self.api_key_id,
            "model": self.model,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "total_tokens": self.total_tokens,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_cost": self.total_cost,
        }


class Database:
    """Database manager"""

    def __init__(self, db_path="data/database.db"):
        self.db_path = db_path
        self.engine = None
        self.Session = None

    def initialize(self):
        """Initialize database connection and create tables"""
        # Create data directory if not exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Create engine with SQLite thread safety
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            echo=False,
            connect_args={"check_same_thread": False},
        )

        # Create all tables (safe: checkfirst=True by default)
        try:
            Base.metadata.create_all(self.engine)
        except Exception as e:
            if "already exists" in str(e):
                pass
            else:
                raise e

        # Create session factory
        self.Session = sessionmaker(bind=self.engine)

        # Create indexes
        self._create_indexes()

        print(f"✓ Database initialized at {self.db_path}")

    def _create_indexes(self):
        """Create database indexes for performance"""
        from sqlalchemy import Index

        # Indexes are defined in the models using index=True
        # Additional composite indexes can be added here if needed
        pass

    def get_session(self):
        """Get a new database session"""
        if not self.Session:
            self.initialize()
        return self.Session()

    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()


# Global database instance
db = Database()
