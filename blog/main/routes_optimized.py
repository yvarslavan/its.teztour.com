"""
Optimized routes for the my-issues page with performance improvements
"""
import time
import logging
from flask import Blueprint, render_template, request, jsonify, g
from flask_login import login_required, current_user
from blog import csrf
from sqlalchemy import text
from blog.utils.performance_optimizer import perf_optimizer
from blog.utils.cache_manager import CacheManager
from mysql_db import Session
from redmine import check_user_active_redmine, get_connection
from config import get

logger = logging.getLogger(__name__)

# Constants
ANONYMOUS_USER_ID = 0  # Default anonymous user ID

# Create optimized blueprint
optimized_main = Blueprint('optimized_main', __name__)

# Initialize cache manager
cache_manager = CacheManager()

@optimized_main.route("/my-issues-optimized", methods=["GET"])
@login_required
@perf_optimizer.measure_execution_time("my_issues_page_load")
def my_issues_optimized():
    """Optimized my-issues page with performance improvements"""
    try:
        # Pre-load critical data in parallel
        start_time = time.time()

        # Check if we can use cached data
        cache_key = f"user_issues_{current_user.id}"
        cached_data = cache_manager.get(cache_key)

        if cached_data and request.args.get('use_cache', '1') == '1':
            logger.info("📦 Using cached data for user %s", current_user.id)
            return render_template("issues_optimized.html",
                                 title="Мои заявки",
                                 cached_data=cached_data)

        # Load page without heavy data - let frontend handle data loading
        load_time = time.time() - start_time
        logger.info("⚡ Optimized page load completed in %.3fs", load_time)

        return render_template("issues_optimized.html", title="Мои заявки")

    except Exception as e:
        logger.error("❌ Error in optimized my_issues: %s", str(e))
        return render_template("issues_optimized.html",
                             title="Мои заявки",
                             error="Ошибка загрузки страницы")

@optimized_main.route("/api/my-issues/optimized", methods=["GET"])
@login_required
@perf_optimizer.measure_execution_time("get_my_issues_api")
def get_my_issues_optimized():
    """Optimized API endpoint for fetching user issues with pagination and caching"""

    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 items
    offset = (page - 1) * per_page

    # Check cache first
    cache_key = f"user_issues_{current_user.id}_page_{page}_per_{per_page}"
    cached_response = cache_manager.get(cache_key)

    if cached_response and request.args.get('use_cache', '1') == '1':
        logger.info("📦 Returning cached issues for user %s, page %s", current_user.id, page)
        return jsonify(cached_response)

    try:
        with Session() as session:
            # Create database indexes if needed (run once)
            if not hasattr(g, 'indexes_created'):
                perf_optimizer.create_database_indexes(session)
                g.indexes_created = True

            # Get database connection
            conn = get_connection(
                get('mysql_redmine', 'host'),
                get('mysql_redmine', 'user'),
                get('mysql_redmine', 'password'),
                get('mysql_redmine', 'database')
            )

            if conn is None:
                return jsonify({
                    "error": "Ошибка подключения к базе данных",
                    "issues": [],
                    "pagination": {}
                }), 500

            # Check user type
            check_user_redmine = check_user_active_redmine(conn, current_user.email)

            # Get cached statuses
            statuses = perf_optimizer.get_cached_statuses(session)

            # Fetch issues based on user type
            if check_user_redmine == ANONYMOUS_USER_ID:
                issues_data = perf_optimizer.optimize_issues_query(
                    session, current_user.email, per_page, offset
                )
                # Get total count for pagination
                count_query = text("""
                    SELECT COUNT(*) FROM issues
                    WHERE easy_email_to = :email OR easy_email_to = :alt_email
                """)
                total_count = session.execute(count_query, {
                    'email': current_user.email,
                    'alt_email': current_user.email.replace("@tez-tour.com", "@msk.tez-tour.com")
                }).scalar()
            else:
                issues_data = perf_optimizer.optimize_redmine_issues_query(
                    conn, check_user_redmine, current_user.email, per_page, offset
                )
                # Get total count for Redmine users
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*) FROM issues
                        WHERE author_id = %s OR easy_email_to LIKE %s
                    """, (check_user_redmine, f"%{current_user.email}%"))
                    total_count = cursor.fetchone()[0]

            # Prepare response
            response_data = {
                "issues": issues_data,
                "statuses": statuses,
                "pagination": perf_optimizer.get_pagination_info(total_count, page, per_page),
                "cached_at": time.time()
            }

            # Compress response data
            response_data = perf_optimizer.compress_response_data(response_data)

            # Cache the response for 5 minutes
            cache_manager.set(cache_key, response_data, ttl=300)

            logger.info("✅ Optimized API response: %s issues, page %s/%s",
                       len(issues_data), page, response_data['pagination']['total_pages'])

            return jsonify(response_data)

    except Exception as e:
        logger.error("❌ Error in optimized get_my_issues: %s", str(e))
        return jsonify({
            "error": str(e),
            "issues": [],
            "statuses": [],
            "pagination": {}
        }), 500

@optimized_main.route("/api/my-issues/statistics", methods=["GET"])
@login_required
@perf_optimizer.measure_execution_time("get_issues_statistics")
def get_issues_statistics():
    """Optimized statistics endpoint with caching"""

    cache_key = f"user_statistics_{current_user.id}"
    cached_stats = cache_manager.get(cache_key)

    if cached_stats and request.args.get('use_cache', '1') == '1':
        return jsonify(cached_stats)

    try:
        with Session() as session:
            conn = get_connection(
                get('mysql_redmine', 'host'),
                get('mysql_redmine', 'user'),
                get('mysql_redmine', 'password'),
                get('mysql_redmine', 'database')
            )

            if conn is None:
                return jsonify({"error": "Database connection failed"}), 500

            check_user_redmine = check_user_active_redmine(conn, current_user.email)

            # Optimized statistics query
            if check_user_redmine == ANONYMOUS_USER_ID:
                stats_query = text("""
                    SELECT
                        s.name as status_name,
                        s.id as status_id,
                        COUNT(i.id) as count
                    FROM issues i
                    INNER JOIN u_statuses s ON i.status_id = s.id
                    WHERE i.easy_email_to = :email OR i.easy_email_to = :alt_email
                    GROUP BY s.id, s.name
                    ORDER BY s.id
                """)
                result = session.execute(stats_query, {
                    'email': current_user.email,
                    'alt_email': current_user.email.replace("@tez-tour.com", "@msk.tez-tour.com")
                })
            else:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT
                            s.name as status_name,
                            s.id as status_id,
                            COUNT(i.id) as count
                        FROM issues i
                        INNER JOIN u_statuses s ON i.status_id = s.id
                        WHERE i.author_id = %s OR i.easy_email_to LIKE %s
                        GROUP BY s.id, s.name
                        ORDER BY s.id
                    """, (check_user_redmine, f"%{current_user.email}%"))
                    result = cursor.fetchall()

            # Process statistics
            statistics = {
                'total': 0,
                'by_status': {},
                'status_list': []
            }

            for row in result:
                if hasattr(row, 'status_name'):  # SQLAlchemy result
                    status_name = row.status_name
                    status_id = row.status_id
                    count = row.count
                else:  # PyMySQL result
                    status_name = row['status_name']
                    status_id = row['status_id']
                    count = row['count']

                statistics['by_status'][status_name] = count
                statistics['status_list'].append({
                    'id': status_id,
                    'name': status_name,
                    'count': count
                })
                statistics['total'] += count

            # Cache for 10 minutes
            cache_manager.set(cache_key, statistics, ttl=600)

            return jsonify(statistics)

    except Exception as e:
        logger.error("❌ Error getting statistics: %s", str(e))
        return jsonify({"error": str(e)}), 500

@optimized_main.route("/api/my-issues/clear-cache", methods=["POST"])
@csrf.exempt  # API endpoint - exempt from CSRF
@login_required
def clear_issues_cache():
    """Clear cache for current user"""
    try:
        user_cache_keys = [
            f"user_issues_{current_user.id}",
            f"user_statistics_{current_user.id}"
        ]

        # Clear paginated cache (first 10 pages)
        for page in range(1, 11):
            for per_page in [10, 20, 50]:
                user_cache_keys.append(f"user_issues_{current_user.id}_page_{page}_per_{per_page}")

        cleared_count = 0
        for key in user_cache_keys:
            if cache_manager.delete(key):
                cleared_count += 1

        logger.info("🗑️ Cleared %s cache entries for user %s", cleared_count, current_user.id)

        return jsonify({
            "success": True,
            "cleared_entries": cleared_count,
            "message": "Cache cleared successfully"
        })

    except Exception as e:
        logger.error("❌ Error clearing cache: %s", str(e))
        return jsonify({"error": str(e)}), 500
