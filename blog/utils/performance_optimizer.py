"""
Performance optimization utilities for the my-issues page
"""
import time
import logging
from functools import wraps
from typing import Dict, List
from sqlalchemy import text
from blog.utils.cache_manager import CacheManager

logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """Centralized performance optimization manager"""

    def __init__(self):
        self.cache_manager = CacheManager()
        self.query_cache = {}
        self.response_cache = {}

    def measure_execution_time(self, operation_name: str):
        """Decorator to measure and log execution time"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    logger.info("⏱️ %s executed in %.3fs", operation_name, execution_time)

                    # Log slow operations
                    if execution_time > 1.0:
                        logger.warning("🐌 Slow operation detected: %s took %.3fs", operation_name, execution_time)

                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    logger.error("❌ %s failed after %.3fs: %s", operation_name, execution_time, str(e))
                    raise
            return wrapper
        return decorator

    def optimize_issues_query(self, session, email: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Optimized query for fetching user issues with pagination and proper indexing"""

        # Use optimized query with proper joins and pagination
        query = text("""
            SELECT
                i.id,
                i.updated_on,
                i.subject,
                s.name as status_name,
                i.status_id,
                i.priority_id,
                i.tracker_id,
                i.created_on
            FROM issues i
            INNER JOIN u_statuses s ON i.status_id = s.id
            WHERE i.easy_email_to = :email
               OR i.easy_email_to = :alt_email
            ORDER BY i.updated_on DESC
            LIMIT :limit OFFSET :offset
        """)

        alt_email = email.replace("@tez-tour.com", "@msk.tez-tour.com")

        result = session.execute(query, {
            'email': email,
            'alt_email': alt_email,
            'limit': limit,
            'offset': offset
        })

        return [
            {
                "id": row.id,
                "updated_on": row.updated_on.isoformat() if row.updated_on else None,
                "subject": row.subject,
                "status_name": row.status_name,
                "status_id": row.status_id,
                "priority_id": row.priority_id,
                "tracker_id": row.tracker_id,
                "created_on": row.created_on.isoformat() if row.created_on else None
            }
            for row in result
        ]

    def get_cached_statuses(self, session) -> List[Dict]:
        """Get cached status list to avoid repeated queries"""
        cache_key = "statuses_list"
        cached_statuses = self.cache_manager.get(cache_key)

        if cached_statuses is None:
            # Optimized status query
            result = session.execute(text("SELECT id, name FROM u_statuses ORDER BY id"))
            cached_statuses = [{"id": row.id, "name": row.name} for row in result]

            # Cache for 1 hour
            self.cache_manager.set(cache_key, cached_statuses, ttl=3600)
            logger.info("📊 Statuses cached for 1 hour")

        return cached_statuses

    def optimize_redmine_issues_query(self, connection, author_id: int, email: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Optimized Redmine issues query with pagination"""

        query = """
        SELECT
            i.id AS issue_id,
            i.updated_on AS updated_on,
            i.subject AS subject,
            us.name AS status_name,
            i.status_id AS status_id,
            i.priority_id,
            i.tracker_id,
            i.created_on
        FROM issues i
        INNER JOIN u_statuses us ON i.status_id = us.id
        WHERE i.author_id = %s OR i.easy_email_to LIKE %s
        ORDER BY i.updated_on DESC
        LIMIT %s OFFSET %s
        """

        issues_data = []

        try:
            with connection.cursor() as cursor:
                cursor.execute(query, (author_id, f"%{email}%", limit, offset))
                rows = cursor.fetchall()

                for row in rows:
                    issues_data.append({
                        "id": row["issue_id"],
                        "updated_on": str(row["updated_on"]),
                        "subject": row["subject"],
                        "status_name": row["status_name"],
                        "status_id": row["status_id"],
                        "priority_id": row.get("priority_id"),
                        "tracker_id": row.get("tracker_id"),
                        "created_on": str(row.get("created_on")) if row.get("created_on") else None
                    })

        except Exception as e:
            logger.error("❌ Error in optimized Redmine query: %s", e)
            return []

        return issues_data

    def create_database_indexes(self, session):
        """Create performance indexes for frequently queried columns"""
        try:
            # Create indexes for better query performance
            indexes_to_create = [
                "CREATE INDEX IF NOT EXISTS idx_issues_email_updated ON issues(easy_email_to, updated_on DESC)",
                "CREATE INDEX IF NOT EXISTS idx_issues_author_updated ON issues(author_id, updated_on DESC)",
                "CREATE INDEX IF NOT EXISTS idx_issues_status ON issues(status_id)",
                "CREATE INDEX IF NOT EXISTS idx_issues_priority ON issues(priority_id)",
                "CREATE INDEX IF NOT EXISTS idx_issues_tracker ON issues(tracker_id)",
                "CREATE INDEX IF NOT EXISTS idx_issues_created ON issues(created_on)",
            ]

            for index_sql in indexes_to_create:
                try:
                    session.execute(text(index_sql))
                    logger.info("✅ Created index: %s", index_sql.split('idx_')[1].split(' ')[0])
                except Exception as e:
                    logger.warning("⚠️ Index creation warning: %s", e)

            session.commit()
            logger.info("🎯 Database indexes optimization completed")

        except Exception as e:
            logger.error("❌ Error creating database indexes: %s", e)
            session.rollback()

    def compress_response_data(self, data: Dict) -> Dict:
        """Compress response data by removing unnecessary fields and optimizing structure"""
        if 'issues' in data:
            # Only include essential fields for initial load
            compressed_issues = []
            for issue in data['issues']:
                compressed_issues.append({
                    'id': issue.get('id'),
                    'subject': issue.get('subject'),
                    'status_name': issue.get('status_name'),
                    'status_id': issue.get('status_id'),
                    'updated_on': issue.get('updated_on')
                })
            data['issues'] = compressed_issues

        return data

    def get_pagination_info(self, total_count: int, page: int, per_page: int) -> Dict:
        """Calculate pagination information"""
        total_pages = (total_count + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1

        return {
            'current_page': page,
            'per_page': per_page,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_next': has_next,
            'has_prev': has_prev,
            'next_page': page + 1 if has_next else None,
            'prev_page': page - 1 if has_prev else None
        }

# Global performance optimizer instance
perf_optimizer = PerformanceOptimizer()
