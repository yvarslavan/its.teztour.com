# blog/tasks/api_routes.py
"""
API endpoints для функционала изменения статуса задач
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from flask_wtf.csrf import CSRFProtect
import time
import traceback
from datetime import datetime

# Импорты из существующих модулей
from blog.utils.cache_manager import weekend_performance_optimizer
from blog.tasks.utils import create_redmine_connector
from redmine import (
    get_connection,
    db_redmine_host,
    db_redmine_user_name,
    db_redmine_password,
    db_redmine_name
)


# Получаем экземпляр CSRF для исключений
from blog import csrf

# Создаем Blueprint для API
api_bp = Blueprint('tasks_api', __name__, url_prefix='/tasks/api')

# ===== API ENDPOINTS ДЛЯ ИЗМЕНЕНИЯ СТАТУСА =====

@api_bp.route("/task/<int:task_id>", methods=["GET"])
@csrf.exempt
@login_required
@weekend_performance_optimizer
def get_task_by_id(task_id):
    """
    API для получения задачи по ID
    """
    current_app.logger.info(f"[API] GET /task/{task_id} - запрос от {current_user.username}")
    start_time = time.time()

    try:
        if not current_user.is_redmine_user:
            return jsonify({
                "error": "Доступ запрещен",
                "success": False,
                "data": None
            }), 403

        # Создаем коннектор Redmine
        redmine_connector = create_redmine_connector(
            is_redmine_user=current_user.is_redmine_user,
            user_login=current_user.username,
            password=current_user.password
        )

        if not redmine_connector:
            return jsonify({
                "error": "Ошибка подключения к Redmine",
                "success": False,
                "data": None
            }), 500

        try:
            # Получаем задачу из Redmine
            task = redmine_connector.redmine.issue.get(task_id, include=['status', 'priority', 'project', 'assigned_to'])

            # Получаем локализованные названия из MySQL
            mysql_conn = get_connection(
                db_redmine_host,
                db_redmine_user_name,
                db_redmine_password,
                db_redmine_name
            )

            task_data = {
                "id": task.id,
                "subject": task.subject,
                "description": getattr(task, 'description', ''),
                "status_id": task.status.id if hasattr(task, 'status') and task.status else None,
                "status_name": task.status.name if hasattr(task, 'status') and task.status else "Неизвестен",
                "priority_id": task.priority.id if hasattr(task, 'priority') and task.priority else None,
                "priority_name": task.priority.name if hasattr(task, 'priority') and task.priority else "Неизвестен",
                "project_id": task.project.id if hasattr(task, 'project') and task.project else None,
                "project_name": task.project.name if hasattr(task, 'project') and task.project else "Неизвестен",
                "assigned_to_id": task.assigned_to.id if hasattr(task, 'assigned_to') and task.assigned_to else None,
                "assigned_to_name": task.assigned_to.name if hasattr(task, 'assigned_to') and task.assigned_to else "Неизвестен",
                "created_on": task.created_on.isoformat() if hasattr(task, 'created_on') and task.created_on else None,
                "updated_on": task.updated_on.isoformat() if hasattr(task, 'updated_on') and task.updated_on else None,
                "due_date": task.due_date.isoformat() if hasattr(task, 'due_date') and task.due_date else None,
                "done_ratio": getattr(task, 'done_ratio', 0),
                "tracker_id": task.tracker.id if hasattr(task, 'tracker') and task.tracker else None,
                "tracker_name": task.tracker.name if hasattr(task, 'tracker') and task.tracker else None
            }

            # Получаем локализованные названия
            if mysql_conn:
                cursor = mysql_conn.cursor()
                try:
                    # Статусы
                    if task_data["status_id"]:
                        try:
                            cursor.execute("SELECT name FROM u_statuses WHERE id = %s", (task_data["status_id"],))
                            status_row = cursor.fetchone()
                            if status_row:
                                task_data["status_name"] = status_row['name']
                        except Exception as status_error:
                            current_app.logger.warning(f"[API] Ошибка получения статуса {task_data['status_id']}: {status_error}")
                            # Используем название из Redmine API
                            task_data["status_name"] = task.status.name if hasattr(task, 'status') and task.status else "Неизвестен"

                    # Приоритеты
                    if task_data["priority_id"]:
                        try:
                            cursor.execute("SELECT name FROM enumerations WHERE id = %s AND type = 'IssuePriority'", (task_data["priority_id"],))
                            priority_row = cursor.fetchone()
                            if priority_row:
                                task_data["priority_name"] = priority_row['name']
                        except Exception as priority_error:
                            current_app.logger.warning(f"[API] Ошибка получения приоритета {task_data['priority_id']}: {priority_error}")
                            # Используем название из Redmine API
                            task_data["priority_name"] = task.priority.name if hasattr(task, 'priority') and task.priority else "Неизвестен"

                    # Проекты
                    if task_data["project_id"]:
                        try:
                            cursor.execute("SELECT name FROM projects WHERE id = %s", (task_data["project_id"],))
                            project_row = cursor.fetchone()
                            if project_row:
                                task_data["project_name"] = project_row['name']
                        except Exception as project_error:
                            current_app.logger.warning(f"[API] Ошибка получения проекта {task_data['project_id']}: {project_error}")
                            # Используем название из Redmine API
                            task_data["project_name"] = task.project.name if hasattr(task, 'project') and task.project else "Неизвестен"

                    # Назначенные пользователи
                    if task_data["assigned_to_id"]:
                        try:
                            cursor.execute("SELECT firstname, lastname FROM users WHERE id = %s", (task_data["assigned_to_id"],))
                            user_row = cursor.fetchone()
                            if user_row:
                                task_data["assigned_to_name"] = f"{user_row['firstname']} {user_row['lastname']}".strip()
                        except Exception as user_error:
                            current_app.logger.warning(f"[API] Ошибка получения пользователя {task_data['assigned_to_id']}: {user_error}")
                            # Используем название из Redmine API
                            task_data["assigned_to_name"] = task.assigned_to.name if hasattr(task, 'assigned_to') and task.assigned_to else "Неизвестен"

                finally:
                    cursor.close()
                    mysql_conn.close()

            response_data = {
                "success": True,
                "data": task_data
            }

            execution_time = time.time() - start_time
            current_app.logger.info(f"[API] GET /task/{task_id} выполнен за {execution_time:.2f}с")

            return jsonify(response_data)

        except Exception as redmine_error:
            current_app.logger.error(f"[API] Ошибка получения задачи {task_id}: {str(redmine_error)}")
            return jsonify({
                "error": f"Ошибка получения данных задачи: {str(redmine_error)}",
                "success": False,
                "data": None
            }), 500

    except Exception as e:
        current_app.logger.error(f"[API] Критическая ошибка в GET /task/{task_id}: {str(e)}. Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": f"Внутренняя ошибка сервера: {str(e)}",
            "success": False,
            "data": None
        }), 500


@api_bp.route("/task/<int:task_id>/statuses", methods=["GET"])
@csrf.exempt
@login_required
@weekend_performance_optimizer
def get_task_available_statuses(task_id):
    """
    API для получения доступных статусов для конкретной задачи
    """
    current_app.logger.info(f"[API] /task/{task_id}/statuses - запрос от {current_user.username}")
    start_time = time.time()

    try:
        if not current_user.is_redmine_user:
            return jsonify({
                "error": "Доступ запрещен",
                "success": False,
                "statuses": []
            }), 403

        # Создаем коннектор Redmine
        redmine_connector = create_redmine_connector(
            is_redmine_user=current_user.is_redmine_user,
            user_login=current_user.username,
            password=current_user.password
        )

        if not redmine_connector:
            return jsonify({
                "error": "Ошибка подключения к Redmine",
                "success": False,
                "statuses": []
            }), 500

        try:
            # Получаем детали задачи для определения доступных статусов
            task = redmine_connector.redmine.issue.get(task_id)
            current_status_id = task.status.id if hasattr(task, 'status') and task.status else None

            current_app.logger.info(f"[API] Задача {task_id}: текущий статус ID = {current_status_id}")

            # Получаем все доступные статусы из Redmine
            all_statuses = redmine_connector.redmine.issue_status.all()

            # Получаем локализованные названия статусов из MySQL
            mysql_conn = get_connection(
                db_redmine_host,
                db_redmine_user_name,
                db_redmine_password,
                db_redmine_name
            )

            localized_statuses = {}
            if mysql_conn:
                cursor = mysql_conn.cursor()
                try:
                    cursor.execute("SELECT id, name FROM u_statuses")
                    for row in cursor.fetchall():
                        localized_statuses[row['id']] = row['name']
                finally:
                    cursor.close()
                    mysql_conn.close()

            # Формируем список доступных статусов
            available_statuses = []
            for status in all_statuses:
                # Пропускаем текущий статус
                if status.id == current_status_id:
                    continue

                status_name = localized_statuses.get(status.id, status.name)
                available_statuses.append({
                    "id": status.id,
                    "name": status_name,
                    "original_name": status.name
                })

            # Также включаем текущий статус для отображения
            current_status_name = localized_statuses.get(current_status_id, "Неизвестен")
            current_status = {
                "id": current_status_id,
                "name": current_status_name,
                "original_name": task.status.name if hasattr(task, 'status') and task.status else "Unknown"
            }

            response_data = {
                "success": True,
                "task_id": task_id,
                "current_status": current_status,
                "available_statuses": available_statuses,
                "total_available": len(available_statuses)
            }

            execution_time = time.time() - start_time
            current_app.logger.info(f"[API] /task/{task_id}/statuses выполнен за {execution_time:.2f}с, доступно {len(available_statuses)} статусов")

            return jsonify(response_data)

        except Exception as redmine_error:
            current_app.logger.error(f"[API] Ошибка получения статусов для задачи {task_id}: {str(redmine_error)}")
            return jsonify({
                "error": f"Ошибка получения данных задачи: {str(redmine_error)}",
                "success": False,
                "statuses": []
            }), 500

    except Exception as e:
        current_app.logger.error(f"[API] Критическая ошибка в /task/{task_id}/statuses: {str(e)}. Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": f"Внутренняя ошибка сервера: {str(e)}",
            "success": False,
            "statuses": []
        }), 500


@api_bp.route("/task/<int:task_id>/status", methods=["PUT"])
@csrf.exempt
@login_required
@weekend_performance_optimizer
def update_task_status(task_id):
    """
    API для изменения статуса задачи через Redmine REST API
    """
    current_app.logger.info(f"[API] PUT /task/{task_id}/status - запрос от {current_user.username}")
    current_app.logger.info(f"[API] Заголовки запроса: {dict(request.headers)}")
    current_app.logger.info(f"[API] Данные запроса: {request.get_json()}")
    start_time = time.time()

    try:
        current_app.logger.info(f"[API] Проверка прав доступа: current_user.is_redmine_user = {current_user.is_redmine_user}")

        if not current_user.is_redmine_user:
            current_app.logger.error(f"[API] Доступ запрещен для пользователя {current_user.username}")
            return jsonify({
                "error": "Доступ запрещен",
                "success": False
            }), 403

        # Получаем данные из запроса
        data = request.get_json()
        if not data or 'status_id' not in data:
            return jsonify({
                "error": "Не указан новый статус (status_id)",
                "success": False
            }), 400

        new_status_id = data['status_id']
        comment = data.get('comment', '')  # Необязательный комментарий

        current_app.logger.info(f"[API] Изменение статуса задачи {task_id} на {new_status_id}, комментарий: '{comment}'")

        # Создаем коннектор Redmine
        redmine_connector = create_redmine_connector(
            is_redmine_user=current_user.is_redmine_user,
            user_login=current_user.username,
            password=current_user.password
        )

        if not redmine_connector:
            return jsonify({
                "error": "Ошибка подключения к Redmine",
                "success": False
            }), 500

        try:
            # Получаем задачу для проверки прав доступа
            task = redmine_connector.redmine.issue.get(task_id)
            old_status_id = task.status.id if hasattr(task, 'status') and task.status else None

            current_app.logger.info(f"[API] Задача {task_id}: текущий статус {old_status_id} -> новый статус {new_status_id}")

            # Проверяем, что статус действительно изменился
            if old_status_id == new_status_id:
                return jsonify({
                    "error": "Новый статус совпадает с текущим",
                    "success": False
                }), 400

            # Подготавливаем данные для обновления
            update_data = {
                "status_id": new_status_id
            }

            # Добавляем комментарий если указан
            if comment.strip():
                update_data["notes"] = comment.strip()

            # Выполняем обновление через Redmine REST API
            result = redmine_connector.redmine.issue.update(task_id, **update_data)

            current_app.logger.info(f"[API] Статус задачи {task_id} успешно изменен на {new_status_id}")

            # Получаем обновленную задачу для возврата актуальных данных
            updated_task = redmine_connector.redmine.issue.get(task_id, include=['status', 'priority', 'project'])

            # Получаем локализованное название нового статуса
            mysql_conn = get_connection(
                db_redmine_host,
                db_redmine_user_name,
                db_redmine_password,
                db_redmine_name
            )

            new_status_name = "Неизвестен"
            if mysql_conn:
                cursor = mysql_conn.cursor()
                try:
                    cursor.execute("SELECT name FROM u_statuses WHERE id = %s", (new_status_id,))
                    result_row = cursor.fetchone()
                    if result_row:
                        new_status_name = result_row['name']
                    else:
                        new_status_name = updated_task.status.name if hasattr(updated_task, 'status') and updated_task.status else "Неизвестен"
                finally:
                    cursor.close()
                    mysql_conn.close()

            response_data = {
                "success": True,
                "task_id": task_id,
                "old_status_id": old_status_id,
                "new_status_id": new_status_id,
                "new_status_name": new_status_name,
                "comment": comment,
                "updated_at": datetime.now().isoformat(),
                "message": f"Статус задачи успешно изменен на '{new_status_name}'"
            }

            execution_time = time.time() - start_time
            current_app.logger.info(f"[API] PUT /task/{task_id}/status выполнен за {execution_time:.2f}с")

            return jsonify(response_data)

        except Exception as redmine_error:
            current_app.logger.error(f"[API] Ошибка изменения статуса задачи {task_id}: {str(redmine_error)}")

            # Обработка специфических ошибок Redmine
            error_message = str(redmine_error)
            if "422" in error_message or "Unprocessable Entity" in error_message:
                error_message = "Некорректные данные для изменения статуса. Проверьте права доступа."
            elif "401" in error_message or "Unauthorized" in error_message:
                error_message = "Отсутствуют права для изменения статуса этой задачи."
            elif "403" in error_message or "Forbidden" in error_message:
                error_message = "Доступ запрещен. Недостаточно прав для изменения статуса."
            elif "404" in error_message or "Not Found" in error_message:
                error_message = f"Задача #{task_id} не найдена."

            return jsonify({
                "error": error_message,
                "success": False,
                "technical_error": str(redmine_error)
            }), 500

    except Exception as e:
        current_app.logger.error(f"[API] Критическая ошибка в PUT /task/{task_id}/status: {str(e)}. Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": f"Внутренняя ошибка сервера: {str(e)}",
            "success": False
        }), 500
