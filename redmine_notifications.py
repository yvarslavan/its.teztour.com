"""
Redmine Notifications Module
Handles notification processing and management.
"""

import logging
import time
import uuid

# Handle optional imports
try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False

try:
    from flask import current_app
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    current_app = None

try:
    from blog.models import Notifications, NotificationsAddNotes
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False

if not PYMYSQL_AVAILABLE:
    logging.warning("pymysql not available - some functions may not work")
if not FLASK_AVAILABLE:
    logging.warning("flask not available - some functions may not work")
if not MODELS_AVAILABLE:
    logging.warning("blog models not available - some functions may not work")

# Создаем объект логгера
logger = logging.getLogger(__name__)


def get_database_cursor(connection):
    """Получает курсор для работы с базой данных"""
    try:
        return connection.cursor()
    except Exception as e:
        logger.error("Ошибка при получении курсора: %s", e)
        return None


def process_status_changes(connection, cursor, email_part, current_user_id, easy_email_to):
    """Обрабатывает изменения статуса заявок"""
    from redmine_db import execute_query

    log = current_app.logger
    run_id = uuid.uuid4()
    func_name = "PROCESS_STATUS_CHANGES"
    start_time_func = time.time()
    log.info(
        f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}, EmailPart={email_part}, EasyEmailTo={easy_email_to}: НАЧАЛО обработки."
    )

    query_status_changes = """
        SELECT id, issue_id, date_created, old_value, new_value, author
        FROM u_its_update_status
        WHERE LOWER(author) = LOWER(%s)
        ORDER BY date_created DESC LIMIT 50
    """
    log.debug(
        f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: SQL Query to Redmine u_its_update_status for Author='{easy_email_to}'"
    )

    query_start_time = time.time()
    rows_status_changes = execute_query(
        cursor, query_status_changes, (easy_email_to,)
    )
    query_end_time = time.time()

    if rows_status_changes is None:
        log.error(
            f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Ошибка SQL-запроса к u_its_update_status. Время: {query_end_time - query_start_time:.2f} сек."
        )
        return 0, [], [f"Ошибка SQL-запроса к u_its_update_status для Author='{easy_email_to}'"]

    if not rows_status_changes:
        log.info(
            f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Нет записей в u_its_update_status для Author='{easy_email_to}'. Время: {query_end_time - query_start_time:.2f} сек."
        )
        return 0, [], []

    log.info(
        f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Найдено {len(rows_status_changes)} записей в u_its_update_status для Author='{easy_email_to}'. Время: {query_end_time - query_start_time:.2f} сек."
    )

    processed_in_this_run = 0
    processed_ids_in_this_run = []
    errors_in_this_run_status = []

    for row in rows_status_changes:
        try:
            issue_id = row["issue_id"]
            date_created = row["date_created"]
            old_value = row["old_value"]
            new_value = row["new_value"]
            author = row["author"]

            log.debug(
                f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Обработка записи ID={row['id']}, IssueID={issue_id}, Author={author}"
            )

            # Проверяем, существует ли уже уведомление для этой записи
            check_query = """
                SELECT id FROM notifications
                WHERE user_id = %s AND issue_id = %s AND date_created = %s AND old_value = %s AND new_value = %s
            """
            existing_notification = execute_query(
                cursor, check_query, (current_user_id, issue_id, date_created, old_value, new_value)
            )

            if existing_notification:
                log.debug(
                    f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Уведомление уже существует для IssueID={issue_id}, DateCreated={date_created}"
                )
                continue

            # Создаем новое уведомление
            insert_query = """
                INSERT INTO notifications (user_id, issue_id, date_created, old_value, new_value, author, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """
            cursor.execute(
                insert_query,
                (current_user_id, issue_id, date_created, old_value, new_value, author),
            )
            processed_in_this_run += 1
            processed_ids_in_this_run.append(row["id"])

            log.debug(
                f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Создано уведомление для IssueID={issue_id}, Author={author}"
            )

        except Exception as e:
            error_msg = f"Ошибка при обработке записи ID={row['id']}: {e}"
            log.error(
                f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: {error_msg}",
                exc_info=True,
            )
            errors_in_this_run_status.append(error_msg)

    end_time_func = time.time()
    log.info(
        f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}, EmailPart={email_part}, EasyEmailTo={easy_email_to}: ЗАВЕРШЕНИЕ обработки. Обработано: {processed_in_this_run}. ID для MySQL удаления: {processed_ids_in_this_run}. Ошибки: {len(errors_in_this_run_status)}. Время: {end_time_func - start_time_func:.2f} сек."
    )
    return processed_in_this_run, processed_ids_in_this_run, errors_in_this_run_status


def check_notifications(user_email, current_user_id):
    from redmine_db import get_connection, db_redmine_host, db_redmine_user_name, db_redmine_password, db_redmine_name, db_redmine_port

    if not FLASK_AVAILABLE:
        logger.warning("Flask not available - returning empty results")
        return {
            "status_changes": 0,
            "added_notes": 0,
            "total_processed": 0,
            "errors": ["Flask not available"],
        }

    logger_main = current_app.logger
    run_id = uuid.uuid4()
    start_time_check = time.time()
    logger_main.info(
        f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}, Email={user_email}: НАЧАЛО проверки уведомлений."
    )

    connection_db = None
    cursor = None
    newly_processed_count = 0
    # Возвращаем словарь с деталями, включая ошибки
    processed_details = {
        "status_changes": 0,
        "added_notes": 0,
        "total_processed": 0,
        "errors": [],
    }

    try:
        logger_main.debug(
            f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Попытка подключения к Redmine DB: host={db_redmine_host}, db={db_redmine_name}"
        )
        connect_start_time = time.time()
        connection_db = get_connection(
            db_redmine_host, db_redmine_user_name, db_redmine_password, db_redmine_name, port=db_redmine_port
        )
        connect_end_time = time.time()
        if connection_db is None:
            logger_main.error(
                f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: НЕ УДАЛОСЬ подключиться к Redmine DB. Время: {connect_end_time - connect_start_time:.2f} сек."
            )
            processed_details["errors"].append("Redmine DB connection failed")
        else:
            logger_main.info(
                f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Успешное подключение к Redmine DB. Время: {connect_end_time - connect_start_time:.2f} сек."
            )

            cursor_start_time = time.time()
            cursor = get_database_cursor(connection_db)
            cursor_end_time = time.time()
            if cursor is None:
                logger_main.error(
                    f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: НЕ УДАЛОСЬ получить курсор для Redmine DB. Время: {cursor_end_time - cursor_start_time:.2f} сек."
                )
                processed_details["errors"].append("Redmine DB cursor failed")
            else:
                logger_main.debug(
                    f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Курсор Redmine DB получен. Время: {cursor_end_time - cursor_start_time:.2f} сек."
                )

                email_part = (
                    user_email.split("@")[0] if "@" in user_email else user_email
                )

                logger_main.info(
                    f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Начало обработки status_changes."
                )
                process_status_start_time = time.time()
                # Передаем user_email как easy_email_to
                s_count, s_ids, s_errors = process_status_changes(
                    connection_db, cursor, email_part, current_user_id, user_email
                )
                process_status_end_time = time.time()
                logger_main.info(
                    f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Завершена обработка status_changes. Найдено: {s_count}. Время: {process_status_end_time - process_status_start_time:.2f} сек."
                )
                processed_details["status_changes"] = s_count
                if s_errors:
                    processed_details["errors"].extend(s_errors)

                if s_count > 0:
                    newly_processed_count += s_count
                    logger_main.info(
                        f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Попытка удаления {len(s_ids)} обработанных status_changes из Redmine DB ID: {s_ids}"
                    )
                    delete_start_time = time.time()
                    delete_notifications(connection_db, s_ids)
                    delete_end_time = time.time()
                    logger_main.info(
                        f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Завершено удаление status_changes. Время: {delete_end_time - delete_start_time:.2f} сек."
                    )

                logger_main.info(
                    f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Начало обработки added_notes."
                )
                process_notes_start_time = time.time()
                n_count, n_ids, n_errors = process_added_notes(
                    cursor, email_part, current_user_id, user_email
                )
                process_notes_end_time = time.time()
                logger_main.info(
                    f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Завершена обработка added_notes. Найдено: {n_count}. Время: {process_notes_end_time - process_notes_start_time:.2f} сек."
                )
                processed_details["added_notes"] = n_count
                if n_errors:
                    processed_details["errors"].extend(n_errors)

                if n_count > 0:
                    newly_processed_count += n_count
                    logger_main.info(
                        f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Попытка удаления {len(n_ids)} обработанных added_notes из Redmine DB ID: {n_ids}"
                    )
                    delete_start_time = time.time()
                    delete_notifications_notes(connection_db, n_ids)
                    delete_end_time = time.time()
                    logger_main.info(
                        f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Завершено удаление added_notes. Время: {delete_end_time - delete_start_time:.2f} сек."
                    )

        processed_details["total_processed"] = newly_processed_count

    except Exception as e:
        if PYMYSQL_AVAILABLE:
            logger_main.error(
                f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}, Email={user_email}: ГЛОБАЛЬНАЯ ОШИБКА. {e}",
                exc_info=True,
            )
        else:
            logger_main.error(
                f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}, Email={user_email}: ГЛОБАЛЬНАЯ ОШИБКА. {e}"
            )
        processed_details["errors"].append(
            f"Global error in check_notifications: {str(e)}"
        )
    finally:
        if cursor:
            try:
                cursor.close()
                logger_main.debug(
                    f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Курсор Redmine DB закрыт."
                )
            except Exception as e_cursor:
                logger_main.error(
                    f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Ошибка при закрытии курсора Redmine DB: {e_cursor}",
                    exc_info=True,
                )
        if connection_db:
            try:
                connection_db.close()
                logger_main.debug(
                    f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Соединение Redmine DB закрыто."
                )
            except Exception as e_conn:
                logger_main.error(
                    f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}: Ошибка при закрытии соединения Redmine DB: {e_conn}",
                    exc_info=True,
                )

    # Код после finally блока - завершение функции
    end_time_check = time.time()
    logger_main.info(
        f"CHECK_NOTIFICATIONS_RUN_ID={run_id}: UserID={current_user_id}, Email={user_email}: ЗАВЕРШЕНИЕ проверки уведомлений. Обработано: {processed_details['total_processed']}. Ошибки: {len(processed_details['errors'])}. Время: {end_time_check - start_time_check:.2f} сек."
    )
    return processed_details


def get_count_notifications(user_id):
    """Количество уведомлений об изменении статуса заявки"""
    if not MODELS_AVAILABLE:
        logger.warning("Models not available - returning 0")
        return 0

    # Получаем notifications
    notifications_data = Notifications.query.filter_by(user_id=user_id).all()
    notifications_count = len(notifications_data)
    return notifications_count


def get_count_notifications_add_notes(user_id):
    """Количество уведомлений о добавлении комментария в заявку"""
    if not MODELS_AVAILABLE:
        logger.warning("Models not available - returning 0")
        return 0

    # Получаем notifications
    notifications_add_notes_data = NotificationsAddNotes.query.filter_by(
        user_id=user_id
    ).all()
    notifications_add_notes_count = len(notifications_add_notes_data)
    return notifications_add_notes_count


def process_added_notes(cursor, email_part, current_user_id, easy_email_to):
    if not FLASK_AVAILABLE:
        logger.warning("Flask not available - returning empty results")
        return 0, [], []

    log = current_app.logger
    run_id = uuid.uuid4()
    func_name = "PROCESS_ADDED_NOTES"
    start_time_func = time.time()
    log.info(
        f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}, EmailPart={email_part}, EasyEmailTo={easy_email_to}: НАЧАЛО обработки."
    )

    query_added_notes = """
        SELECT id, issue_id, date_created, Notes, Author, RowDateCreated
        FROM u_its_add_notes
        WHERE LOWER(Author) = LOWER(%s) # Возвращаем easy_email_to (полный email)
        ORDER BY RowDateCreated DESC LIMIT 50
    """
    log.debug(
        f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: SQL Query to Redmine u_its_add_notes for Author='{easy_email_to}'"
    )

    query_start_time = time.time()
    from redmine_db import execute_query
    rows_added_notes = execute_query(
        cursor, query_added_notes, (easy_email_to,)
    )  # Возвращаем easy_email_to
    query_end_time = time.time()

    if rows_added_notes is None:
        log.error(
            f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Ошибка SQL-запроса к u_its_add_notes. Время: {query_end_time - query_start_time:.2f} сек."
        )
        return (
            0,
            [],
            [f"Ошибка SQL-запроса к u_its_add_notes для Author='{easy_email_to}'"],
        )

    if not rows_added_notes:
        log.info(
            f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Нет записей в u_its_add_notes для Author='{easy_email_to}'. Время: {query_end_time - query_start_time:.2f} сек."
        )
        return 0, [], []

    log.info(
        f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Найдено {len(rows_added_notes)} записей в u_its_add_notes для Author='{easy_email_to}'. Время: {query_end_time - query_start_time:.2f} сек."
    )

    processed_in_this_run = 0
    processed_ids_in_this_run = []
    errors_in_this_run_notes = []

    for row in rows_added_notes:
        try:
            issue_id = row["issue_id"]
            date_created = row["date_created"]
            notes = row["Notes"]
            author = row["Author"]
            row_date_created = row["RowDateCreated"]

            log.debug(
                f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Обработка записи ID={row['id']}, IssueID={issue_id}, Author={author}"
            )

            # Проверяем, существует ли уже уведомление для этой записи
            check_query = """
                SELECT id FROM notifications_add_notes
                WHERE user_id = %s AND issue_id = %s AND date_created = %s AND notes = %s
            """
            existing_notification = execute_query(
                cursor, check_query, (current_user_id, issue_id, date_created, notes)
            )

            if existing_notification:
                log.debug(
                    f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Уведомление уже существует для IssueID={issue_id}, DateCreated={date_created}"
                )
                continue

            # Создаем новое уведомление
            insert_query = """
                INSERT INTO notifications_add_notes (user_id, issue_id, date_created, notes, author, row_date_created, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """
            cursor.execute(
                insert_query,
                (current_user_id, issue_id, date_created, notes, author, row_date_created),
            )
            processed_in_this_run += 1
            processed_ids_in_this_run.append(row["id"])

            log.debug(
                f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: Создано уведомление для IssueID={issue_id}, Author={author}"
            )

        except Exception as e:
            error_msg = f"Ошибка при обработке записи ID={row['id']}: {e}"
            log.error(
                f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}: {error_msg}",
                exc_info=True,
            )
            errors_in_this_run_notes.append(error_msg)

    end_time_func = time.time()
    log.info(
        f"{func_name}_RUN_ID={run_id}: UserID={current_user_id}, EmailPart={email_part}, EasyEmailTo={easy_email_to}: ЗАВЕРШЕНИЕ обработки. Обработано: {processed_in_this_run}. ID для MySQL удаления: {processed_ids_in_this_run}. Ошибки: {len(errors_in_this_run_notes)}. Время: {end_time_func - start_time_func:.2f} сек."
    )
    return processed_in_this_run, processed_ids_in_this_run, errors_in_this_run_notes


def delete_notifications(connection, ids_to_delete):
    try:
        log = current_app.logger
    except RuntimeError:
        log = logger
    run_id = uuid.uuid4()
    func_name = "DELETE_NOTIFICATIONS_STATUS"
    start_time = time.time()

    if not ids_to_delete:
        log.info(f"{func_name}_RUN_ID={run_id}: Список ID для удаления пуст.")
        return 0

    log.info(
        f"{func_name}_RUN_ID={run_id}: НАЧАЛО удаления {len(ids_to_delete)} записей из u_its_update_status. IDs: {ids_to_delete}"
    )
    cursor = None
    try:
        cursor = connection.cursor()
        placeholders = ", ".join(["%s"] * len(ids_to_delete))
        query = f"DELETE FROM u_its_update_status WHERE id IN ({placeholders})"
        log.debug(
            f"{func_name}_RUN_ID={run_id}: SQL='{query}', IDs={tuple(ids_to_delete)}"
        )

        cursor.execute(query, tuple(ids_to_delete))
        connection.commit()
        deleted_count = cursor.rowcount
        end_time = time.time()
        log.info(
            f"{func_name}_RUN_ID={run_id}: Успешно удалено {deleted_count} записей. IDs: {ids_to_delete}. Время: {end_time - start_time:.2f} сек."
        )
        return deleted_count
    except Exception as e:
        end_time = time.time()
        log.error(
            f"{func_name}_RUN_ID={run_id}: ОШИБКА pymysql. {e}. IDs: {ids_to_delete}. Время: {end_time - start_time:.2f} сек.",
            exc_info=True,
        )
        if connection:
            connection.rollback()
        return 0
    finally:
        if cursor:
            cursor.close()


def delete_notifications_notes(connection, ids_to_delete):
    try:
        log = current_app.logger
    except RuntimeError:
        log = logger
    run_id = uuid.uuid4()
    func_name = "DELETE_NOTIFICATIONS_NOTES"
    start_time = time.time()

    if not ids_to_delete:
        log.info(f"{func_name}_RUN_ID={run_id}: Список ID для удаления пуст.")
        return 0

    log.info(
        f"{func_name}_RUN_ID={run_id}: НАЧАЛО удаления {len(ids_to_delete)} записей из u_its_add_notes. IDs: {ids_to_delete}"
    )
    cursor = None
    try:
        cursor = connection.cursor()
        placeholders = ", ".join(["%s"] * len(ids_to_delete))
        query = f"DELETE FROM u_its_add_notes WHERE id IN ({placeholders})"
        log.debug(
            f"{func_name}_RUN_ID={run_id}: SQL='{query}', IDs={tuple(ids_to_delete)}"
        )

        cursor.execute(query, tuple(ids_to_delete))
        connection.commit()
        deleted_count = cursor.rowcount
        end_time = time.time()
        log.info(
            f"{func_name}_RUN_ID={run_id}: Успешно удалено {deleted_count} записей. IDs: {ids_to_delete}. Время: {end_time - start_time:.2f} сек."
        )
        return deleted_count
    except Exception as e:
        end_time = time.time()
        log.error(
            f"{func_name}_RUN_ID={run_id}: ОШИБКА pymysql. {e}. IDs: {ids_to_delete}. Время: {end_time - start_time:.2f} сек.",
            exc_info=True,
        )
        if connection:
            connection.rollback()
        return 0
    finally:
        if cursor:
            cursor.close()
