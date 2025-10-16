#!/usr/bin/env python3
"""
Setup script for performance optimization
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from blog.utils.performance_optimizer import perf_optimizer
from mysql_db import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database_indexes():
    """Create performance indexes in the database"""
    logger.info("🔧 Setting up database indexes...")

    try:
        with Session() as session:
            perf_optimizer.create_database_indexes(session)
            logger.info("✅ Database indexes created successfully")
    except Exception as e:
        logger.error("❌ Failed to create database indexes: %s", e)
        return False

    return True

def verify_optimization_files():
    """Verify that all optimization files exist"""
    logger.info("🔍 Verifying optimization files...")

    required_files = [
        "blog/utils/performance_optimizer.py",
        "blog/main/routes_optimized.py",
        "blog/utils/cache_manager.py",
        "blog/static/js/my_issues_optimized.js",
        "blog/static/css/my_issues_optimized.css",
        "blog/templates/issues_optimized.html",
        "blog/static/sw.js"
    ]

    missing_files = []
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)

    if missing_files:
        logger.error("❌ Missing optimization files:")
        for file_path in missing_files:
            logger.error("  - %s", file_path)
        return False

    logger.info("✅ All optimization files present")
    return True

def main():
    """Main setup function"""
    logger.info("🚀 Starting performance optimization setup...")

    # Verify files
    if not verify_optimization_files():
        logger.error("❌ Setup failed: Missing required files")
        sys.exit(1)

    # Setup database indexes
    if not setup_database_indexes():
        logger.error("❌ Setup failed: Database index creation failed")
        sys.exit(1)

    logger.info("✅ Performance optimization setup completed successfully!")
    logger.info("📋 Next steps:")
    logger.info("  1. Access optimized page at: /optimized/my-issues-optimized")
    logger.info("  2. Monitor performance metrics in browser console")
    logger.info("  3. Configure Redis for advanced caching (optional)")
    logger.info("  4. Review PERFORMANCE_OPTIMIZATION_REPORT.md for details")

if __name__ == "__main__":
    main()
