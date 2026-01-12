# Flask Helpdesk (TEZ Navigator) — Полное описание проекта

## Цель проекта
- Создать единое веб‑приложение для работы с обращениями Easy Redmine, уведомлениями и корпоративными интеграциями (ERP/Oracle, Cisco Finesse), с упором на удобство сотрудников, стабильность и производительность.
- Снизить переключение контекстов между системами: управление задачами, оперативные уведомления и служебные инструменты — в одном интерфейсе.

## Основные функции
- **Управление задачами Redmine**:
  - Просмотр деталей задачи и метаданных.
  - Изменение статуса с локализованными названиями из БД Redmine.
  - Изменение приоритета с локализацией.
  - Назначение/смена исполнителя, скачивание вложений.
  - Кэширование ответов и соединений; оптимизация в выходные.
- **Уведомления**:
  - Современный виджет уведомлений с управлением звуком, отметкой «прочитано», сбросом «увиденных» и диагностикой.
  - Фоновая обработка уведомлений планировщиком, привязка задач APScheduler к пользователю.
  - Поддержка push через Firebase Admin SDK, совместимость с Web Push (VAPID).
- **Пользователи и аутентификация**:
  - Логин через ERP/Oracle с проверкой и синхронизацией пароля в локальной БД.
  - Профиль, обновление VPN‑даты, аватар/подпись, управление правами (админ, доступ к качеству и др.).
- **Контроль качества**: доступ к разделу качества по разрешениям.
- **Сетевой монитор**: пинг целевых хостов (история/статус) для быстрой диагностики.
- **Cisco Finesse интеграция**: проксирование запросов для трансфера звонков и получения диалогов.

## Используемые технологии и архитектура
- **Backend**: Flask (Blueprints: `blog/main`, `blog/tasks`, `blog/user`, `blog/netmonitor`, `blog/finesse`), Flask‑Login, Flask‑WTF (CSRF), APScheduler.
- **Данные**: SQLite (локальные модели), Oracle (ERP), MySQL (Redmine, локализация статусов/приоритетов/проектов).
- **Интеграции**: Redmine REST API, Oracle ERP (`oracledb`), MySQL (`PyMySQL`), Cisco Finesse (proxy), `requests`, Flask‑CORS.
- **Уведомления**: Firebase Admin SDK для push; VAPID ключи для Web Push.
- **Frontend**: Jinja2 шаблоны, JS/CSS в `blog/static/` (включая modern splash screen).

## Целевая аудитория
- Сотрудники и ИТ‑подразделения, работающие с тикетами/уведомлениями Redmine и ERP‑интеграциями.
- Диспетчеры/операторы контакт‑центров, использующие Cisco Finesse.

## Этапы разработки (пайплайн)
- База: инициализация приложения, блюпринтов, моделей и миграций; подключение Oracle/MySQL/SQLite.
- Функционал задач: статусы/приоритеты/исполнители/вложения; локализация из MySQL; кэширование и оптимизации.
- Уведомления/фон: планировщик под пользователя, виджет, звук/пуш.
- Интеграции: ERP/Oracle логин, Cisco Finesse прокси/трансфер.
- UX/Frontend: сплэш‑экран, улучшения виджета, адаптив.
- Безопасность/эксплуатация: CSRF/`login_required`, раздельные БД, логи и мониторинг.

## Ожидаемые результаты
- Ускорение работы с обращениями (меньше переключений).
- Своевременные уведомления (звук/push), снижение ручных действий.
- Единая точка входа для смежных корпоративных сервисов.
- Стабильность за счёт мониторинга соединений и кэширования.

## Примеры API
- Получить доступные статусы: `GET /tasks/api/task/{task_id}/statuses` — список статусов, локализованный через MySQL `u_statuses`.
- Изменить статус: `PUT /tasks/api/task/{task_id}/status` с телом `{ "status_id": <int>, "comment": "..." }`.
- Изменить приоритет: `PUT /tasks/api/task/{task_id}/priority` с телом `{ "priority_id": <int>, "comment": "..." }`.
- Сменить исполнителя: `PUT /tasks/api/task/{task_id}/assignee` с телом `{ "assignee_id": <int>, "comment": "..." }`.
- Скачать вложение: `GET /tasks/api/task/{task_id}/attachment/{attachment_id}/download` — URL скачивания из Redmine.

## Ключевые преимущества
- **Единое окно**: задачи, уведомления, интеграции и утилиты в одном UI.
- **Глубокие интеграции**: аутентификация/атрибуты из ERP; действия в Redmine от имени пользователя.
- **Производительность**: кэш ответов и соединений; оптимизации в выходные.
- **Оперативность**: фоновые уведомления, звук и push.
- **Локализация**: статусы/приоритеты — из MySQL Redmine, без хардкода.
- **Надёжность**: мониторинг соединений, диагностика и логи.

## Проектные соглашения и правила
- **Статусы/приоритеты не хардкодить**: названия и списки брать из БД Redmine (`u_statuses`, `enumerations`, `u_Priority`).
- **Коннектор Redmine**: создавать через `create_redmine_connector`; пароль получать из ERP/Oracle (`get_user_redmine_password`) перед действиями.
- **Планировщик**: использовать глобальный `scheduler` из `blog`; задачи с ID вида `notification_job_{user_id}`; не создавать отдельные инстансы.
- **Кэширование**: ответы — `cached_response`/`cache_manager`; соединения — `tasks_cache_optimizer`.
- **Безопасность API**: `login_required` для REST по задачам; CSRF исключать точечно для JSON API.
- **Push‑уведомления**: приоритизировать Firebase Admin SDK; обновить ключи в `blog/config/vapid_keys.py` перед продом.

## Конфигурация и деплой
- **VAPID/Firebase**: обновить `FIREBASE_PROJECT_ID` и `FIREBASE_SERVICE_ACCOUNT_PATH` в `blog/config/vapid_keys.py`; ключи генерируются в Firebase Console (Cloud Messaging, раздел Web Push certificates) — адрес в документации указывать в виде `https://console.firebase.google.com`.
- **ERP файл**: проверить путь к ERP в `config.ini` и в `users.download_erp`.
- **БД**: миграции и доступность Oracle/MySQL; инициализация через `scripts/init_database.py`.
- **Сервис (Linux/systemd)**: управление сервисом — `sudo systemctl status flask-helpdesk`, `sudo systemctl restart flask-helpdesk`, `sudo systemctl stop flask-helpdesk`, логи — `sudo journalctl -u flask-helpdesk -f`.

## Опорные файлы/модули
- `blog/tasks/api_routes.py` — API задач (статусы, приоритеты, исполнители, вложения).
- `blog/user/routes.py` — аутентификация, профиль, права, планировщик уведомлений.
- `blog/firebase_push_service.py` — отправка push через Firebase Admin SDK.
- `blog/netmonitor/routes.py` — сетевой монитор (пинг/история/сводка).
- `blog/finesse/routes.py` — прокси и трансфер для Cisco Finesse.
- `blog/config/vapid_keys.py` — VAPID и Firebase настройки.
- `blog/utils/cache_manager.py`, `blog/utils/connection_monitor.py` — кэширование и мониторинг соединений.

## Структура проекта (высокоуровнево)
```
flask_helpdesk/
├── app.py
├── blog/
│   ├── __init__.py
│   ├── main/ · tasks/ · user/ · netmonitor/ · finesse/
│   ├── templates/ · static/
│   └── config/ · utils/ · db/
├── scripts/
├── migrations/
└── memory-bank/
```

## Примечания
- Для корректной работы звука уведомлений и виджета используйте инструкции в `SOUND_DIAGNOSTICS_README.md`.
- Современный сплэш‑экран подключён в `blog/templates/layout.html`, логика — `blog/static/js/modern_splash_screen.js`, стили — `blog/static/css/modern_splash_screen.css`.
