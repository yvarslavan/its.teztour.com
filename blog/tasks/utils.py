# blog/tasks/utils.py
import traceback
from flask import current_app
from flask import request
from datetime import date, datetime

# Импорты из корневой директории проекта
from config import get
from redmine import RedmineConnector # Исправленный импорт
from redmine import get_connection, db_redmine_host, db_redmine_user_name, db_redmine_password, db_redmine_name

# ANONYMOUS_USER_ID будет браться из get('redmine', 'api_key') в create_redmine_connector для анонимных случаев,
# или должен быть получен через get('redmine', 'anonymous_user_id') если нужен именно ID.
# Пока что логика create_redmine_connector полагается на общий api_key для "анонимов".

def create_redmine_connector(is_redmine_user, user_login, password=None, api_key_param=None):
    try:
        # Получаем URL Redmine из конфигурации
        url = get('redmine', 'url')
        if not url:
            current_app.logger.error("URL Redmine не найден в конфигурации")
            return None

        current_app.logger.info(f"Создание коннектора Redmine для URL: {url}")
        effective_api_key = api_key_param

        if not is_redmine_user and not api_key_param:
            effective_api_key = get('redmine', 'api_key', None)
            current_app.logger.info(f"Используется API ключ из конфигурации: {'Да' if effective_api_key else 'Нет'}")

        # Логируем параметры создания коннектора
        current_app.logger.info(f"Параметры коннектора - is_redmine_user: {is_redmine_user}, user_login: {user_login}, password: {'***' if password else 'None'}")

        if is_redmine_user:
            if not user_login or not password:
                current_app.logger.error(f"Недостаточно данных для пользователя Redmine - login: {user_login}, password: {'***' if password else 'None'}")
                return None

            connector = RedmineConnector(
                url=url,
                username=user_login,
                password=password,
                api_key=effective_api_key
            )
            current_app.logger.info(f"Создан коннектор для пользователя Redmine: {user_login}")
            return connector
        else:
            if not effective_api_key:
                current_app.logger.error("API ключ не найден для анонимного пользователя")
                return None

            connector = RedmineConnector(
                url=url,
                username=None,
                password=None,
                api_key=effective_api_key
            )
            current_app.logger.info("Создан коннектор для анонимного пользователя")
            return connector

    except Exception as e:
        current_app.logger.error(f"Ошибка при создании коннектора Redmine: {e}")
        import traceback
        current_app.logger.error(f"Трассировка: {traceback.format_exc()}")
        return None

def get_redmine_connector(current_user_obj, user_password_erp):
    """Получение экземпляра RedmineConnector с fallback механизмом"""
    password_to_use = user_password_erp if user_password_erp else None
    username = current_user_obj.username

    try:
        # Определяем логин для Redmine (если есть маппинг, используем его)
        redmine_login = getattr(current_user_obj, 'redmine_username', None) or username
        current_app.logger.info(f"Попытка аутентификации для пользователя {username}, логин в Redmine: {redmine_login}")

        # Попытка 1: Аутентификация по паролю из ERP
        current_app.logger.info(f"Попытка аутентификации по паролю для пользователя {username}")
        redmine_conn = create_redmine_connector(
            is_redmine_user=current_user_obj.is_redmine_user,
            user_login=redmine_login,  # Используем правильный логин
            password=password_to_use,
            api_key_param=None
        )

        if redmine_conn and hasattr(redmine_conn, 'is_user_authenticated'):
            if redmine_conn.is_user_authenticated():
                current_app.logger.info(f"✅ Аутентификация по паролю успешна для пользователя {username}")
                return redmine_conn
            else:
                current_app.logger.warning(f"⚠️ Аутентификация по паролю не прошла для пользователя {username}")

        # Попытка 2: Проверяем, есть ли у пользователя API ключ в профиле
        if hasattr(current_user_obj, 'redmine_api_key') and current_user_obj.redmine_api_key:
            current_app.logger.info(f"Попытка аутентификации по API ключу для пользователя {username}")
            redmine_conn_api = create_redmine_connector(
                is_redmine_user=False,  # Используем API ключ, не логин/пароль
                user_login=None,
                password=None,
                api_key_param=current_user_obj.redmine_api_key
            )

            if redmine_conn_api and hasattr(redmine_conn_api, 'is_user_authenticated'):
                if redmine_conn_api.is_user_authenticated():
                    current_app.logger.info(f"✅ Аутентификация по API ключу успешна для пользователя {username}")
                    return redmine_conn_api
                else:
                    current_app.logger.warning(f"⚠️ Аутентификация по API ключу не прошла для пользователя {username}")

        # Попытка 3: Fallback к общему API ключу системы (только для чтения)
        system_api_key = get('redmine', 'api_key', None)
        if system_api_key:
            current_app.logger.info(f"Попытка fallback к системному API ключу для пользователя {username}")
            redmine_conn_system = create_redmine_connector(
                is_redmine_user=False,
                user_login=None,
                password=None,
                api_key_param=system_api_key
            )

            if redmine_conn_system and hasattr(redmine_conn_system, 'is_user_authenticated'):
                if redmine_conn_system.is_user_authenticated():
                    current_app.logger.info(f"✅ Fallback к системному API успешен для пользователя {username} (режим только чтения)")
                    return redmine_conn_system
                else:
                    current_app.logger.warning(f"⚠️ Fallback к системному API не прошел для пользователя {username}")

        current_app.logger.error(f"❌ Все попытки аутентификации не удались для пользователя {username}")
        return None

    except Exception as e:
        current_app.logger.error(f"Ошибка при создании Redmine коннектора для пользователя {username}: {e}")
        import traceback
        current_app.logger.error(f"Трассировка: {traceback.format_exc()}")
        return None

def get_user_redmine_password(username):
    """Получает оригинальный пароль пользователя из Oracle для подключения к Redmine"""
    try:
        from erp_oracle import connect_oracle, get_user_erp_password, db_host, db_port, db_service_name, db_user_name, db_password

        oracle_conn = connect_oracle(db_host, db_port, db_service_name, db_user_name, db_password)
        if not oracle_conn:
            current_app.logger.error("Не удалось подключиться к Oracle для получения пароля")
            return None

        user_password_erp = get_user_erp_password(oracle_conn, username)
        if not user_password_erp:
            current_app.logger.error(f"Не удалось получить пароль для пользователя {username} из ERP")
            return None

        actual_password = user_password_erp[0] if isinstance(user_password_erp, tuple) else user_password_erp
        return actual_password

    except Exception as e:
        current_app.logger.error(f"Ошибка при получении пароля пользователя {username}: {str(e)}")
        return None

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
    """Преобразует объект задачи Redmine в простой словарь, оптимизированный для DataTables."""
    try:
        if not issue:
            # Возвращаем структуру-заглушку, чтобы избежать ошибок на фронтенде
            return {
                'id': 0,
                'subject': 'Ошибка: Задача не найдена',
                'project_name': 'N/A',
                'status_name': 'N/A',
                'priority_name': 'N/A',
                'author_name': 'N/A',
                'assigned_to_name': 'N/A',
                'easy_email_to': '-',
                'created_on': '',
                'updated_on': '',
                'start_date': '',
                'due_date': '',
                'closed_on': '',
                'done_ratio': 0,
                'description': 'Задача не была найдена или произошла ошибка при ее загрузке.',
            }

        # Формируем "плоский" словарь
        return {
            'id': issue.id,
            'subject': getattr(issue, 'subject', ''),

            # Прямые поля для статуса, приоритета и проекта
            'status_name': getattr(issue.status, 'name', 'Неизвестен') if hasattr(issue, 'status') else 'Неизвестен',
            'status_id': getattr(issue.status, 'id', 1) if hasattr(issue, 'status') else 1,
            'priority_name': getattr(issue.priority, 'name', 'Обычный') if hasattr(issue, 'priority') else 'Обычный',
            'project_name': getattr(issue.project, 'name', 'Без проекта') if hasattr(issue, 'project') else 'Без проекта',

            # Остальные поля
            'tracker_name': getattr(issue.tracker, 'name', 'Без трекера') if hasattr(issue, 'tracker') else 'Без трекера',
            'author_name': getattr(issue.author, 'name', 'Аноним') if hasattr(issue, 'author') else 'Аноним',
            'assigned_to_name': getattr(issue.assigned_to, 'name', 'Не назначен') if hasattr(issue, 'assigned_to') else 'Не назначен',

            'easy_email_to': getattr(issue, 'easy_email_to', '-'),
            'created_on': format_issue_date(getattr(issue, 'created_on', None)),
            'updated_on': format_issue_date(getattr(issue, 'updated_on', None)),
            'start_date': format_issue_date(getattr(issue, 'start_date', None)),
            'due_date': format_issue_date(getattr(issue, 'due_date', None)),
            'closed_on': format_issue_date(getattr(issue, 'closed_on', None)),
            'done_ratio': getattr(issue, 'done_ratio', 0),
            'description': getattr(issue, 'description', ''),
        }
    except Exception as e:
        issue_id = getattr(issue, 'id', 'N/A')
        current_app.logger.error(f"Ошибка преобразования задачи #{issue_id} в словарь: {e}", exc_info=True)
        # В случае любой ошибки возвращаем словарь-заглушку с той же структурой
        return {
            'id': issue_id,
            'subject': f'Ошибка обработки данных для задачи #{issue_id}',
            'project_name': 'Ошибка',
            'status_name': 'Ошибка',
            'priority_name': 'Ошибка',
            'author_name': 'Ошибка',
            'assigned_to_name': 'Ошибка',
            'easy_email_to': '-',
            'created_on': '',
            'updated_on': '',
            'start_date': '',
            'due_date': '',
            'closed_on': '',
            'done_ratio': 0,
            'description': f'Произошла ошибка при обработке данных для задачи #{issue_id}.',
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
        advanced_search_enabled=False, force_load=False, exclude_completed=False
    ):
    try:
        # Извлекаем параметры фильтрации по имени напрямую из request
        status_name = request.args.get('status_name', '')
        project_name = request.args.get('project_name', '')
        priority_name = request.args.get('priority_name', '')

        # Извлекаем параметры фильтрации по ID напрямую из request
        status_id = request.args.get('status_id', '')
        project_id = request.args.get('project_id', '')
        priority_id = request.args.get('priority_id', '')

        # Приоритет имеют параметры, полученные напрямую из запроса
        if status_id:
            status_ids = [status_id]
        if project_id:
            project_ids = [project_id]
        if priority_id:
            priority_ids = [priority_id]

        current_app.logger.info(f"🔍 [FILTER_DEBUG] Получены параметры фильтрации: status_id={status_id}, project_id={project_id}, priority_id={priority_id}")
        current_app.logger.info(f"🔍 [FILTER_DEBUG] Получены параметры фильтрации по имени: status_name='{status_name}', project_name='{project_name}', priority_name='{priority_name}'")

        # Переменная для отслеживания, нужна ли фильтрация на стороне Python
        use_python_filtering = False
        python_filters = {}

        # Проверка наличия параметров фильтрации по имени
        if status_name and status_name not in ['Все статусы', 'All']:
            current_app.logger.info(f"🔍 [FILTER_DEBUG] Обнаружен фильтр по имени статуса: '{status_name}'")
            python_filters['status_name'] = status_name
            use_python_filtering = True

        if project_name and project_name not in ['Все проекты', 'All']:
            current_app.logger.info(f"🔍 [FILTER_DEBUG] Обнаружен фильтр по имени проекта: '{project_name}'")
            python_filters['project_name'] = project_name
            use_python_filtering = True

        if priority_name and priority_name not in ['Все приоритеты', 'All']:
            current_app.logger.info(f"🔍 [FILTER_DEBUG] Обнаружен фильтр по имени приоритета: '{priority_name}'")
            python_filters['priority_name'] = priority_name
            use_python_filtering = True

        current_app.logger.info(f"Получение задач: user_id={redmine_user_id}, page={page}, per_page={per_page}, search='{search_term}', sort='{sort_column}:{sort_direction}', statuses={status_ids}, projects={project_ids}, priorities={priority_ids}")

        # Увеличиваем лимит для Kanban запросов с force_load=True
        if force_load:
            per_page = min(max(1, per_page), 1000)  # Увеличиваем лимит до 1000 для Kanban
        else:
            per_page = min(max(1, per_page), 100)   # Обычный лимит 100

        filter_params = {
            'assigned_to_id': redmine_user_id,
            'sort': f'{sort_column}:{sort_direction}',
            'limit': per_page,
            'offset': (page - 1) * per_page,
            'include': ['status', 'priority', 'project', 'tracker', 'author', 'description', 'easy_email_to']
        }

        # Если есть ID фильтров, добавляем их в запрос к Redmine API
        if status_ids and isinstance(status_ids, list) and status_ids[0]:
            filter_params['status_id'] = status_ids[0]
            current_app.logger.info(f"🔍 [FILTER_DEBUG] Добавлен фильтр по ID статуса: {status_ids[0]}")

        if project_ids and isinstance(project_ids, list) and project_ids[0]:
            filter_params['project_id'] = project_ids[0]
            current_app.logger.info(f"🔍 [FILTER_DEBUG] Добавлен фильтр по ID проекта: {project_ids[0]}")

        if priority_ids and isinstance(priority_ids, list) and priority_ids[0]:
            filter_params['priority_id'] = priority_ids[0]
            current_app.logger.info(f"🔍 [FILTER_DEBUG] Добавлен фильтр по ID приоритета: {priority_ids[0]}")

        # Если это принудительная загрузка данных при первом запросе, добавляем специальный параметр
        if force_load:
            current_app.logger.info(f"🔍 [FILTER_DEBUG] Принудительная загрузка данных (force_load=True)")
            # Добавляем параметр status_id=* для загрузки всех задач
            filter_params['status_id'] = '*'

        # Исключение завершённых задач для оптимизации Kanban
        if exclude_completed:
            current_app.logger.info(f"🔍 [FILTER_DEBUG] Исключение завершённых задач (exclude_completed=True)")
            # Исключаем завершённые статусы (5=Закрыта, 6=Отклонена, 14=Перенаправлена)
            completed_status_ids = ['5', '6', '14']
            if 'status_id' in filter_params:
                # Если уже есть фильтр по статусу, добавляем исключение завершённых
                current_status = filter_params['status_id']
                if current_status == '*':
                    # Исключаем завершённые из всех статусов
                    filter_params['status_id'] = '!' + '|'.join(completed_status_ids)
                else:
                    # Добавляем исключение к существующему фильтру
                    filter_params['status_id'] = current_status + '|!' + '|'.join(completed_status_ids)
            else:
                # Добавляем фильтр исключения завершённых
                filter_params['status_id'] = '!' + '|'.join(completed_status_ids)

        # Фильтрация по тексту поиска
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

        # Объединение логики текстового поиска и фильтрации по имени
        use_python_search_or_filter = use_python_only_search or use_python_filtering

        # Выполняем запрос к Redmine REST API
        try:
            if use_python_search_or_filter:
                # Для текстового поиска или фильтрации по имени: загружаем БОЛЬШЕ задач
                filter_params_for_python = filter_params.copy()
                if force_load:
                    filter_params_for_python['limit'] = 1000  # Увеличиваем лимит для Kanban
                else:
                    filter_params_for_python['limit'] = 200   # Обычный лимит для поиска/фильтрации
                filter_params_for_python['offset'] = 0   # Сбрасываем offset для поиска/фильтрации

                current_app.logger.info(f"🔍 ОТЛАДКА: Загружаем {filter_params_for_python['limit']} задач для обработки на Python")
                issues_page = redmine_connector.redmine.issue.filter(**filter_params_for_python)
            else:
                # Обычный поиск по ID или без поиска
                current_app.logger.info(f"🔍 ОТЛАДКА: Выполняем стандартный запрос к Redmine")
                issues_page = redmine_connector.redmine.issue.filter(**filter_params)
        except Exception as api_error:
            current_app.logger.error(f"❌ Ошибка запроса к Redmine API: {str(api_error)}")
            current_app.logger.error(f"Traceback: {traceback.format_exc()}")
            raise api_error

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
