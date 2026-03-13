"""Legacy compatibility shim for task utils.

Единая рабочая реализация живет в blog.tasks.utils.
Этот модуль сохранен только для обратной совместимости старых импортов.
"""

from blog.tasks.utils import (
    create_redmine_connector,
    format_issue_date,
    get_accurate_task_count,
    get_redmine_connector,
    get_user_assigned_tasks_paginated_optimized,
    task_to_dict,
)

__all__ = [
    "create_redmine_connector",
    "format_issue_date",
    "get_accurate_task_count",
    "get_redmine_connector",
    "get_user_assigned_tasks_paginated_optimized",
    "task_to_dict",
]
