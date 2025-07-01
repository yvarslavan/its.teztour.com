# 🚀 РУКОВОДСТВО ПО ОПТИМИЗАЦИИ: Страница деталей задачи

## 📋 ПРАКТИЧЕСКАЯ РЕАЛИЗАЦИЯ

### ШАГ 1: Модификация роута `task_detail`

#### 1.1 Добавить функцию сбора всех ID

```python
def collect_ids_from_task_history(task):
    """Собирает все ID из истории изменений задачи для пакетной загрузки"""
    user_ids = set()
    project_ids = set()
    status_ids = set()
    priority_ids = set()

    # Добавляем ID из основной задачи
    if hasattr(task, 'assigned_to') and task.assigned_to:
        user_ids.add(task.assigned_to.id)
    if hasattr(task, 'author') and task.author:
        user_ids.add(task.author.id)
    if hasattr(task, 'status') and task.status:
        status_ids.add(task.status.id)
    if hasattr(task, 'priority') and task.priority:
        priority_ids.add(task.priority.id)
    if hasattr(task, 'project') and task.project:
        project_ids.add(task.project.id)

    # Собираем ID из истории изменений
    for journal in task.journals:
        for detail in journal.details:
            field_name = detail.get('name', '')
            old_value = detail.get('old_value')
            new_value = detail.get('new_value')

            if field_name == 'assigned_to_id':
                if old_value and old_value.isdigit():
                    user_ids.add(int(old_value))
                if new_value and new_value.isdigit():
                    user_ids.add(int(new_value))

            elif field_name == 'project_id':
                if old_value and old_value.isdigit():
                    project_ids.add(int(old_value))
                if new_value and new_value.isdigit():
                    project_ids.add(int(new_value))

            elif field_name == 'status_id':
                if old_value and old_value.isdigit():
                    status_ids.add(int(old_value))
                if new_value and new_value.isdigit():
                    status_ids.add(int(new_value))

            elif field_name == 'priority_id':
                if old_value and old_value.isdigit():
                    priority_ids.add(int(old_value))
                if new_value and new_value.isdigit():
                    priority_ids.add(int(new_value))

    return {
        'user_ids': list(user_ids),
        'project_ids': list(project_ids),
        'status_ids': list(status_ids),
        'priority_ids': list(priority_ids)
    }
```

#### 1.2 Обновить функцию `task_detail`

```python
@tasks_bp.route("/my-tasks/<int:task_id>", methods=["GET"])
@login_required
@weekend_performance_optimizer
def task_detail(task_id):
    """Оптимизированная версия страницы деталей задачи"""
    start_time = time.time()
    current_app.logger.info(f"🚀 [PERFORMANCE] Загрузка задачи {task_id} - начало")

    try:
        # Получаем коннектор Redmine (без изменений)
        redmine_conn_obj = create_redmine_connector(
            is_redmine_user=current_user.is_redmine_user,
            user_login=current_user.username,
            password=current_user.password
        )

        if not redmine_conn_obj or not hasattr(redmine_conn_obj, 'redmine'):
            flash("Не удалось подключиться к Redmine.", "error")
            return redirect(url_for(".my_tasks_page"))

        # Получаем детали задачи (без изменений)
        task = redmine_conn_obj.redmine.issue.get(
            task_id,
            include=['status', 'priority', 'project', 'tracker', 'author', 'assigned_to', 'journals', 'done_ratio', 'attachments', 'relations', 'watchers', 'changesets']
        )

        # ✅ НОВОЕ: Собираем все ID для пакетной загрузки
        ids_data = collect_ids_from_task_history(task)
        current_app.logger.info(f"🔍 [PERFORMANCE] Собрано ID: users={len(ids_data['user_ids'])}, statuses={len(ids_data['status_ids'])}, projects={len(ids_data['project_ids'])}, priorities={len(ids_data['priority_ids'])}")

        # ✅ НОВОЕ: Создаем ОДНО соединение для всех запросов
        connection = get_connection(db_redmine_host, db_redmine_user_name, db_redmine_password, db_redmine_name)

        if not connection:
            current_app.logger.error("❌ [PERFORMANCE] Не удалось создать соединение с MySQL")
            flash("Ошибка соединения с базой данных.", "error")
            return redirect(url_for(".my_tasks_page"))

        # ✅ НОВОЕ: Пакетная загрузка всех данных
        try:
            user_names = get_multiple_user_names(connection, ids_data['user_ids'])
            project_names = get_multiple_project_names(connection, ids_data['project_ids'])
            status_names = get_multiple_status_names(connection, ids_data['status_ids'])
            priority_names = get_multiple_priority_names(connection, ids_data['priority_ids'])

            current_app.logger.info(f"✅ [PERFORMANCE] Загружено данных: users={len(user_names)}, projects={len(project_names)}, statuses={len(status_names)}, priorities={len(priority_names)}")

        finally:
            # ✅ ВАЖНО: Закрываем соединение
            connection.close()
            current_app.logger.info("🔒 [PERFORMANCE] Соединение с MySQL закрыто")

        # Получаем все статусы для создания словаря ID -> название (без изменений)
        status_mapping = {}
        try:
            redmine_statuses = redmine_conn_obj.redmine.issue_status.all()
            for status in redmine_statuses:
                status_mapping[status.id] = status.name
        except Exception as status_error:
            current_app.logger.error(f"❌ Не удалось получить статусы: {status_error}")
            status_mapping = {}

        # Время выполнения
        execution_time = time.time() - start_time
        current_app.logger.info(f"🚀 [PERFORMANCE] Задача {task_id} загружена за {execution_time:.3f}с")

        # ✅ НОВОЕ: Передаем словари данных вместо функций
        return render_template("task_detail.html",
                             task=task,
                             title=f"Задача #{task.id}",
                             count_notifications=0,
                             status_mapping=status_mapping,
                             # ✅ Новые данные для оптимизированного шаблона
                             user_names=user_names,
                             project_names=project_names,
                             status_names=status_names,
                             priority_names=priority_names,
                             # ✅ Убираем функции создающие соединения
                             # get_property_name=get_property_name,          # ❌ УДАЛЕНО
                             # get_status_name_from_id=get_status_name_from_id, # ❌ УДАЛЕНО
                             # get_project_name_from_id=get_project_name_from_id, # ❌ УДАЛЕНО
                             # get_user_full_name_from_id=get_user_full_name_from_id, # ❌ УДАЛЕНО
                             # get_priority_name_from_id=get_priority_name_from_id, # ❌ УДАЛЕНО
                             # get_connection=get_connection,               # ❌ УДАЛЕНО
                             # db_redmine_* параметры больше не нужны     # ❌ УДАЛЕНО
                             # Оставляем только helper для форматирования
                             convert_datetime_msk_format=convert_datetime_msk_format,
                             format_boolean_field=format_boolean_field)

    except ResourceNotFoundError:
        current_app.logger.warning(f"Задача с ID {task_id} не найдена в Redmine")
        flash(f"Задача #{task_id} не найдена.", "error")
        return redirect(url_for(".my_tasks_page"))
    except Exception as e:
        current_app.logger.error(f"Ошибка при получении задачи {task_id}: {str(e)}")
        flash("Произошла ошибка при загрузке данных задачи.", "error")
        return redirect(url_for(".my_tasks_page"))
```

### ШАГ 2: Обновление шаблона `task_detail.html`

#### 2.1 Замена функций на словари (строки 406-439)

**БЫЛО (медленно):**
```jinja2
{% if detail.name == 'status_id' %}
  {{ get_status_name_from_id(get_connection(db_redmine_host, db_redmine_user_name, db_redmine_password, db_redmine_name), detail.old_value) or detail.old_value }}
{% elif detail.name == 'assigned_to_id' %}
  {{ get_user_full_name_from_id(get_connection(db_redmine_host, db_redmine_user_name, db_redmine_password, db_redmine_name), detail.old_value) or detail.old_value }}
{% elif detail.name == 'project_id' %}
  {{ get_project_name_from_id(get_connection(db_redmine_host, db_redmine_user_name, db_redmine_password, db_redmine_name), detail.old_value) or detail.old_value }}
{% elif detail.name == 'priority_id' %}
  {{ get_priority_name_from_id(get_connection(db_redmine_host, db_redmine_user_name, db_redmine_password, db_redmine_name), detail.old_value) or detail.old_value }}
{% endif %}
```

**СТАЛО (быстро):**
```jinja2
{% if detail.name == 'status_id' %}
  {{ status_names.get(detail.old_value|int, detail.old_value) if detail.old_value and detail.old_value.isdigit() else detail.old_value }}
{% elif detail.name == 'assigned_to_id' %}
  {{ user_names.get(detail.old_value|int, detail.old_value) if detail.old_value and detail.old_value.isdigit() else detail.old_value }}
{% elif detail.name == 'project_id' %}
  {{ project_names.get(detail.old_value|int, detail.old_value) if detail.old_value and detail.old_value.isdigit() else detail.old_value }}
{% elif detail.name == 'priority_id' %}
  {{ priority_names.get(detail.old_value|int, detail.old_value) if detail.old_value and detail.old_value.isdigit() else detail.old_value }}
{% endif %}
```

#### 2.2 Аналогично для new_value

**БЫЛО (медленно):**
```jinja2
{% if detail.name == 'status_id' %}
  {{ get_status_name_safe(detail.new_value) }}
{% elif detail.name == 'assigned_to_id' %}
  {{ get_user_name_safe(detail.new_value) if detail.new_value else 'Не назначен' }}
{% elif detail.name == 'project_id' %}
  {{ get_project_name_safe(detail.new_value) }}
{% elif detail.name == 'priority_id' %}
  {{ get_priority_name_safe(detail.new_value) }}
{% endif %}
```

**СТАЛО (быстро):**
```jinja2
{% if detail.name == 'status_id' %}
  {{ status_names.get(detail.new_value|int, detail.new_value) if detail.new_value and detail.new_value.isdigit() else detail.new_value }}
{% elif detail.name == 'assigned_to_id' %}
  {% if detail.new_value and detail.new_value.isdigit() %}
    {{ user_names.get(detail.new_value|int, detail.new_value) }}
  {% else %}
    Не назначен
  {% endif %}
{% elif detail.name == 'project_id' %}
  {{ project_names.get(detail.new_value|int, detail.new_value) if detail.new_value and detail.new_value.isdigit() else detail.new_value }}
{% elif detail.name == 'priority_id' %}
  {{ priority_names.get(detail.new_value|int, detail.new_value) if detail.new_value and detail.new_value.isdigit() else detail.new_value }}
{% endif %}
```

### ШАГ 3: Добавление недостающих пакетных функций

Если функции `get_multiple_*` еще не реализованы, добавить в `redmine.py`:

```python
@monitor_performance("get_multiple_project_names")
def get_multiple_project_names(connection, project_ids):
    """Пакетная загрузка названий проектов по списку ID"""
    if not project_ids or not connection:
        return {}

    clean_ids = list(set(filter(None, project_ids)))
    if not clean_ids:
        return {}

    placeholders = ','.join(['%s'] * len(clean_ids))
    sql = f"SELECT id, name FROM projects WHERE id IN ({placeholders})"

    cursor = None
    result = {}
    try:
        cursor = connection.cursor()
        cursor.execute(sql, clean_ids)
        for row in cursor:
            result[row["id"]] = row["name"]
        return result
    except pymysql.Error as e:
        logger.error(f"Ошибка при пакетной загрузке названий проектов: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()

@monitor_performance("get_multiple_status_names")
def get_multiple_status_names(connection, status_ids):
    """Пакетная загрузка названий статусов по списку ID"""
    if not status_ids or not connection:
        return {}

    clean_ids = list(set(filter(None, status_ids)))
    if not clean_ids:
        return {}

    placeholders = ','.join(['%s'] * len(clean_ids))
    sql = f"""
        SELECT s.id, COALESCE(us.name, s.name) as name
        FROM issue_statuses s
        LEFT JOIN u_statuses us ON s.id = us.id
        WHERE s.id IN ({placeholders})
    """

    cursor = None
    result = {}
    try:
        cursor = connection.cursor()
        cursor.execute(sql, clean_ids)
        for row in cursor:
            result[row["id"]] = row["name"]
        return result
    except pymysql.Error as e:
        logger.error(f"Ошибка при пакетной загрузке названий статусов: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()

@monitor_performance("get_multiple_priority_names")
def get_multiple_priority_names(connection, priority_ids):
    """Пакетная загрузка названий приоритетов по списку ID"""
    if not priority_ids or not connection:
        return {}

    clean_ids = list(set(filter(None, priority_ids)))
    if not clean_ids:
        return {}

    placeholders = ','.join(['%s'] * len(clean_ids))
    sql = f"""
        SELECT e.id, COALESCE(up.name, e.name) as name
        FROM enumerations e
        LEFT JOIN u_Priority up ON e.id = up.id
        WHERE e.id IN ({placeholders}) AND e.type = 'IssuePriority'
    """

    cursor = None
    result = {}
    try:
        cursor = connection.cursor()
        cursor.execute(sql, clean_ids)
        for row in cursor:
            result[row["id"]] = row["name"]
        return result
    except pymysql.Error as e:
        logger.error(f"Ошибка при пакетной загрузке названий приоритетов: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()
```

### ШАГ 4: Добавление helper для boolean полей

```python
def format_boolean_field(value, field_name):
    """Форматирование булевых полей для шаблона"""
    if field_name == 'easy_helpdesk_need_reaction':
        return 'Да' if value == '1' else 'Нет'
    elif field_name == '16':
        return 'Да' if value and value != '0' else 'Нет'
    else:
        return 'Да' if value else 'Нет'
```

## 📊 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

### ДО ОПТИМИЗАЦИИ:
- **Время загрузки**: 3-10 секунд
- **Соединения с БД**: 50-100+
- **SQL запросы**: 50-100+ одиночных SELECT

### ПОСЛЕ ОПТИМИЗАЦИИ:
- **Время загрузки**: 0.5-1.5 секунды ⚡
- **Соединения с БД**: 1 📉
- **SQL запросы**: 4 пакетных SELECT 📦

### УЛУЧШЕНИЯ:
- **Производительность**: ⬆️ до 10x быстрее
- **Нагрузка на БД**: ⬇️ на 90%+
- **Стабильность**: ⬆️ меньше тайм-аутов
- **Масштабируемость**: ⬆️ готовность к росту нагрузки

## 🧪 ТЕСТИРОВАНИЕ

### 1. Функциональное тестирование
- Проверить отображение всех полей в истории изменений
- Убедиться в корректности преобразования ID в названия
- Протестировать edge cases (пустые значения, несуществующие ID)

### 2. Нагрузочное тестирование
- Измерить время загрузки до и после оптимизации
- Проверить работу под одновременной нагрузкой
- Убедиться в отсутствии утечек соединений

### 3. Мониторинг
- Настроить логирование времени выполнения
- Отслеживать количество соединений с БД
- Мониторить использование памяти

---

**Статус**: Готово к реализации
**Приоритет**: КРИТИЧЕСКИЙ
**Время на реализацию**: 2-4 часа
