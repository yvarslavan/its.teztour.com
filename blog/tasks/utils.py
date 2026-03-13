# blog/tasks/utils.py
import traceback
import os
from flask import current_app
from flask import request
from datetime import date, datetime

# Импорты из корневой директории проекта
from redmine import RedmineConnector # Исправленный импорт
from redmine import get_connection, db_redmine_host, db_redmine_user_name, db_redmine_password, db_redmine_name

# ANONYMOUS_USER_ID будет браться из get('redmine', 'api_key') в create_redmine_connector для анонимных случаев,
# или должен быть получен через get('redmine', 'anonymous_user_id') если нужен именно ID.
# Пока что логика create_redmine_connector полагается на общий api_key для "анонимов".


def _tasks_debug_enabled():
    """Включает подробные логи только по явному флагу приложения."""
    try:
        return bool(current_app.config.get('TASKS_DEBUG', False))
    except RuntimeError:
        return False


def _tasks_debug_log(level, message, *args, **kwargs):
    if not _tasks_debug_enabled():
        return

    log_method = getattr(current_app.logger, level, None)
    if callable(log_method):
        log_method(message, *args, **kwargs)


def _should_include_description():
    return request.args.get('with_description') == '1'


def _should_search_in_description():
    return request.args.get('search_in_description') == '1' or _should_include_description()

def create_redmine_connector(is_redmine_user, user_login, password=None, api_key_param=None):
    try:
        # Получаем URL Redmine из переменных окружения
        url = os.getenv('REDMINE_URL')
        if not url:
            current_app.logger.error("REDMINE_URL не установлен в переменных окружения")
            return None

        _tasks_debug_log('info', "Создание коннектора Redmine для URL: %s", url)
        effective_api_key = api_key_param

        if not is_redmine_user and not api_key_param:
            effective_api_key = os.getenv('REDMINE_API_KEY')
            _tasks_debug_log('info', "Используется API ключ из переменных окружения: %s", 'Да' if effective_api_key else 'Нет')

        if effective_api_key:
            masked_key = f"...{effective_api_key[-6:]}" if len(effective_api_key) > 6 else "***"
            _tasks_debug_log('info', "Используется API ключ Redmine: %s", masked_key)
            if "your_redmine_api_key_here" in effective_api_key:
                current_app.logger.error("В переменных окружения используется шаблонный REDMINE_API_KEY, а не реальный ключ")
                return None

        # Логируем параметры создания коннектора
        _tasks_debug_log(
            'info',
            "Параметры коннектора - is_redmine_user: %s, user_login: %s, password: %s",
            is_redmine_user,
            user_login,
            '***' if password else 'None',
        )

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
            _tasks_debug_log('info', "Создан коннектор для пользователя Redmine: %s", user_login)
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
            _tasks_debug_log('info', "Создан коннектор для анонимного пользователя")
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

        # Если у пользователя нет Redmine аккаунта, сразу используем системный API ключ
        if not current_user_obj.is_redmine_user:
            current_app.logger.info(f"Пользователь {username} не имеет Redmine аккаунта, используем системный API ключ")
            system_api_key = os.getenv('REDMINE_API_KEY')
            if system_api_key:
                redmine_conn_system = create_redmine_connector(
                    is_redmine_user=False,
                    user_login=None,
                    password=None,
                    api_key_param=system_api_key
                )

                if redmine_conn_system and hasattr(redmine_conn_system, 'is_user_authenticated'):
                    if redmine_conn_system.is_user_authenticated():
                        current_app.logger.info(f"✅ Системный API ключ успешно использован для пользователя {username}")
                        return redmine_conn_system
                    current_app.logger.warning(
                        f"⚠️ Системный API ключ не прошел проверку аутентификации для пользователя {username}"
                    )
                else:
                    current_app.logger.warning(f"⚠️ Не удалось создать коннектор с системным API ключом для пользователя {username}")
            else:
                current_app.logger.error(f"❌ Системный API ключ не найден для пользователя {username}")
                return None

        # Попытка 1: Аутентификация по паролю из ERP (только для пользователей с Redmine аккаунтом)
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
        system_api_key = os.getenv('REDMINE_API_KEY')
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
                current_app.logger.warning(
                    f"⚠️ Fallback к системному API не прошел для пользователя {username} - аутентификация отклонена"
                )
            else:
                current_app.logger.warning(
                    f"⚠️ Fallback к системному API не прошел для пользователя {username} - коннектор не создан"
                )

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

def task_to_dict(issue, include_description=False):
    """Преобразует объект задачи Redmine в простой словарь, оптимизированный для DataTables."""
    try:
        if not issue:
            # Возвращаем структуру-заглушку, чтобы избежать ошибок на фронтенде
            fallback_task = {
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
            }

            if include_description:
                fallback_task['description'] = 'Задача не была найдена или произошла ошибка при ее загрузке.'

            return fallback_task

        # Формируем "плоский" словарь
        task_data = {
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
        }

        if include_description:
            task_data['description'] = getattr(issue, 'description', '')

        return task_data
    except Exception as e:
        issue_id = getattr(issue, 'id', 'N/A')
        current_app.logger.error(f"Ошибка преобразования задачи #{issue_id} в словарь: {e}", exc_info=True)
        # В случае любой ошибки возвращаем словарь-заглушку с той же структурой
        fallback_task = {
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
        }

        if include_description:
            fallback_task['description'] = f'Произошла ошибка при обработке данных для задачи #{issue_id}.'

        return fallback_task

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

        # Переменная для отслеживания, нужна ли фильтрация на стороне Python
        use_python_filtering = False
        python_filters = {}
        include_description = _should_include_description()
        search_in_description = _should_search_in_description()

        # Проверка наличия параметров фильтрации по имени
        if status_name and status_name not in ['Все статусы', 'All']:
            python_filters['status_name'] = status_name
            use_python_filtering = True

        if project_name and project_name not in ['Все проекты', 'All']:
            python_filters['project_name'] = project_name
            use_python_filtering = True

        if priority_name and priority_name not in ['Все приоритеты', 'All']:
            python_filters['priority_name'] = priority_name
            use_python_filtering = True

        # Увеличиваем лимит для Kanban запросов с force_load=True
        if force_load:
            per_page = min(max(1, per_page), 1000)  # Увеличиваем лимит до 1000 для Kanban
        else:
            per_page = min(max(1, per_page), 100)   # Обычный лимит 100

        # По умолчанию не тянем тяжелое поле description в списках
        includes_base = ['status', 'priority', 'project', 'tracker', 'author', 'easy_email_to']
        if include_description or search_in_description:
            includes_base.append('description')

        filter_params = {
            'assigned_to_id': redmine_user_id,
            'sort': f'{sort_column}:{sort_direction}',
            'limit': per_page,
            'offset': (page - 1) * per_page,
            'include': includes_base
        }

        # Если есть ID фильтров, добавляем их в запрос к Redmine API
        if status_ids and isinstance(status_ids, list) and status_ids[0]:
            filter_params['status_id'] = status_ids[0]

        if project_ids and isinstance(project_ids, list) and project_ids[0]:
            filter_params['project_id'] = project_ids[0]

        if priority_ids and isinstance(priority_ids, list) and priority_ids[0]:
            filter_params['priority_id'] = priority_ids[0]

        # Если это принудительная загрузка данных при первом запросе, добавляем специальный параметр
        if force_load:
            # Добавляем параметр status_id=* для загрузки всех задач
            filter_params['status_id'] = '*'

        # Исключение завершённых задач для оптимизации Kanban
        if exclude_completed:
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
            elif search_encoded.startswith('#') and search_encoded[1:].isdigit():
                # Поиск по ID задачи с символом # - используем Redmine фильтр
                filter_params['issue_id'] = search_encoded[1:]
            else:
                # Поиск по тексту - НЕ используем Redmine фильтры, делаем на стороне Python
                use_python_only_search = True
                _tasks_debug_log(
                    'info',
                    "Python text search enabled for user_id=%s, search='%s', include_description=%s",
                    redmine_user_id,
                    search_encoded,
                    search_in_description,
                )

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

                issues_page = redmine_connector.redmine.issue.filter(**filter_params_for_python)
            else:
                # Обычный поиск по ID или без поиска
                issues_page = redmine_connector.redmine.issue.filter(**filter_params)
        except Exception as api_error:
            current_app.logger.error(f"❌ Ошибка запроса к Redmine API: {str(api_error)}")
            current_app.logger.error(f"Traceback: {traceback.format_exc()}")
            raise api_error

        issues_list_initial = list(issues_page)
        _tasks_debug_log('info', "Fetched %s issues from Redmine API for user_id=%s", len(issues_list_initial), redmine_user_id)

        # ОБЪЕДИНЕННАЯ PYTHON-ФИЛЬТРАЦИЯ: Для текстового поиска и фильтрации по имени
        if use_python_search_or_filter:
            issues_list_filtered = []

            # Подготавливаем параметры поиска
            search_term_lower = search_term.lower() if search_term else None

            for issue in issues_list_initial:
                # По умолчанию задача проходит фильтр
                include_issue = True

                # ПРОВЕРКА ПОИСКА: Если есть поисковый запрос, проверяем его
                if use_python_only_search and search_term_lower:
                    # Поля для текстового поиска
                    fields_to_search = [getattr(issue, 'subject', '')]
                    if search_in_description:
                        fields_to_search.append(getattr(issue, 'description', ''))

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

            _tasks_debug_log(
                'info',
                "Python filtering kept %s of %s issues for user_id=%s",
                len(issues_list_filtered),
                len(issues_list_initial),
                redmine_user_id,
            )
            issues_list_to_return = issues_list_filtered

            # Применяем пагинацию на уже отфильтрованных данных
            start_index = (page - 1) * per_page
            end_index = start_index + per_page
            issues_list_to_return = issues_list_to_return[start_index:end_index]
            total_count_final = len(issues_list_filtered)  # Общее количество после фильтрации
        else:
            issues_list_to_return = issues_list_initial
            total_count_final = issues_page.total_count if hasattr(issues_page, 'total_count') else len(issues_list_to_return)

        _tasks_debug_log(
            'info',
            "Paginated tasks ready: page=%s per_page=%s found_on_page=%s total=%s",
            page,
            per_page,
            len(issues_list_to_return),
            total_count_final,
        )
        return issues_list_to_return, total_count_final

    except Exception as e:
        current_app.logger.error(f"Ошибка в get_user_assigned_tasks_paginated_optimized: {str(e)}")
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        return [], 0
