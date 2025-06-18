# Документация страницы "Мои задачи в Redmine" (/tasks/my-tasks)

## 1. Назначение страницы

Страница `/tasks/my-tasks` представляет собой централизованный интерфейс для управления и мониторинга задач пользователя в системе Redmine. Основные функции:

- **Отображение списка задач**: Показывает все задачи, назначенные текущему пользователю
- **Интерактивная фильтрация**: Позволяет фильтровать задачи по статусу, проекту, приоритету
- **Поиск и сортировка**: Полнотекстовый поиск и сортировка по различным полям
- **Статистическая аналитика**: Визуализация разбивки задач по статусам с детализацией
- **Интеграция с Redmine**: Прямые ссылки на систему Redmine для детального просмотра и редактирования
- **Пагинация**: Эффективная загрузка больших объемов данных

## 2. Пользовательские сценарии

### 2.1 Типы пользователей

**Redmine-пользователи** (`is_redmine_user = True`):
- Имеют доступ к полному функционалу страницы
- Аутентифицируются в Redmine через свои учетные данные
- Видят только свои назначенные задачи

**Обычные пользователи** (`is_redmine_user = False`):
- Не имеют доступа к странице
- Перенаправляются на главную страницу с предупреждением

### 2.2 Основные пользовательские потоки

#### Сценарий 1: Просмотр списка задач
1. Пользователь переходит на `/tasks/my-tasks`
2. Система проверяет права доступа
3. Загружается страница с индикатором загрузки
4. Отображается таблица задач с пагинацией (по умолчанию 25 записей)
5. Пользователь может переключать количество записей на странице (10, 25, 50, 100)

#### Сценарий 2: Фильтрация задач
1. Пользователь выбирает фильтр (статус/проект/приоритет)
2. Таблица автоматически обновляется без перезагрузки страницы
3. Появляется кнопка очистки фильтра
4. Обновляется статистика в карточках разбивки
5. Пользователь может комбинировать несколько фильтров

#### Сценарий 3: Поиск задач
1. Пользователь вводит поисковый запрос в поле поиска
2. Поиск выполняется по полям: subject, description, ID
3. Результаты отображаются в реальном времени
4. Поиск работает совместно с фильтрами

#### Сценарий 4: Просмотр детализации задачи
1. Пользователь кликает на ID задачи в таблице
2. Переход на страницу `/tasks/my-tasks/{task_id}`
3. Отображается полная информация о задаче
4. Доступны журналы изменений, вложения, связи

#### Сценарий 5: Анализ статистики
1. Пользователь просматривает карточки разбивки по статусам
2. Кликает на кнопку детализации карточки
3. Раскрывается подробная информация по статусам
4. Может развернуть/свернуть все карточки глобальной кнопкой

#### Сценарий 6: Переход в Redmine
1. Пользователь кликает "Перейти в Redmine"
2. Открывается новая вкладка с системой Redmine
3. Или кликает "Мои заявки" для перехода на страницу заявок

## 3. Структура интерфейса

### 3.1 Заголовок страницы (Header Section)
```html
<header class="page-header">
  <div class="header-content">
    <div class="header-main">
      <div class="header-icon">
        <i class="fas fa-tasks"></i>
      </div>
      <div class="header-text">
        <h1 class="page-title">Мои задачи в Redmine</h1>
        <p class="page-subtitle">Управление и мониторинг ваших задач в Redmine</p>
      </div>
    </div>
    <div class="header-actions">
      <a href="https://helpdesk.teztour.com" class="action-button secondary">
        <i class="fas fa-external-link-alt"></i>
        <span>Перейти в Redmine</span>
      </a>
      <a href="{{ url_for('main.my_issues') }}" class="action-button primary">
        <i class="fas fa-ticket-alt"></i>
        <span>Мои заявки</span>
      </a>
    </div>
  </div>
</header>
```

**Компоненты:**
- Иконка задач (Font Awesome)
- Заголовок и подзаголовок
- Кнопка "Перейти в Redmine" (внешняя ссылка)
- Кнопка "Мои заявки" (внутренняя навигация)

### 3.2 Панель статистики (Status Breakdown Dashboard)
```html
<section class="status-breakdown-dashboard">
  <div class="breakdown-header">
    <div class="breakdown-title">
      <i class="fas fa-chart-pie"></i>
      <h2>Разбивка по статусам</h2>
    </div>
    <div class="breakdown-summary">
      <span class="summary-value" id="total-tasks-summary">-</span>
      <span class="summary-label">всего задач</span>
      <button class="global-toggle-btn" id="globalToggleBtn">
        <i class="fas fa-expand-alt"></i>
        <span>Развернуть все</span>
      </button>
    </div>
  </div>

  <div class="status-breakdown-grid">
    <!-- 4 карточки: Всего, Открытые, Закрытые в БД, Приостановленные -->
  </div>
</section>
```

**Карточки статистики:**
1. **Всего задач** - общее количество
2. **Открытые задачи** - новые и ожидающие
3. **Закрытые в БД** - фактически закрытые
4. **Приостановленные** - на паузе и заморожены

Каждая карточка имеет:
- Иконку статуса
- Заголовок
- Числовое значение
- Описание
- Кнопку детализации (разворачивает/сворачивает подробности)

### 3.3 Панель фильтров
```html
<div class="filters-section">
  <div class="filter-container">
    <label class="filter-label">Статус:</label>
    <select id="status-filter" class="filter-select">
      <option value="">Все статусы</option>
      <!-- Динамически загружаемые опции -->
    </select>
    <button class="clear-filter-btn" id="clear-status-filter">
      <i class="fas fa-times"></i>
    </button>
  </div>

  <div class="filter-container">
    <label class="filter-label">Проект:</label>
    <select id="project-filter" class="filter-select">
      <option value="">Все проекты</option>
      <!-- Динамически загружаемые опции -->
    </select>
    <button class="clear-filter-btn" id="clear-project-filter">
      <i class="fas fa-times"></i>
    </button>
  </div>

  <div class="filter-container">
    <label class="filter-label">Приоритет:</label>
    <select id="priority-filter" class="filter-select">
      <option value="">Все приоритеты</option>
      <!-- Динамически загружаемые опции -->
    </select>
    <button class="clear-filter-btn" id="clear-priority-filter">
      <i class="fas fa-times"></i>
    </button>
  </div>
</div>
```

### 3.4 Таблица задач (DataTables)
```html
<table id="tasksTable" class="display modern-datatable">
  <thead>
    <tr>
      <th data-column="id">ID</th>
      <th data-column="project">Проект</th>
      <th data-column="tracker">Трекер</th>
      <th data-column="status">Статус</th>
      <th data-column="priority">Приоритет</th>
      <th data-column="subject">Тема</th>
      <th data-column="assigned_to">Назначена</th>
      <th data-column="easy_email_to">Email отправителя</th>
      <th data-column="updated_on">Обновлена</th>
    </tr>
  </thead>
  <tbody>
    <!-- Динамически загружаемые строки -->
  </tbody>
</table>
```

### 3.5 Элементы загрузки
```html
<!-- Основной спинер загрузки -->
<div id="loading-spinner" class="loading-overlay">
  <div class="loading-content">
    <div class="spinner-icon">
      <i class="fas fa-cog fa-spin"></i>
    </div>
    <h3>Загрузка задач...</h3>
    <p>Подключение к системе Redmine и получение данных</p>
  </div>
</div>

<!-- Индикатор обработки DataTables -->
<div class="dt-processing">
  <div class="processing-content">
    <i class="fas fa-spinner fa-spin"></i>
    <span>Обработка...</span>
  </div>
</div>
```

## 4. API и данные

### 4.1 Основные API маршруты

#### GET `/tasks/my-tasks`
**Назначение:** Отображение главной страницы задач
**Параметры:** Нет
**Ответ:** HTML-страница с шаблоном

#### GET `/tasks/get-my-tasks-paginated`
**Назначение:** Получение списка задач с пагинацией для DataTables
**Параметры:**
```javascript
{
  draw: 1,                    // Номер запроса DataTables
  start: 0,                   // Смещение для пагинации
  length: 25,                 // Количество записей на странице
  "search[value]": "",        // Поисковый запрос
  "order[0][column]": 0,      // Индекс столбца для сортировки
  "order[0][dir]": "desc",    // Направление сортировки
  "status_id[]": [],          // Массив ID статусов для фильтрации
  "project_id[]": [],         // Массив ID проектов для фильтрации
  "priority_id[]": []         // Массив ID приоритетов для фильтрации
}
```

**Ответ:**
```javascript
{
  draw: 1,
  recordsTotal: 150,          // Общее количество записей
  recordsFiltered: 25,        // Количество записей после фильтрации
  data: [                     // Массив объектов задач
    {
      id: 12345,
      subject: "Исправить ошибку в модуле авторизации",
      status: {
        id: 2,
        name: "В работе"
      },
      priority: {
        id: 4,
        name: "Высокий"
      },
      project: {
        id: 10,
        name: "Система поддержки"
      },
      tracker: {
        id: 1,
        name: "Ошибка"
      },
      author: {
        id: 5,
        name: "Иван Петров"
      },
      assigned_to: {
        id: 3,
        name: "Мария Сидорова"
      },
      easy_email_to: "client@example.com",
      created_on: "2024-01-15 10:30:00",
      updated_on: "2024-01-16 14:20:00",
      start_date: "2024-01-15",
      due_date: "2024-01-20",
      done_ratio: 75,
      estimated_hours: 8.0,
      spent_hours: 6.0,
      description: "Подробное описание задачи...",
      custom_fields: {
        "Категория": "Техническая",
        "Срочность": "Критическая"
      }
    }
  ]
}
```

#### GET `/tasks/get-my-tasks-statistics-optimized`
**Назначение:** Получение статистики по задачам для карточек
**Параметры:** Нет
**Ответ:**
```javascript
{
  total_tasks: 150,
  open_tasks: 45,
  closed_db_tasks: 85,
  paused_tasks: 20,
  status_counts: {
    "Новая": 15,
    "В работе": 20,
    "Ожидает ответа": 10,
    "Закрыта": 85,
    "Приостановлена": 20
  },
  detailed_breakdown: {
    open_statuses: ["Новая", "В работе", "Ожидает ответа"],
    closed_statuses: ["Закрыта", "Решена", "Отклонена"],
    paused_statuses: ["Приостановлена", "Заморожена"]
  }
}
```

#### GET `/tasks/get-my-tasks-filters-optimized`
**Назначение:** Получение опций для фильтров
**Параметры:** Нет
**Ответ:**
```javascript
{
  statuses: [
    {id: 1, name: "Новая", is_closed: false},
    {id: 2, name: "В работе", is_closed: false},
    {id: 5, name: "Закрыта", is_closed: true}
  ],
  projects: [
    {
      id: 10,
      name: "Система поддержки",
      parent_id: null,
      level: 0,
      children: [
        {id: 11, name: "Модуль авторизации", parent_id: 10, level: 1}
      ]
    }
  ],
  priorities: [
    {id: 1, name: "Низкий"},
    {id: 2, name: "Обычный"},
    {id: 3, name: "Высокий"},
    {id: 4, name: "Критический"}
  ]
}
```

#### GET `/tasks/my-tasks/{task_id}`
**Назначение:** Детальная страница задачи
**Параметры:** `task_id` (integer) - ID задачи
**Ответ:** HTML-страница с детальной информацией

### 4.2 Формат данных задачи

Каждая задача в системе представлена объектом со следующими полями:

```typescript
interface Task {
  // Основные поля
  id: number;                    // Уникальный ID задачи
  subject: string;               // Тема/заголовок задачи
  description: string;           // Описание задачи (до 1000 символов)

  // Связанные объекты
  status: {
    id: number;
    name: string;
  };
  priority: {
    id: number;
    name: string;
  };
  project: {
    id: number;
    name: string;
  };
  tracker: {
    id: number;
    name: string;
  };
  author: {
    id: number;
    name: string;
  };
  assigned_to: {
    id: number;
    name: string;
  };

  // Временные метки
  created_on: string;            // ISO datetime строка
  updated_on: string;            // ISO datetime строка
  start_date: string | null;     // Дата начала (YYYY-MM-DD)
  due_date: string | null;       // Срок выполнения (YYYY-MM-DD)
  closed_on: string | null;      // Дата закрытия

  // Дополнительные поля
  done_ratio: number;            // Процент выполнения (0-100)
  estimated_hours: number | null; // Оценочное время
  spent_hours: number | null;    // Затраченное время
  easy_email_to: string;         // Email отправителя заявки

  // Пользовательские поля
  custom_fields: Record<string, string>;

  // Вычисляемые поля для удобства
  status_name: string;
  priority_name: string;
  project_name: string;
  tracker_name: string;
  author_name: string;
  assigned_to_name: string;
}
```

## 5. Состояния страницы

### 5.1 Состояние загрузки (Loading State)
```css
.loading-overlay {
  display: flex;
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  z-index: 9999;
}
```

**Триггеры:**
- Первоначальная загрузка страницы
- Применение фильтров
- Поиск
- Изменение пагинации

**Индикаторы:**
- Полноэкранный спинер с анимацией
- Текст "Загрузка задач..."
- Синий цвет спинера (#3b82f6)

### 5.2 Состояние пустого списка (Empty State)
```html
<div class="empty-state">
  <i class="fas fa-inbox empty-icon"></i>
  <h3>Задач не найдено</h3>
  <p>По вашим критериям поиска задачи не найдены</p>
  <button class="btn-reset-filters">Сбросить фильтры</button>
</div>
```

**Условия:**
- Нет задач, соответствующих фильтрам
- Поиск не дал результатов
- У пользователя нет назначенных задач

### 5.3 Состояние ошибки (Error State)
```html
<div class="error-state">
  <i class="fas fa-exclamation-triangle error-icon"></i>
  <h3>Ошибка загрузки данных</h3>
  <p>Не удалось подключиться к системе Redmine</p>
  <button class="btn-retry">Попробовать снова</button>
</div>
```

**Типы ошибок:**
- Ошибка аутентификации в Redmine
- Сетевые ошибки
- Таймауты подключения
- Ошибки сервера (500)

### 5.4 Состояние отсутствия доступа (Access Denied)
```html
<div class="access-denied">
  <i class="fas fa-lock"></i>
  <h3>Доступ запрещен</h3>
  <p>У вас нет прав для просмотра задач Redmine</p>
</div>
```

**Условия:**
- `current_user.is_redmine_user = False`
- Автоматическое перенаправление на главную страницу

### 5.5 Состояние обработки фильтров (Processing State)
```css
.dt-processing {
  display: block;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(255, 255, 255, 0.9);
  padding: 20px;
  border-radius: 8px;
}
```

**Триггеры:**
- Изменение фильтров
- Сортировка столбцов
- Поиск в реальном времени

## 6. Бизнес-логика

### 6.1 Правила доступа

#### Проверка прав пользователя
```python
@login_required
def my_tasks_page():
    if not current_user.is_redmine_user:
        flash("У вас нет доступа к модулю 'Мои задачи'", "warning")
        return redirect(url_for("main.home"))
```

#### Аутентификация в Redmine
```python
# Использование пароля из локальной БД для оптимизации
redmine_connector_instance = create_redmine_connector(
    is_redmine_user=current_user.is_redmine_user,
    user_login=current_user.username,
    password=current_user.password  # Пароль из модели User
)
```

### 6.2 Фильтрация задач

#### Правила отображения задач
- Показываются только задачи, назначенные текущему пользователю
- Фильтрация происходит на стороне Redmine API
- Поддерживаются множественные фильтры (AND логика)

#### Логика фильтров
```javascript
// Статус: может быть пустым (все статусы) или конкретный ID
status_ids = request.args.getlist("status_id[]")

// Проект: поддерживает иерархию (родительские/дочерние проекты)
project_ids = request.args.getlist("project_id[]")

// Приоритет: простая фильтрация по ID
priority_ids = request.args.getlist("priority_id[]")
```

### 6.3 Поиск

#### Поисковые поля
- `subject` - тема задачи (основное поле)
- `description` - описание задачи
- `id` - точный поиск по ID

#### Логика поиска
```python
# Поиск выполняется через Redmine API
search_value = request.args.get("search[value]", "", type=str).strip()
if search_value:
    filter_params['q'] = search_value  # Полнотекстовый поиск Redmine
```

### 6.4 Сортировка

#### Доступные поля для сортировки
```python
column_mapping = {
    'id': 'id',
    'project': 'project.name',
    'tracker': 'tracker.name',
    'status': 'status.name',
    'priority': 'priority.name',
    'subject': 'subject',
    'assigned_to': 'assigned_to.name',
    'easy_email_to': 'easy_email_to',
    'updated_on': 'updated_on',
    'created_on': 'created_on',
    'due_date': 'due_date'
}
```

#### Сортировка по умолчанию
- Поле: `updated_on`
- Направление: `desc` (сначала новые)

### 6.5 Пагинация

#### Настройки пагинации
- По умолчанию: 25 записей на странице
- Доступные варианты: 10, 25, 50, 100
- Серверная пагинация через Redmine API

#### Подсчет записей
```python
def get_accurate_task_count(redmine_connector, filter_params):
    # Использует total_count из Redmine API
    # Fallback на итерацию с лимитом 1001
```

### 6.6 Статистика

#### Категории статусов
```python
def get_status_type(status_name):
    open_statuses = ['Новая', 'В работе', 'Ожидает ответа', 'Назначена']
    closed_statuses = ['Закрыта', 'Решена', 'Отклонена']
    paused_statuses = ['Приостановлена', 'Заморожена', 'На паузе']
```

#### Расчет метрик
- **Всего задач**: общее количество назначенных пользователю
- **Открытые**: статусы из категории "открытые"
- **Закрытые в БД**: статусы с флагом `is_closed = true`
- **Приостановленные**: статусы из категории "приостановленные"

## 7. Технические ограничения и особенности

### 7.1 Производительность

#### Оптимизации
- **Кэширование выходных дней**: `@weekend_performance_optimizer`
- **Локальное хранение паролей**: избегание обращений к Oracle ERP
- **Ленивая загрузка фильтров**: асинхронная загрузка опций
- **Пагинация на сервере**: ограничение объема передаваемых данных

#### Ограничения
- **Лимит поиска**: максимум 1001 запись для подсчета
- **Таймауты**: 30 секунд на запросы к Redmine API
- **Размер описания**: обрезается до 1000 символов

### 7.2 Зависимости

#### Внешние сервисы
```python
# Redmine API
from redminelib import Redmine
from redminelib.exceptions import ResourceNotFoundError

# Oracle ERP (для паролей - deprecated)
import cx_Oracle
```

#### JavaScript библиотеки
```html
<!-- DataTables для таблиц -->
<script src="datatables.min.js"></script>

<!-- Font Awesome для иконок -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">

<!-- jQuery (требуется для DataTables) -->
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
```

### 7.3 Совместимость браузеров

#### Поддерживаемые браузеры
- Chrome 80+ ✅
- Firefox 75+ ✅
- Safari 13+ ✅
- Edge 80+ ✅

#### CSS особенности
```css
/* Backdrop filter поддержка */
backdrop-filter: blur(20px);
-webkit-backdrop-filter: blur(20px);

/* CSS Grid для адаптивности */
.status-breakdown-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}
```

### 7.4 Безопасность

#### Аутентификация
- Проверка `is_redmine_user` на каждом запросе
- Использование собственных учетных данных пользователя
- Защита от CSRF через Flask-WTF

#### Валидация данных
```python
# Санитизация поисковых запросов
search_value = request.args.get("search[value]", "", type=str).strip()

# Валидация параметров пагинации
page = request.args.get("start", 0, type=int) // request.args.get("length", 25, type=int) + 1
per_page = request.args.get("length", 25, type=int)
```

### 7.5 Логирование и мониторинг

#### Логирование событий
```python
current_app.logger.info(f"Запрос /tasks/get-my-tasks-paginated для {current_user.username}")
current_app.logger.error(f"Ошибка при получении задач: {str(e)}")
current_app.logger.warning(f"Пользователь {current_user.username} не является пользователем Redmine")
```

#### Метрики производительности
```python
start_time = time.time()
# ... выполнение запроса ...
execution_time = time.time() - start_time
current_app.logger.info(f"Запрос выполнен за {execution_time:.2f} сек")
```

## 8. Возможные улучшения

### 8.1 Известные проблемы

#### Производительность
- **Медленные запросы**: при большом количестве задач (>1000) запросы могут выполняться медленно
- **Дублирование спинеров**: иногда показывается несколько индикаторов загрузки одновременно
- **Проблемы с кэшированием**: изменения в шаблонах не всегда отображаются сразу

#### UX/UI
- **Фильтры сбрасываются**: при обновлении страницы теряется состояние фильтров
- **Отсутствие индикации**: нет визуальной обратной связи при применении фильтров
- **Мобильная адаптивность**: таблица плохо отображается на малых экранах

#### Функциональность
- **Ограниченный поиск**: поиск работает только по базовым полям
- **Отсутствие экспорта**: нет возможности экспорта данных в Excel/CSV
- **Нет bulk операций**: нельзя выполнять массовые действия над задачами

### 8.2 Рекомендации по рефакторингу

#### Архитектурные улучшения
1. **Разделение на компоненты**: выделить отдельные Vue.js/React компоненты
2. **State management**: использовать Vuex/Redux для управления состоянием
3. **API стандартизация**: перейти на REST API с консистентными эндпоинтами
4. **Кэширование**: реализовать Redis кэш для часто запрашиваемых данных

#### Технические улучшения
1. **TypeScript**: добавить типизацию для лучшей поддерживаемости
2. **Webpack**: настроить сборку ассетов для оптимизации
3. **Testing**: добавить unit и integration тесты
4. **Error boundaries**: улучшить обработку ошибок

#### UX улучшения
1. **Infinite scroll**: заменить пагинацию на бесконечную прокрутку
2. **Real-time updates**: WebSocket уведомления об изменениях
3. **Advanced filters**: добавить фильтры по датам, исполнителям, etc.
4. **Keyboard shortcuts**: горячие клавиши для быстрой навигации

### 8.3 Миграционный план

#### Фаза 1: Стабилизация (2-3 недели)
- Исправление критических багов
- Оптимизация производительности
- Улучшение логирования

#### Фаза 2: Модернизация UI (4-6 недель)
- Переход на современный CSS framework (Tailwind CSS)
- Адаптивный дизайн
- Улучшение accessibility

#### Фаза 3: Архитектурные изменения (8-12 недель)
- Разделение на микросервисы
- Внедрение фронтенд фреймворка
- API реорганизация

#### Фаза 4: Расширение функциональности (6-8 недель)
- Добавление новых фич
- Интеграция с дополнительными системами
- Аналитика и отчетность

### 8.4 Схема данных для нового API

#### Предлагаемая структура REST API
```
GET    /api/v2/tasks                    # Список задач с фильтрами
POST   /api/v2/tasks                    # Создание задачи
GET    /api/v2/tasks/{id}               # Детали задачи
PUT    /api/v2/tasks/{id}               # Обновление задачи
DELETE /api/v2/tasks/{id}               # Удаление задачи

GET    /api/v2/tasks/statistics         # Статистика по задачам
GET    /api/v2/tasks/filters            # Опции для фильтров

POST   /api/v2/tasks/bulk-update        # Массовые операции
POST   /api/v2/tasks/export             # Экспорт данных
```

#### Стандартизированный формат ответов
```json
{
  "success": true,
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "per_page": 25,
      "total": 150,
      "pages": 6
    },
    "filters": {
      "applied": {...},
      "available": {...}
    }
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2024-01-16T10:30:00Z",
    "execution_time": 0.245
  }
}
```

Эта документация предоставляет полное понимание текущего состояния страницы `/tasks/my-tasks` и может служить основой для дальнейшего развития и рефакторинга системы.
