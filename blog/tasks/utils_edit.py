# blog/tasks/utils.py
import traceback
import os
from flask import current_app
from flask import request
from datetime import date, datetime

# Импорты из корневой директории проекта
from redmine import RedmineConnector # Исправленный импорт

# ANONYMOUS_USER_ID будет браться из get('redmine', 'api_key') в create_redmine_connector для анонимных случаев,
# или должен быть получен через get('redmine', 'anonymous_user_id') если нужен именно ID.
# Пока что логика create_redmine_connector полагается на общий api_key для "анонимов".

def create_redmine_connector(is_redmine_user, user_login, password=None, api_key_param=None):
    url = os.getenv('REDMINE_URL')
    effective_api_key = api_key_param

    if not is_redmine_user and not api_key_param:
        effective_api_key = os.getenv('REDMINE_API_KEY')

    if is_redmine_user:
        return RedmineConnector(
            url=url,
            username=user_login,
            password=password,
            api_key=effective_api_key
        )
    else:
        return RedmineConnector(
            url=url,
            username=None,
            password=None,
            api_key=effective_api_key
        )

def get_redmine_connector(current_user_obj, user_password_erp):
    """Получение экземпляра RedmineConnector. current_user_obj - это объект current_user"""
    password_to_use = user_password_erp if user_password_erp else None

    redmine_conn = create_redmine_connector(
        is_redmine_user=current_user_obj.is_redmine_user,
        user_login=current_user_obj.username,
        password=password_to_use,
        api_key_param=None
    )
    return redmine_conn

def format_issue_date(date_obj):
    if not date_obj:
        return ''
    try:
        if isinstance(date_obj, datetime):
            return date_obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(date_obj, date):
            return date_obj.strftime('%Y-%m-%d')
        elif isinstance(date_obj, str):
            try:
                dt_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))
                return dt_obj.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    dt_obj = datetime.strptime(date_obj, '%Y-%m-%d')
                    return dt_obj.strftime('%Y-%m-%d')
                except ValueError:
                    return date_obj
        else:
            return str(date_obj)
    except Exception as e:
        current_app.logger.error(f"Ошибка форматирования даты '{date_obj}': {str(e)}")
        return str(date_obj)


def task_to_dict(issue):
    try:
        task_data = {
            'id': issue.id,
            'subject': getattr(issue, 'subject', ''),
            'status': {
                'id': issue.status.id if hasattr(issue, 'status') and issue.status else None,
                'name': issue.status.name if hasattr(issue, 'status') and issue.status else 'Неизвестен'
            },
            'priority': {
                'id': issue.priority.id if hasattr(issue, 'priority') and issue.priority else None,
                'name': issue.priority.name if hasattr(issue, 'priority') and issue.priority else 'Обычный'
            },
            'project': {
                'id': issue.project.id if hasattr(issue, 'project') and issue.project else None,
                'name': issue.project.name if hasattr(issue, 'project') and issue.project else 'Без проекта'
            },
            'tracker': {
                'id': issue.tracker.id if hasattr(issue, 'tracker') and issue.tracker else None,
                'name': issue.tracker.name if hasattr(issue, 'tracker') and issue.tracker else 'Без трекера'
            },
            'author': {
                'id': issue.author.id if hasattr(issue, 'author') and issue.author else None,
                'name': issue.author.name if hasattr(issue, 'author') and issue.author else 'Аноним'
            },
            'assigned_to': {
                'id': issue.assigned_to.id if hasattr(issue, 'assigned_to') and issue.assigned_to else None,
                'name': issue.assigned_to.name if hasattr(issue, 'assigned_to') and issue.assigned_to else 'Не назначен'
            },
            'created_on': format_issue_date(getattr(issue, 'created_on', None)),
            'updated_on': format_issue_date(getattr(issue, 'updated_on', None)),
            'start_date': format_issue_date(getattr(issue, 'start_date', None)),
            'due_date': format_issue_date(getattr(issue, 'due_date', None)),
            'closed_on': format_issue_date(getattr(issue, 'closed_on', None)),
            'done_ratio': getattr(issue, 'done_ratio', 0),
            'estimated_hours': getattr(issue, 'estimated_hours', None),
            'spent_hours': getattr(issue, 'spent_hours', None),
            'description': getattr(issue, 'description', '')[:1000]
        }

        custom_fields_data = {}
        if hasattr(issue, 'custom_fields'):
            for field in issue.custom_fields:
                field_value_attr = getattr(field, 'value', None)
                field_value = str(field_value_attr) if field_value_attr is not None else ''
                custom_fields_data[field.name] = field_value


        task_data['custom_fields'] = custom_fields_data
        task_data['status_name'] = task_data['status']['name']
        task_data['priority_name'] = task_data['priority']['name']
        task_data['project_name'] = task_data['project']['name']
        task_data['tracker_name'] = task_data['tracker']['name'] if task_data.get('tracker') else 'N/A'
        task_data['author_name'] = task_data['author']['name'] if task_data.get('author') else 'N/A'
        task_data['assigned_to_name'] = task_data['assigned_to']['name'] if task_data.get('assigned_to') else 'N/A'

        return task_data
    except AttributeError as e:
        current_app.logger.warning(f"AttributeError при преобразовании задачи {getattr(issue, 'id', 'unknown')}: {str(e)}. Поля: {dir(issue) if issue else 'No issue'}")
        fallback_id = getattr(issue, 'id', 0)
        return {
            'id': fallback_id, 'subject': f'Ошибка данных для задачи #{fallback_id}',
            'status_name': 'Ошибка', 'priority_name': 'Ошибка', 'project_name': 'Ошибка',
            'description': f'Произошла ошибка атрибута при обработке задачи: {str(e)}',
            'error': True, 'error_details': str(e),
            'created_on':'', 'updated_on':'', 'assigned_to_name': ''
        }
    except Exception as e:
        current_app.logger.error(f"Критическая ошибка преобразования задачи {getattr(issue, 'id', 'unknown')}: {str(e)}. Trace: {traceback.format_exc()}")
        return {
            'id': getattr(issue, 'id', 0),
            'subject': f'Критическая ошибка обработки задачи #{getattr(issue, "id", "unknown")}',
            'status_name': 'Ошибка', 'error': True,
            'error_message': 'Критическая ошибка на сервере при обработке данных задачи.',
            'original_exception': str(e),
            'created_on':'', 'updated_on':'', 'assigned_to_name': ''
        }

def get_accurate_task_count(redmine_connector, filter_params):
    try:
        count_params = filter_params.copy()
        count_params.pop('limit', None)
        count_params.pop('offset', None)
        count_params.pop('include', None)

        issues_for_count = redmine_connector.redmine.issue.filter(**count_params)
        if hasattr(issues_for_count, 'total_count') and isinstance(issues_for_count.total_count, int):
             actual_count = issues_for_count.total_count
             current_app.logger.info(f"Точный подсчет задач (атрибут total_count): {actual_count} для фильтров: {count_params}")
             return actual_count
        else:
            current_app.logger.warning(f"Атрибут total_count отсутствует или не int. Попытка подсчета через list() с лимитом. Фильтры: {count_params}")
            count_params_limited = count_params.copy()
            count_params_limited['limit'] = 1001

            try:
                issues_list_for_count = redmine_connector.redmine.issue.filter(**count_params_limited)
                count = 0
                for _ in issues_list_for_count:
                    count += 1
                    if count >= count_params_limited['limit']:
                        break

                current_app.logger.info(f"Подсчет задач (через итерацию, лимит {count_params_limited['limit']}): {count}")
                if count == count_params_limited['limit']:
                     current_app.logger.warning(f"Достигнут лимит в {count_params_limited['limit']} при подсчете, общее количество может быть больше.")
                return count
            except Exception as e_list_count:
                current_app.logger.error(f"Ошибка при подсчете задач через list(): {e_list_count}")
                return None

    except Exception as e:
        current_app.logger.warning(f"Ошибка точного подсчета: {str(e)}. Trace: {traceback.format_exc()}")
        return None

def get_user_assigned_tasks_paginated_optimized(
        redmine_connector, redmine_user_id, page=1, per_page=25,
        search_term='', sort_column='updated_on', sort_direction='desc',
        status_ids=None, priority_ids=None, project_ids=None,
        advanced_search_enabled=False
    ):
    try:
        # НОВЫЙ КОД: Обработка параметров фильтрации по имени
        status_name = request.args.get('status_name', '')
        project_name = request.args.get('project_name', '')
        priority_name = request.args.get('priority_name', '')

        current_app.logger.info(f"🔍 [FILTER_DEBUG] Получены новые параметры: status_name='{status_name}', project_name='{project_name}', priority_name='{priority_name}'")

        # НОВЫЙ КОД: Переменная для отслеживания, нужна ли фильтрация на стороне Python
        use_python_filtering = False
        python_filters = {}

        # НОВЫЙ КОД: Проверка наличия новых параметров фильтрации
        if status_name:
            current_app.logger.info(f"🔍 [FILTER_DEBUG] Обнаружен фильтр по имени статуса: '{status_name}'")
            python_filters['status_name'] = status_name
            use_python_filtering = True

        if project_name:
            current_app.logger.info(f"🔍 [FILTER_DEBUG] Обнаружен фильтр по имени проекта: '{project_name}'")
            python_filters['project_name'] = project_name
            use_python_filtering = True

        if priority_name:
            current_app.logger.info(f"🔍 [FILTER_DEBUG] Обнаружен фильтр по имени приоритета: '{priority_name}'")
            python_filters['priority_name'] = priority_name
            use_python_filtering = True

        current_app.logger.info(f"Получение задач: user_id={redmine_user_id}, page={page}, per_page={per_page}, search='{search_term}', sort='{sort_column}:{sort_direction}', statuses={status_ids}, projects={project_ids}, priorities={priority_ids}")
        per_page = min(max(1, per_page), 100)

        filter_params = {
            'assigned_to_id': redmine_user_id,
            'sort': f'{sort_column}:{sort_direction}',
            'limit': per_page,
            'offset': (page - 1) * per_page,
            'include': ['status', 'priority', 'project', 'tracker', 'author', 'description']  # Добавляем description для поиска
        }

        # КАРДИНАЛЬНОЕ ИСПРАВЛЕНИЕ #4: Если поиск по тексту, игнорируем Redmine фильтры и делаем поиск на стороне Python
        use_python_only_search = False
        if search_term:
            search_encoded = search_term.strip()
            if search_encoded.isdigit():
                # Поиск по ID задачи - используем Redmine фильтр
                filter_params['issue_id'] = search_encoded
                current_app.logger.info(f"🔍 ОТЛАДКА: Поиск по ID задачи: {search_encoded}")
            elif search_encoded.startswith('#') and search_encoded[1:].isdigit():
                # Поиск по ID задачи с символом # - используем Redmine фильтр
                filter_params['issue_id'] = search_encoded[1:]
                current_app.logger.info(f"🔍 ОТЛАДКА: Поиск по ID задачи (с #): {search_encoded[1:]}")
            else:
                # Поиск по тексту - НЕ используем Redmine фильтры, делаем на стороне Python
                use_python_only_search = True
                current_app.logger.info(f"🔍 ОТЛАДКА: ТЕКСТОВЫЙ ПОИСК '{search_encoded}' - будем загружать ВСЕ задачи и фильтровать на Python")

        current_app.logger.debug(f"Итоговые фильтры Redmine REST API: {filter_params}")
        current_app.logger.info(f"🔍 ОТЛАДКА: use_python_only_search = {use_python_only_search}, use_python_filtering = {use_python_filtering}")

        # ОБНОВЛЕНО: Объединение логики текстового поиска и фильтрации по имени
        use_python_search_or_filter = use_python_only_search or use_python_filtering

        # Выполняем запрос к Redmine REST API
        if use_python_search_or_filter:
            # Для текстового поиска или фильтрации по имени: загружаем БОЛЬШЕ задач
            filter_params_for_python = filter_params.copy()
            filter_params_for_python['limit'] = 200  # Увеличиваем лимит для поиска/фильтрации
            filter_params_for_python['offset'] = 0   # Сбрасываем offset для поиска/фильтрации

            current_app.logger.info(f"🔍 ОТЛАДКА: Загружаем {filter_params_for_python['limit']} задач для обработки на Python")
            issues_page = redmine_connector.redmine.issue.filter(**filter_params_for_python)
        else:
            # Обычный поиск по ID или без поиска
            current_app.logger.info(f"🔍 ОТЛАДКА: Выполняем стандартный запрос к Redmine")
            issues_page = redmine_connector.redmine.issue.filter(**filter_params)

        issues_list_initial = list(issues_page)
        current_app.logger.info(f"🔍 ОТЛАДКА: Получено {len(issues_list_initial)} задач от Redmine API")

        # ОБЪЕДИНЕННАЯ PYTHON-ФИЛЬТРАЦИЯ: Для текстового поиска и фильтрации по имени
        if use_python_search_or_filter:
            current_app.logger.info(f"🔍 ОТЛАДКА: ЗАПУСК Python-фильтрации")
            issues_list_filtered = []

            # Подготавливаем параметры поиска
            search_term_lower = search_term.lower() if search_term else None

            for issue in issues_list_initial:
                # По умолчанию задача проходит фильтр
                include_issue = True

                # ПРОВЕРКА ПОИСКА: Если есть поисковый запрос, проверяем его
                if use_python_only_search and search_term_lower:
                    # Поля для текстового поиска
                    fields_to_search = [
                        getattr(issue, 'subject', ''),
                        getattr(issue, 'description', ''),
                    ]

                    # Проверяем, содержится ли поисковый термин в любом из полей
                    found_in_any_field = False
                    for field_value in fields_to_search:
                        if field_value and search_term_lower in str(field_value).lower():
                            found_in_any_field = True
                            break

                    # Если не нашли поисковый термин, пропускаем задачу
                    if not found_in_any_field:
                        include_issue = False

                # ПРОВЕРКА ФИЛЬТРОВ: Если задача прошла текстовый поиск, проверяем фильтры по имени
                if include_issue and use_python_filtering:
                    # Проверка фильтра по имени статуса
                    if 'status_name' in python_filters and hasattr(issue, 'status') and issue.status:
                        if python_filters['status_name'] != issue.status.name:
                            include_issue = False

                    # Проверка фильтра по имени проекта
                    if include_issue and 'project_name' in python_filters and hasattr(issue, 'project') and issue.project:
                        if python_filters['project_name'] != issue.project.name:
                            include_issue = False

                    # Проверка фильтра по имени приоритета
                    if include_issue and 'priority_name' in python_filters and hasattr(issue, 'priority') and issue.priority:
                        if python_filters['priority_name'] != issue.priority.name:
                            include_issue = False

                # Если задача прошла все проверки, добавляем её в результат
                if include_issue:
                    issues_list_filtered.append(issue)

            current_app.logger.info(f"🔍 ОТЛАДКА: После Python-фильтрации осталось {len(issues_list_filtered)} задач из {len(issues_list_initial)}")
            issues_list_to_return = issues_list_filtered

            # Применяем пагинацию на уже отфильтрованных данных
            start_index = (page - 1) * per_page
            end_index = start_index + per_page
            issues_list_to_return = issues_list_to_return[start_index:end_index]
            total_count_final = len(issues_list_filtered)  # Общее количество после фильтрации
        else:
            issues_list_to_return = issues_list_initial
            total_count_final = issues_page.total_count if hasattr(issues_page, 'total_count') else len(issues_list_to_return)

        current_app.logger.info(f"get_user_assigned_tasks_paginated_optimized: page={page}, per_page={per_page}, found_on_page={len(issues_list_to_return)}, total_overall={total_count_final}")
        return issues_list_to_return, total_count_final

    except Exception as e:
        current_app.logger.error(f"Ошибка в get_user_assigned_tasks_paginated_optimized: {str(e)}")
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        return [], 0
