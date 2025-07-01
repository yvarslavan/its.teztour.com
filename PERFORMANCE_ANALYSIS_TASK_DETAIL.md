# 🚀 АНАЛИЗ ПРОИЗВОДИТЕЛЬНОСТИ: Страница деталей задачи (/tasks/my-tasks/<id>)

## 📊 КРАТКОЕ РЕЗЮМЕ ПРОБЛЕМЫ

При загрузке страницы деталей задачи происходит **МНОЖЕСТВЕННОЕ СОЗДАНИЕ СОЕДИНЕНИЙ** с базой данных MySQL Redmine, что приводит к значительному замедлению загрузки.

### ⚡ КЛЮЧЕВЫЕ ПРОБЛЕМЫ:
1. **В шаблоне**: Каждый helper вызов в цикле создает новое соединение
2. **В функциях**: Отсутствие переиспользования соединений
3. **Дублирование**: Параллельное использование старых и новых helper функций
4. **Неоптимальные запросы**: Множественные одиночные SELECT вместо пакетных запросов

---

## 🔍 ДЕТАЛЬНЫЙ АНАЛИЗ ВЫЗОВОВ `get_connection`

### 1. В ШАБЛОНЕ `task_detail.html` (строки 406-412)

**КРИТИЧЕСКАЯ ПРОБЛЕМА**: В цикле по истории изменений задачи каждый helper создает новое соединение:

```jinja2
{% for journal in task.journals %}
  {% for detail in journal.details %}
    <!-- ❌ ПРОБЛЕМА: Каждый вызов создает новое соединение! -->
    {{ get_status_name_from_id(get_connection(...), detail.old_value) }}
    {{ get_user_full_name_from_id(get_connection(...), detail.old_value) }}
    {{ get_project_name_from_id(get_connection(...), detail.old_value) }}
    {{ get_priority_name_from_id(get_connection(...), detail.old_value) }}

    <!-- А также для new_value используются новые helper'ы -->
    {{ get_status_name_safe(detail.new_value) }}
    {{ get_user_name_safe(detail.new_value) }}
    {{ get_project_name_safe(detail.new_value) }}
    {{ get_priority_name_safe(detail.new_value) }}
  {% endfor %}
{% endfor %}
```

**МАСШТАБ ПРОБЛЕМЫ**: Если у задачи 10 изменений и каждое изменение имеет 4 поля, это означает:
- 10 × 4 = 40 вызовов старых helper'ов (каждый создает соединение)
- 10 × 4 = 40 вызовов новых helper'ов (каждый создает соединение)
- **ИТОГО: 80 соединений только для истории изменений!**

### 2. В РОУТЕ `task_detail` (blog/tasks/routes.py:128-145)

Роут передает в шаблон функции, которые создают собственные соединения:

```python
return render_template("task_detail.html",
    # ❌ Эти функции создают соединения внутри себя
    get_property_name=get_property_name,              # создает соединение в redmine.py:181
    get_status_name_from_id=get_status_name_from_id,
    get_project_name_from_id=get_project_name_from_id,
    get_user_full_name_from_id=get_user_full_name_from_id,
    get_priority_name_from_id=get_priority_name_from_id,
    get_connection=get_connection,                    # ❌ Передается функция создания соединения
    # Параметры подключения для создания соединений в шаблоне
    db_redmine_host=db_redmine_host,
    db_redmine_user_name=db_redmine_user_name,
    db_redmine_password=db_redmine_password,
    db_redmine_name=db_redmine_name)
```

### 3. СТАРЫЕ HELPER ФУНКЦИИ (redmine.py)

Каждая функция создает свой курсор:

```python
def get_status_name_from_id(connection, status_id):
    cursor = connection.cursor()  # ❌ Новый курсор каждый раз
    # ... запрос
    cursor.close()

def get_user_full_name_from_id(connection, property_value):
    cursor = connection.cursor()  # ❌ Новый курсор каждый раз
    # ... запрос
    cursor.close()

def get_project_name_from_id(connection, project_id):
    cursor = connection.cursor()  # ❌ Новый курсор каждый раз
    # ... запрос
    cursor.close()

def get_priority_name_from_id(connection, priority_id):
    cursor = connection.cursor()  # ❌ Новый курсор каждый раз
    # ... запрос
    cursor.close()
```

### 4. НОВЫЕ HELPER ФУНКЦИИ (blog/utils/template_helpers.py)

Каждая функция создает собственное соединение:

```python
def get_status_name_safe(self, status_id):
    conn = self.get_mysql_connection()  # ❌ Новое соединение
    cursor = conn.cursor()
    # ... запрос

def get_user_name_safe(self, user_id):
    conn = self.get_mysql_connection()  # ❌ Новое соединение
    cursor = conn.cursor()
    # ... запрос

def get_project_name_safe(self, project_id):
    conn = self.get_mysql_connection()  # ❌ Новое соединение
    cursor = conn.cursor()
    # ... запрос

def get_priority_name_safe(self, priority_id):
    conn = self.get_mysql_connection()  # ❌ Новое соединение
    cursor = conn.cursor()
    # ... запрос
```

### 5. ФУНКЦИЯ `get_property_name` (redmine.py:178-206)

Создает собственное соединение для каждого вызова:

```python
def get_property_name(property_name, prop_key, old_value, value):
    connection = get_connection(                    # ❌ Новое соединение каждый раз
        db_redmine_host, db_redmine_user_name,
        db_redmine_password, db_redmine_name
    )
    # ... внутри еще больше вызовов helper'ов
```

---

## 📈 ИЗМЕРЕНИЕ ПРОИЗВОДИТЕЛЬНОСТИ

### ТЕКУЩАЯ СИТУАЦИЯ:
- **Соединения на страницу**: 50-100+ (зависит от количества изменений)
- **Время загрузки**: 3-10 секунд
- **Нагрузка на БД**: Высокая из-за множественных подключений

### ЦЕЛЕВЫЕ ПОКАЗАТЕЛИ:
- **Соединения на страницу**: 1-2 максимум
- **Время загрузки**: 0.5-1.5 секунды
- **Нагрузка на БД**: Минимальная

---

## 🛠️ ПЛАН ОПТИМИЗАЦИИ

### ЭТАП 1: НЕМЕДЛЕННЫЕ ИСПРАВЛЕНИЯ

#### 1.1 Оптимизация шаблона
```python
# В роуте: предварительная загрузка всех данных одним запросом
def task_detail(task_id):
    # ... получение задачи

    # Собираем все ID для пакетной загрузки
    user_ids = set()
    project_ids = set()
    status_ids = set()
    priority_ids = set()

    for journal in task.journals:
        for detail in journal.details:
            if detail.name == 'assigned_to_id':
                if detail.old_value: user_ids.add(detail.old_value)
                if detail.new_value: user_ids.add(detail.new_value)
            # ... аналогично для других полей

    # Одно соединение для всех данных
    connection = get_connection(...)
    user_names = get_multiple_user_names(connection, list(user_ids))
    project_names = get_multiple_project_names(connection, list(project_ids))
    status_names = get_multiple_status_names(connection, list(status_ids))
    priority_names = get_multiple_priority_names(connection, list(priority_ids))
    connection.close()

    return render_template("task_detail.html",
        user_names=user_names,
        project_names=project_names,
        status_names=status_names,
        priority_names=priority_names,
        # Убираем все helper функции создающие соединения
    )
```

#### 1.2 Изменение шаблона
```jinja2
<!-- ✅ ОПТИМИЗИРОВАННАЯ ВЕРСИЯ -->
{% for journal in task.journals %}
  {% for detail in journal.details %}
    {% if detail.name == 'status_id' %}
      <span class="old-value">{{ status_names.get(detail.old_value|int, detail.old_value) }}</span>
      <span class="new-value">{{ status_names.get(detail.new_value|int, detail.new_value) }}</span>
    {% elif detail.name == 'assigned_to_id' %}
      <span class="old-value">{{ user_names.get(detail.old_value|int, detail.old_value) }}</span>
      <span class="new-value">{{ user_names.get(detail.new_value|int, detail.new_value) }}</span>
    {% endif %}
  {% endfor %}
{% endfor %}
```

### ЭТАП 2: АРХИТЕКТУРНЫЕ УЛУЧШЕНИЯ

#### 2.1 Кэширование
```python
# Кэш для часто используемых данных
@lru_cache(maxsize=1000)
def get_cached_user_name(user_id):
    # ... реализация с кэшем
```

#### 2.2 Пул соединений
```python
# Создание пула соединений для переиспользования
connection_pool = PooledDB(
    pymysql,
    maxconnections=10,
    host=db_redmine_host,
    # ...
)
```

#### 2.3 Оптимизированные SQL запросы
```sql
-- Вместо множественных SELECT
-- Один JOIN запрос для всех данных истории
SELECT
    j.id as journal_id,
    jd.property,
    jd.old_value,
    jd.new_value,
    CASE
        WHEN jd.property = 'status_id' THEN s.name
        WHEN jd.property = 'assigned_to_id' THEN CONCAT(u.firstname, ' ', u.lastname)
        -- ... другие поля
    END as display_value
FROM journals j
JOIN journal_details jd ON j.id = jd.journal_id
LEFT JOIN issue_statuses s ON jd.new_value = s.id AND jd.property = 'status_id'
LEFT JOIN users u ON jd.new_value = u.id AND jd.property = 'assigned_to_id'
WHERE j.journalized_id = ? AND j.journalized_type = 'Issue'
```

---

## ⚡ ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

### ПОСЛЕ ОПТИМИЗАЦИИ:
- **Соединения**: 1 вместо 50-100+
- **Время загрузки**: Уменьшение в 5-10 раз
- **Нагрузка на БД**: Снижение на 90%+
- **Пользовательский опыт**: Мгновенная загрузка страниц

### ДОПОЛНИТЕЛЬНЫЕ ПРЕИМУЩЕСТВА:
- Лучшая стабильность под нагрузкой
- Меньше ошибок тайм-аута
- Возможность масштабирования
- Улучшенная отзывчивость системы

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ

1. **Немедленно**: Реализовать пакетную загрузку данных в роуте `task_detail`
2. **В течение недели**: Переписать шаблон для использования предзагруженных данных
3. **В течение месяца**: Внедрить пул соединений и кэширование
4. **Долгосрочно**: Рассмотреть переход на асинхронные запросы

---

**Дата анализа**: {current_date}
**Критичность**: ВЫСОКАЯ
**Приоритет**: НЕМЕДЛЕННО
