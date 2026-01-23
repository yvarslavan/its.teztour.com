"""
Redmine Main Module
Main entry point that imports and coordinates all Redmine functionality.
"""

# Import all functionality from separated modules
from redmine_db import (
    get_connection,
    execute_query,
    execute_update,
    db_redmine_host,
    db_redmine_user_name,
    db_redmine_password,
    db_redmine_name,
    db_redmine_port,
    REDMINE_URL,
    REDMINE_ADMIN_API_KEY,
    ANONYMOUS_USER_ID_CONFIG,
)

from redmine_api import RedmineConnector, update_user_id

from redmine_utils import (
    convert_datetime_msk_format,
    get_multiple_user_names,
    get_multiple_project_names,
    get_multiple_status_names,
    get_multiple_priority_names,
    generate_optimized_property_names,
    determine_activity_type,
)

from redmine_notifications import (
    get_count_notifications,
    get_count_notifications_add_notes,
    process_added_notes,
    delete_notifications,
    delete_notifications_notes,
    check_notifications,
)

# Re-export for backward compatibility
__all__ = [
    # Database functions
    'get_connection',
    'execute_query',
    'execute_update',
    'db_redmine_host',
    'db_redmine_user_name',
    'db_redmine_password',
    'db_redmine_name',
    'db_redmine_port',
    'REDMINE_URL',
    'REDMINE_ADMIN_API_KEY',
    'ANONYMOUS_USER_ID_CONFIG',
    # API functions
    'RedmineConnector',
    'update_user_id',
    # Utility functions
    'convert_datetime_msk_format',
    'get_multiple_user_names',
    'get_multiple_project_names',
    'get_multiple_status_names',
    'get_multiple_priority_names',
    'generate_optimized_property_names',
    'determine_activity_type',
    # Notification functions
    'get_count_notifications',
    'get_count_notifications_add_notes',
    'process_added_notes',
    'delete_notifications',
    'delete_notifications_notes',
    'check_notifications',
]
