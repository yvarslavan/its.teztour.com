"""
MySQL database connection and model definitions for the blog application.
This module provides database connectivity and model classes for MySQL operations.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text, Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
import logging
import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
import threading

logger = logging.getLogger(__name__)

# Base class for quality control models
QualityBase = declarative_base()

# Database manager for connection pooling and management
class DatabaseManager:
    """Manages database connections and sessions"""

    def __init__(self):
        self._engines = {}
        self._sessions = {}
        self._lock = threading.Lock()

    def get_engine(self, database_url, pool_size=5, max_overflow=10):
        """Get or create a database engine with connection pooling"""
        with self._lock:
            if database_url not in self._engines:
                self._engines[database_url] = create_engine(
                    database_url,
                    poolclass=QueuePool,
                    pool_size=pool_size,
                    max_overflow=max_overflow,
                    pool_pre_ping=True,
                    pool_recycle=3600
                )
            return self._engines[database_url]

    def get_session(self, database_url):
        """Get or create a session factory for a database"""
        with self._lock:
            if database_url not in self._sessions:
                engine = self.get_engine(database_url)
                self._sessions[database_url] = sessionmaker(bind=engine)
            return self._sessions[database_url]()

    def close_all(self):
        """Close all database connections"""
        with self._lock:
            for engine in self._engines.values():
                engine.dispose()
            self._engines.clear()
            self._sessions.clear()

# Global database manager instance
db_manager = DatabaseManager()

# Database connection configurations
QUALITY_DB_URL = "mysql+pymysql://user:password@localhost/quality_db"
MAIN_DB_URL = "mysql+pymysql://user:password@localhost/main_db"

def get_quality_connection():
    """Get a connection to the quality database"""
    return db_manager.get_session(QUALITY_DB_URL)

def init_quality_db():
    """Initialize the quality database connection"""
    try:
        session = get_quality_connection()
        session.close()
        logger.info("Quality database connection initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize quality database: {e}")
        return False

@contextmanager
def execute_quality_query_safe(query, params=None):
    """Safely execute a query on the quality database"""
    session = None
    try:
        session = get_quality_connection()
        if params:
            result = session.execute(text(query), params)
        else:
            result = session.execute(text(query))
        yield result
        session.commit()
    except Exception as e:
        if session:
            session.rollback()
        logger.error(f"Error executing quality query: {e}")
        raise
    finally:
        if session:
            session.close()

@contextmanager
def execute_main_query_safe(query, params=None):
    """Safely execute a query on the main database"""
    session = None
    try:
        session = db_manager.get_session(MAIN_DB_URL)
        if params:
            result = session.execute(text(query), params)
        else:
            result = session.execute(text(query))
        yield result
        session.commit()
    except Exception as e:
        if session:
            session.rollback()
        logger.error(f"Error executing main query: {e}")
        raise
    finally:
        if session:
            session.close()

# Model classes for MySQL operations
class Issue(QualityBase):
    """Model for Redmine issues"""
    __tablename__ = 'issues'

    id = Column(Integer, primary_key=True)
    subject = Column(String(255), nullable=False)
    description = Column(Text)
    status_id = Column(Integer)
    tracker_id = Column(Integer)
    priority_id = Column(Integer)
    author_id = Column(Integer)
    assigned_to_id = Column(Integer)
    created_on = Column(DateTime, default=datetime.utcnow)
    updated_on = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    project_id = Column(Integer)
    is_private = Column(Boolean, default=False)

    def __repr__(self):
        return f"<Issue {self.id}: {self.subject}>"

class Status(QualityBase):
    """Model for issue statuses"""
    __tablename__ = 'issue_statuses'

    id = Column(Integer, primary_key=True)
    name = Column(String(30), nullable=False)
    is_closed = Column(Boolean, default=False)
    is_default = Column(Boolean, default=False)
    position = Column(Integer)

    def __repr__(self):
        return f"<Status {self.id}: {self.name}>"

class Tracker(QualityBase):
    """Model for issue trackers"""
    __tablename__ = 'trackers'

    id = Column(Integer, primary_key=True)
    name = Column(String(30), nullable=False)
    is_in_chlog = Column(Boolean, default=False)
    position = Column(Integer)

    def __repr__(self):
        return f"<Tracker {self.id}: {self.name}>"

class CustomValue(QualityBase):
    """Model for custom field values"""
    __tablename__ = 'custom_values'

    id = Column(Integer, primary_key=True)
    customized_type = Column(String(30), nullable=False)
    customized_id = Column(Integer, nullable=False)
    custom_field_id = Column(Integer, nullable=False)
    value = Column(Text)

    def __repr__(self):
        return f"<CustomValue {self.id}: {self.value}>"

# Session classes
class Session:
    """Database session wrapper"""

    def __init__(self, database_url=None):
        self.database_url = database_url or QUALITY_DB_URL
        self._session = None

    def __enter__(self):
        self._session = db_manager.get_session(self.database_url)
        return self._session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            if exc_type:
                self._session.rollback()
            else:
                self._session.commit()
            self._session.close()

class QualitySession(Session):
    """Quality database session"""

    def __init__(self):
        super().__init__(QUALITY_DB_URL)

# Legacy compatibility - create instances for backward compatibility
Session = Session()
QualitySession = QualitySession()
