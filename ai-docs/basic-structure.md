## Flask Helpdesk — базовая структура проекта

Краткий обзор директорий, модулей и ключевых файлов. Документ предназначен для быстрого ориентирования в кодовой базе и не описывает второстепенные артефакты.

### Корень репозитория
- `app.py` / `wsgi.py`: точки входа приложения (runserver и WSGI). Поднимают Flask‑приложение, регистрируют блюпринты, настраивают конфигурацию и расширения.
- `config.py` / `config.ini`: конфигурация приложения и внешних сервисов. INI — операционные параметры (пути ERP и пр.).
- `requirements.txt`: зависимости Python.
- `scripts/`: служебные скрипты (инициализация БД, миграции, мониторинг, деплой). См. `scripts/README.md`.
- `migrations/`: инфраструктура Alembic с версиями миграций.
- `logs/`: логи приложения для отладки.
- `memory-bank/`: проектные документы (брief, текконтекст, стили, задачи). Используется как база знаний проекта.
- `mysql_db.py`: декларативные модели SQLAlchemy для MySQL‑таблиц, используемых для локализаций (статусы/приоритеты/пользователи).
- `redmine.py` / `blog/redmine.py`: функции для работы с Redmine/MySQL (получение имён статусов/приоритетов, маппинг свойств).
- `erp_oracle.py`: интеграция с ERP/Oracle (аутентификация и бизнес‑операции).

### Пакет `blog/` — основное приложение
Много-модульная структура на Flask с блюпринтами по доменам.

- `blog/__init__.py`: фабрика приложения/инициализация расширений, регистрация блюпринтов (`main`, `tasks`, `user`, `netmonitor`, `finesse`, `post`, `call`).
- `blog/models.py`: ORM‑модели локальной БД (SQLite) — пользователи, посты, настройки и т.п.
- `blog/settings.py`: прикладные настройки, флаги и константы UI/поведения.
- `blog/migrations.py`: вспомогательная логика миграций под запуск из приложения.
- `blog/db_config.py`: параметры подключения к внешним БД (MySQL Redmine и др.).
- `blog/firebase_push_service.py`: сервис отправки push через Firebase Admin SDK (Web Push совместимость).
- `blog/notification_service.py`: фоновые уведомления; интеграция с планировщиком.
- `blog/scheduler_tasks.py`: задания APScheduler (привязка задач к пользователю, периодические джобы).

#### Блюпринты
- `blog/main/`
  - `routes.py`, `forms.py`: стартовые страницы, общий UI, рендер основных шаблонов.
- `blog/tasks/`
  - `routes.py`: страницы «Мои задачи», канбан, фильтры; прямые SQL‑выборки для быстрого UI. Возвращает локализованные названия статусов/приоритетов (через `u_statuses`, `u_Priority`). Ключевой эндпоинт: `get_my_tasks_direct_sql` — источник данных для канбана/таблицы.
  - `api_routes.py`: REST API по задачам (доступные статусы/приоритеты, смена статуса/приоритета/исполнителя, вложения). Подключается к Redmine и локализует названия из MySQL.
  - `utils.py`, `utils_edit.py`: вспомогательные функции (кэш/оптимизации/форматирование/редактирование).
- `blog/user/`
  - `routes.py`, `forms.py`, `utils.py`: аутентификация (ERP/Oracle), профиль, права, загрузка аватара, системные действия.
- `blog/netmonitor/`
  - `routes.py`: пинг/история/статус хостов, сводные страницы быстрого мониторинга сети.
- `blog/finesse/`
  - `routes.py`: прокси‑эндпоинты Cisco Finesse; операции трансфера звонков; статические артефакты гаджета (`static/js`, `templates/finesse/callTransfer.html`).
- `blog/post/`
  - `routes.py`, `forms.py`, `utils.py`: блог/статьи, CRUD, загрузка изображений; шаблоны отображения контента.
- `blog/call/`
  - `routes.py`: вспомогательная логика вызовов (интеграция со звонками/гаджетами при необходимости).

#### Конфигурация и утилиты
- `blog/config/`
  - `vapid_keys.py`: ключи VAPID и параметры Firebase (`FIREBASE_PROJECT_ID`, `FIREBASE_SERVICE_ACCOUNT_PATH`).
- `blog/utils/`
  - `cache_manager.py`: кэширование ответов и объектов для ускорения UI.
  - `connection_monitor.py`: контроль и метрики соединений с внешними БД/API.
  - `email_sender.py`: отправка email‑уведомлений/шаблоны.
  - `logger.py`: централизованный логгер.
  - `template_helpers.py`: хелперы для шаблонов (форматирование, безопасный вывод, преобразования).

#### Шаблоны и статические файлы
- `blog/templates/`: Jinja2 шаблоны страниц. Ключевые шаблоны:
  - `layout.html`: базовый макет, общие стили/скрипты, сплэш‑экран.
  - `my_tasks.html`: интерфейсы списка/канбана; подключение задачных скриптов.
  - `task_detail.html`, `issues.html`, `issue.html`: карточка/перечень задач.
  - `post.html`, `create_post.html`, `update_post.html`: блог/статьи.
  - `profile.html`, `users.html`, `login.html`, `register.html`: пользовательские страницы.
  - `network_monitor.html`: мониторинг сети.
- `blog/static/`: ресурсы фронтенда.
  - `static/js/pages/tasks/`: модульная фронтенд‑часть задач.
    - `core/`: инфраструктура UI (`EventBus.js`, `LoadingManager.js`, `TasksApp.js`).
    - `services/TasksAPI.js`: работа с эндпоинтами задач/фильтров.
    - `components/`:
      - `KanbanManager.js`: логика канбана (создание колонок/карточек, DnD, фильтры, подгрузки). Источник данных — `get_my_tasks_direct_sql`.
      - `TasksTable.js` и `TasksTable_Simple.js`: рендер табличного вида.
      - `FiltersPanel*.js`, `StatisticsPanel*.js`: фильтры и сводные показатели.
      - `KanbanOnboarding.js`, `KanbanTips.js`, `KanbanTooltips.js`: подсказки и онбординг.
    - `utils/`: утилиты фронтенда (`debounce.js`, `validators.js`).
  - `static/css/pages/tasks/`: стили таблицы/канбана и подсказок (`tasks.css`, `kanban-*.css`).
  - Другие ключевые файлы: `modern_splash_screen.js`, `my_tasks_app.js`, `tasks_paginated.js`, набор глобальных UI‑фиксов.

### Ключевые потоки данных и интеграции
- Redmine: REST API и прямой доступ к MySQL (таблицы `u_statuses`, `enumerations`, `u_Priority`). Названия статусов/приоритетов берутся из MySQL для локализации. Коннектор создаётся точечно в API задач; пароль пользователя подтягивается из ERP при надобности.
- ERP/Oracle: проверка логина и синхронизация пароля/атрибутов пользователя (`erp_oracle.py`, вызовы из `blog/user/routes.py`).
- Уведомления: фоновые задачи (APScheduler) и push через Firebase (`blog/firebase_push_service.py`).
- Кэш/мониторинг: `blog/utils/cache_manager.py` и `blog/utils/connection_monitor.py`.

### Важные эндпоинты (по файлам)
- `blog/tasks/api_routes.py`:
  - `GET /tasks/api/task/<id>/statuses` — доступные статусы (локализованы).
  - `PUT /tasks/api/task/<id>/status` — изменение статуса.
  - `PUT /tasks/api/task/<id>/priority` — изменение приоритета; возвращает локализованное имя из `u_Priority`.
  - `PUT /tasks/api/task/<id>/assignee` — смена исполнителя.
  - `GET /tasks/api/task/<id>/attachment/<attachment_id>/download` — загрузка вложения (прокси Redmine).
- `blog/tasks/routes.py`:
  - `GET /tasks/get-my-tasks-direct-sql` — быстрый источник данных для списка/канбана. Выдаёт статусы/приоритеты в локализованном виде; группировка и ограничение по статусам для канбана.

### Организация и соглашения
- Блюпринты по доменам с чётким разграничением UI (`templates`, `static`) и серверной логики (`routes.py`, `api_routes.py`).
- Локализация статусов/приоритетов — только из MySQL (`u_statuses`, `u_Priority`), без хардкода.
- Планировщик — глобальный, задачи именуются с привязкой к пользователю, без создания отдельных инстансов.
- Безопасность: `login_required` для пользовательских и задачных страниц; точечные исключения CSRF для JSON API.

### Мини‑FAQ по навигации в коде
- Изменить канбан/таблицу задач: см. `blog/static/js/pages/tasks/components/` и `blog/templates/my_tasks.html`.
- Добавить действие по задаче: сервер — `blog/tasks/api_routes.py`; фронт — `services/TasksAPI.js` и соответствующий компонент.
- Обновить локализацию статусов/приоритетов: запросы в `blog/tasks/api_routes.py` и `blog/tasks/routes.py`; SQL‑хелперы в `redmine.py`/`mysql_db.py`.
- Настроить push/Web Push: `blog/config/vapid_keys.py`, `blog/firebase_push_service.py`.
