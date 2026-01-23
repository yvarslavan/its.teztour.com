"""
Redmine Utilities Module
Contains utility functions, data processing, and helper functions.
"""

import logging
import time
import uuid
from datetime import timedelta, datetime
import pytz

# Создаем объект логгера
logger = logging.getLogger(__name__)


def convert_datetime_msk_format(input_datetime, redmine_timezone_str="Europe/Moscow"):
    """
    Конвертирует datetime в формат МСК с учетом часового пояса Redmine.

    Args:
        input_datetime: Входная дата и время
        redmine_timezone_str: Часовой пояс Redmine (по умолчанию Europe/Moscow)

    Returns:
        str: Отформатированная строка даты и времени
    """
    output_format = "%d.%m.%Y %H:%M"

    # Устанавливаем часовой пояс сервера Redmine
    redmine_timezone = pytz.timezone(redmine_timezone_str)
    input_datetime = input_datetime.astimezone(redmine_timezone) + timedelta(
        hours=3
    )  # Прибавляем 3 часа для МСК
    return input_datetime.strftime(output_format)


def get_multiple_user_names(connection, user_ids):
    """
    Пакетная загрузка имен пользователей из Redmine.

    Args:
        connection: Соединение с базой данных
        user_ids: Список ID пользователей

    Returns:
        dict: Словарь {user_id: full_name}
    """
    if not user_ids or not connection:
        return {}

    # Удаляем дубликаты и None значения
    clean_ids = list(set(filter(None, user_ids)))
    if not clean_ids:
        return {}

    cursor = None
    try:
        cursor = connection.cursor()
        placeholders = ", ".join(["%s"] * len(clean_ids))
        query = f"""
            SELECT id, firstname, lastname
            FROM redmine.users
            WHERE id IN ({placeholders})
        """

        cursor.execute(query, tuple(clean_ids))
        results = cursor.fetchall()

        user_names = {}
        for row in results:
            full_name = f"{row['firstname']} {row['lastname']}".strip()
            user_names[row['id']] = full_name

        logger.info(
            "Загружено %s имен пользователей из %s запрошенных",
            len(user_names), len(clean_ids)
        )
        return user_names

    except Exception as e:
        logger.error("Ошибка при пакетной загрузке имен пользователей: %s", e)
        return {}
    finally:
        if cursor:
            cursor.close()


def get_multiple_project_names(connection, project_ids):
    """
    Пакетная загрузка названий проектов из Redmine.

    Args:
        connection: Соединение с базой данных
        project_ids: Список ID проектов

    Returns:
        dict: Словарь {project_id: name}
    """
    if not project_ids or not connection:
        return {}

    clean_ids = list(set(filter(None, project_ids)))
    if not clean_ids:
        return {}

    cursor = None
    try:
        cursor = connection.cursor()
        placeholders = ", ".join(["%s"] * len(clean_ids))
        query = f"""
            SELECT id, name
            FROM redmine.projects
            WHERE id IN ({placeholders})
        """

        cursor.execute(query, tuple(clean_ids))
        results = cursor.fetchall()

        project_names = {}
        for row in results:
            project_names[row['id']] = row['name']

        logger.info(
            "Загружено %s названий проектов из %s запрошенных",
            len(project_names), len(clean_ids)
        )
        return project_names

    except Exception as e:
        logger.error("Ошибка при пакетной загрузке названий проектов: %s", e)
        return {}
    finally:
        if cursor:
            cursor.close()


def get_multiple_status_names(connection, status_ids):
    """
    Пакетная загрузка названий статусов из Redmine.

    Args:
        connection: Соединение с базой данных
        status_ids: Список ID статусов

    Returns:
        dict: Словарь {status_id: name}
    """
    if not status_ids or not connection:
        return {}

    clean_ids = list(set(filter(None, status_ids)))
    if not clean_ids:
        return {}

    cursor = None
    try:
        cursor = connection.cursor()
        placeholders = ", ".join(["%s"] * len(clean_ids))
        query = f"""
            SELECT id, name
            FROM redmine.issue_statuses
            WHERE id IN ({placeholders})
        """

        cursor.execute(query, tuple(clean_ids))
        results = cursor.fetchall()

        status_names = {}
        for row in results:
            status_names[row['id']] = row['name']

        logger.info(
            "Загружено %s названий статусов из %s запрошенных",
            len(status_names), len(clean_ids)
        )
        return status_names

    except Exception as e:
        logger.error("Ошибка при пакетной загрузке названий статусов: %s", e)
        return {}
    finally:
        if cursor:
            cursor.close()


def get_multiple_priority_names(connection, priority_ids):
    """
    Пакетная загрузка названий приоритетов из Redmine.

    Args:
        connection: Соединение с базой данных
        priority_ids: Список ID приоритетов

    Returns:
        dict: Словарь {priority_id: name}
    """
    if not priority_ids or not connection:
        return {}

    clean_ids = list(set(filter(None, priority_ids)))
    if not clean_ids:
        return {}

    cursor = None
    try:
        cursor = connection.cursor()
        placeholders = ", ".join(["%s"] * len(clean_ids))
        query = f"""
            SELECT id, name
            FROM redmine.enumerations
            WHERE type = 'IssuePriority' AND id IN ({placeholders})
        """

        cursor.execute(query, tuple(clean_ids))
        results = cursor.fetchall()

        priority_names = {}
        for row in results:
            priority_names[row['id']] = row['name']

        logger.info(
            "Загружено %s названий приоритетов из %s запрошенных",
            len(priority_names), len(clean_ids)
        )
        return priority_names

    except Exception as e:
        logger.error("Ошибка при пакетной загрузке названий приоритетов: %s", e)
        return {}
    finally:
        if cursor:
            cursor.close()


def generate_optimized_property_names(connection, issue_history):
    """
    Генерирует предопределенные описания для свойств заявок.

    Args:
        connection: Соединение с базой данных
        issue_history: История изменений заявки

    Returns:
        dict: Словарь с предгенерированными описаниями изменений
        Ключ: "{property}:{name}:{old_value}:{new_value}"
        Значение: HTML-описание изменения
    """
    if not issue_history:
        return {}

    # Собираем все уникальные ID для пакетной загрузки
    user_ids = set()
    project_ids = set()
    status_ids = set()
    priority_ids = set()

    # Проходим по всей истории и собираем ID
    for journal_entry in issue_history:
        if 'details' in journal_entry and journal_entry['details']:
            for detail in journal_entry['details']:
                if detail.get('property') == 'attr':
                    if detail.get('name') == 'assigned_to_id':
                        old_val = detail.get('old_value')
                        new_val = detail.get('new_value')
                        if old_val:
                            user_ids.add(int(old_val))
                        if new_val:
                            user_ids.add(int(new_val))
                    elif detail.get('name') == 'status_id':
                        old_val = detail.get('old_value')
                        new_val = detail.get('new_value')
                        if old_val:
                            status_ids.add(int(old_val))
                        if new_val:
                            status_ids.add(int(new_val))
                    elif detail.get('name') == 'priority_id':
                        old_val = detail.get('old_value')
                        new_val = detail.get('new_value')
                        if old_val:
                            priority_ids.add(int(old_val))
                        if new_val:
                            priority_ids.add(int(new_val))

    # Добавляем автора и исполнителя из основной информации
    for entry in issue_history:
        if 'user' in entry and entry['user']:
            user_ids.add(entry['user']['id'])
        if 'issue' in entry and entry['issue'].get('assigned_to'):
            user_ids.add(entry['issue']['assigned_to']['id'])
        if 'issue' in entry and entry['issue'].get('project'):
            project_ids.add(entry['issue']['project']['id'])

    logger.info(
        "Начинаем пакетную загрузку: users=%s, projects=%s, statuses=%s, priorities=%s",
        len(user_ids), len(project_ids), len(status_ids), len(priority_ids)
    )

    user_names = get_multiple_user_names(connection, list(user_ids))
    project_names = get_multiple_project_names(connection, list(project_ids))
    status_names = get_multiple_status_names(connection, list(status_ids))
    priority_names = get_multiple_priority_names(connection, list(priority_ids))

    # Генерируем описания изменений
    property_descriptions = {}

    for journal_entry in issue_history:
        if 'details' in journal_entry and journal_entry['details']:
            for detail in journal_entry['details']:
                if detail.get('property') == 'attr':
                    prop_name = detail.get('name')
                    old_val = detail.get('old_value')
                    new_val = detail.get('new_value')

                    cache_key = f"{prop_name}:{old_val}:{new_val}"
                    if cache_key in property_descriptions:
                        continue  # Уже есть в кеше

                    # Генерируем описание в зависимости от типа свойства
                    if prop_name == 'assigned_to_id':
                        old_name = user_names.get(int(old_val), 'Неизвестный') if old_val else 'Нobody'
                        new_name = user_names.get(int(new_val), 'Неизвестный') if new_val else 'Нobody'
                        result = f"Исполнитель изменен с <strong>{old_name}</strong> на <strong>{new_name}</strong>"
                    elif prop_name == 'status_id':
                        old_name = status_names.get(int(old_val), 'Неизвестный') if old_val else 'None'
                        new_name = status_names.get(int(new_val), 'Неизвестный') if new_val else 'None'
                        result = f"Статус изменен с <strong>{old_name}</strong> на <strong>{new_name}</strong>"
                    elif prop_name == 'priority_id':
                        old_name = priority_names.get(int(old_val), 'Неизвестный') if old_val else 'None'
                        new_name = priority_names.get(int(new_val), 'Неизвестный') if new_val else 'None'
                        result = f"Приоритет изменен с <strong>{old_name}</strong> на <strong>{new_name}</strong>"
                    else:
                        result = f"Атрибут <strong>{prop_name}</strong> изменен с <strong>{old_val}</strong> на <strong>{new_val}</strong>"

                    # Сохраняем результат в кеш
                    if result:
                        property_descriptions[cache_key] = result

    logger.info("Сгенерировано %s описаний изменений", len(property_descriptions))
    return property_descriptions


def determine_activity_type(property_name, prop_key, _old_value, _value, notes):
    """
    Определение типа активности на основе данных из journals

    Returns:
        tuple: (activity_type, activity_icon, activity_text)
    """
    # Если есть комментарий (notes)
    if notes and notes.strip():
        return ("comment", "💬", "Добавлен комментарий")

    # Если это изменение атрибута
    if property_name == "attr":
        if prop_key == "status_id":
            return ("status", "🔄", "Изменен статус")
        elif prop_key == "priority_id":
            return ("priority", "⚡", "Изменен приоритет")
        elif prop_key == "assigned_to_id":
            return ("assigned", "👤", "Изменен исполнитель")
        elif prop_key == "description":
            return ("description", "📝", "Изменено описание")
        elif prop_key == "subject":
            return ("subject", "📋", "Изменена тема")
        elif prop_key == "due_date":
            return ("due_date", "📅", "Изменен срок выполнения")
        elif prop_key == "estimated_hours":
            return ("estimated", "⏱️", "Изменена оценка времени")
        elif prop_key == "done_ratio":
            return ("progress", "📊", "Изменен прогресс")
        elif prop_key == "start_date":
            return ("start_date", "🚀", "Изменена дата начала")
        else:
            return ("attr", "🔧", f"Изменен атрибут: {prop_key}")
    else:
        # Для других типов изменений
        return ("other", "🔄", "Изменение")
