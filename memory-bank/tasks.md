# ТЕХНИЧЕСКОЕ ЗАДАНИЕ: Интеграция уведомлений Redmine

## ОБЩИЕ СВЕДЕНИЯ

**Название:** Система получения уведомлений о задачах Redmine для групп пользователей
**Дата создания:** {{ current_date }}
**Статус:** В планировании
**Приоритет:** Высокий

## ЦЕЛЬ И ЗАДАЧИ

### Основная цель
Интегрировать существующую систему уведомлений Flask Helpdesk с API Redmine для автоматического получения уведомлений о задачах, назначенных группе текущего пользователя.

### Задачи
1. **Синхронизация данных:** Настроить получение задач из Redmine через REST API
2. **Групповая логика:** Реализовать определение групп через связку таблиц users и groups_users
3. **Уведомления:** Интегрировать с существующим виджетом уведомлений
4. **Real-time обновления:** Обеспечить своевременное получение уведомлений об изменениях
5. **Настройки:** Предоставить пользователям возможность настройки уведомлений

## ТЕХНИЧЕСКАЯ АРХИТЕКТУРА

### Компоненты системы
1. **Redmine API Client** - модуль для работы с API Redmine
2. **Group Manager** - управление группами пользователей
3. **Notification Processor** - обработка и создание уведомлений
4. **Scheduler** - планировщик задач для периодической синхронизации
5. **Webhook Handler** - обработчик webhook'ов от Redmine (опционально)

### Технологический стек
- **API библиотека:** python-redmine
- **Планировщик:** APScheduler или Celery
- **База данных:** MySQL (существующая)
- **Кеширование:** Redis (опционально)

## СТРУКТУРА ДАННЫХ

### Полные SQL-скрипты для создания таблиц в MySQL

#### 1. МАКСИМАЛЬНО упрощенная таблица redmine_integration
Только URL Redmine и API ключ - больше ничего не нужно.

```sql
-- ============================================================
-- Таблица: redmine_integration (МАКСИМАЛЬНО упрощенная)
-- Назначение: Только URL и API ключ для подключения к Redmine
-- ============================================================

CREATE TABLE `redmine_integration` (
  `id` INT(11) NOT NULL AUTO_INCREMENT COMMENT 'ID интеграции',
  `user_id` INT(11) NOT NULL COMMENT 'ID пользователя Flask Helpdesk',
  `redmine_url` VARCHAR(255) NOT NULL COMMENT 'URL Redmine (https://redmine.company.com)',
  `api_key` VARCHAR(40) NOT NULL COMMENT 'API ключ Redmine',
  `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT 'Включена ли интеграция (0-нет, 1-да)',
  `last_sync` TIMESTAMP NULL COMMENT 'Время последней проверки новых задач',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Дата создания',

  PRIMARY KEY (`id`),

  -- Один пользователь - одна интеграция
  CONSTRAINT `fk_redmine_integration_user`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,

  UNIQUE KEY `uk_redmine_integration_user` (`user_id`)
    COMMENT 'Один пользователь - одна интеграция',

  -- Минимальные индексы
  INDEX `idx_redmine_integration_active` (`is_active`, `last_sync`)
    COMMENT 'Активные интеграции для синхронизации'

) ENGINE=InnoDB
  AUTO_INCREMENT=1
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Простые настройки подключения к Redmine (только URL + API ключ)';
```

### Убрано из redmine_integration:
- ❌ **api_key_hash** - не нужно усложнять
- ❌ **redmine_user_id, redmine_login** - не нужны для уведомлений
- ❌ **sync_interval_minutes** - всегда 5 минут, зашито в код
- ❌ **connection_status, connection_error** - либо работает, либо нет
- ❌ **settings_json** - никаких дополнительных настроек
- ❌ **updated_at** - не изменяется после создания
- ❌ **сложные индексы** - только один простой

#### 2. Таблица redmine_notifications
Хранит уведомления о задачах Redmine для пользователей Flask Helpdesk.

```sql
-- =================================================================
-- Таблица: redmine_notifications
-- Назначение: Уведомления о задачах Redmine для пользователей
-- =================================================================

CREATE TABLE `redmine_notifications` (
  `id` INT(11) NOT NULL AUTO_INCREMENT COMMENT 'Уникальный идентификатор уведомления',
  `user_id` INT(11) NOT NULL COMMENT 'ID пользователя-получателя уведомления',
  `redmine_issue_id` INT(11) NOT NULL COMMENT 'ID задачи в системе Redmine',
  `redmine_project_id` INT(11) NOT NULL COMMENT 'ID проекта в системе Redmine',
  `assigned_group_id` INT(11) NULL COMMENT 'ID группы, на которую назначена задача',
  `notification_type` VARCHAR(50) NOT NULL COMMENT 'Тип уведомления: assignment, status_change, comment, priority_change',
  `title` VARCHAR(500) NOT NULL COMMENT 'Заголовок уведомления',
  `description` TEXT NULL COMMENT 'Описание уведомления',
  `old_value` VARCHAR(255) NULL COMMENT 'Старое значение (для изменений)',
  `new_value` VARCHAR(255) NULL COMMENT 'Новое значение (для изменений)',
  `redmine_data` JSON NULL COMMENT 'Полные данные задачи из Redmine API',
  `redmine_journal_id` INT(11) NULL COMMENT 'ID записи журнала изменений в Redmine',
  `is_read` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Флаг прочтения (0-не прочитано, 1-прочитано)',
  `read_at` TIMESTAMP NULL COMMENT 'Время прочтения уведомления',
  `is_dismissed` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Флаг скрытия уведомления',
  `dismissed_at` TIMESTAMP NULL COMMENT 'Время скрытия уведомления',
  `priority` TINYINT(1) NOT NULL DEFAULT 1 COMMENT 'Приоритет уведомления (1-низкий, 2-обычный, 3-высокий)',
  `expires_at` TIMESTAMP NULL COMMENT 'Время истечения актуальности уведомления',
  `source_integration_id` INT(11) NOT NULL COMMENT 'ID интеграции, создавшей уведомление',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Дата создания уведомления',
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Дата последнего обновления',

  -- Первичный ключ
  PRIMARY KEY (`id`),

  -- Внешние ключи
  CONSTRAINT `fk_redmine_notifications_user_id`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,

  CONSTRAINT `fk_redmine_notifications_integration_id`
    FOREIGN KEY (`source_integration_id`) REFERENCES `redmine_integration` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,

  -- Уникальные ключи (предотвращение дублирования уведомлений)
  UNIQUE KEY `uk_redmine_notifications_unique` (`user_id`, `redmine_issue_id`, `notification_type`, `redmine_journal_id`)
    COMMENT 'Предотвращение дублирования уведомлений',

  -- Составные индексы для оптимизации запросов
  INDEX `idx_redmine_notifications_user_unread` (`user_id`, `is_read`, `created_at` DESC)
    COMMENT 'Быстрый поиск непрочитанных уведомлений пользователя',

  INDEX `idx_redmine_notifications_user_active` (`user_id`, `is_dismissed`, `expires_at`, `created_at` DESC)
    COMMENT 'Поиск активных уведомлений пользователя',

  INDEX `idx_redmine_notifications_issue` (`redmine_issue_id`, `created_at` DESC)
    COMMENT 'Поиск уведомлений по задаче Redmine',

  INDEX `idx_redmine_notifications_type` (`notification_type`, `created_at` DESC)
    COMMENT 'Поиск по типу уведомления',

  INDEX `idx_redmine_notifications_group` (`assigned_group_id`, `created_at` DESC)
    COMMENT 'Поиск уведомлений по группе',

  INDEX `idx_redmine_notifications_priority` (`priority`, `is_read`, `created_at` DESC)
    COMMENT 'Поиск по приоритету уведомлений',

  -- Простые индексы
  INDEX `idx_redmine_notifications_created` (`created_at` DESC) COMMENT 'Сортировка по дате создания',
  INDEX `idx_redmine_notifications_expires` (`expires_at`) COMMENT 'Поиск истекших уведомлений',
  INDEX `idx_redmine_notifications_read_at` (`read_at`) COMMENT 'Статистика по прочтению'

) ENGINE=InnoDB
  AUTO_INCREMENT=1
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Уведомления о задачах Redmine для пользователей Flask Helpdesk';
```

#### 3. МАКСИМАЛЬНО упрощенная таблица redmine_notifications
Только самое необходимое - уведомление о новой задаче в группе пользователя.

```sql
-- =================================================================
-- Таблица: redmine_notifications (МАКСИМАЛЬНО упрощенная версия)
-- Назначение: Уведомления "В вашу группу поступила новая задача"
-- =================================================================

CREATE TABLE `redmine_notifications` (
  `id` INT(11) NOT NULL AUTO_INCREMENT COMMENT 'ID уведомления',
  `user_id` INT(11) NOT NULL COMMENT 'ID пользователя-получателя',
  `redmine_issue_id` INT(11) NOT NULL COMMENT 'Номер задачи в Redmine (#263117)',
  `issue_subject` VARCHAR(500) NOT NULL COMMENT 'Тема задачи',
  `issue_description` TEXT NULL COMMENT 'Описание/текст задачи',
  `author_name` VARCHAR(255) NOT NULL COMMENT 'От кого (автор задачи)',
  `author_email` VARCHAR(255) NULL COMMENT 'Email автора',
  `group_name` VARCHAR(255) NOT NULL COMMENT 'Название группы исполнителей',
  `is_read` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Прочитано (0-нет, 1-да)',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Дата создания',

  PRIMARY KEY (`id`),

  -- Внешний ключ на пользователя
  CONSTRAINT `fk_redmine_notifications_user`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,

  -- Предотвращение дублирования
  UNIQUE KEY `uk_redmine_notifications_unique` (`user_id`, `redmine_issue_id`)
    COMMENT 'Один пользователь - одно уведомление на задачу',

  -- Основные индексы
  INDEX `idx_redmine_notifications_user_unread` (`user_id`, `is_read`, `created_at` DESC)
    COMMENT 'Непрочитанные уведомления пользователя',

  INDEX `idx_redmine_notifications_created` (`created_at` DESC)
    COMMENT 'Сортировка по дате'

) ENGINE=InnoDB
  AUTO_INCREMENT=1
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Уведомления о новых задачах Redmine в группах пользователей';
```

### Логика работы (МАКСИМАЛЬНО упрощенная):

**Что делает система:**
1. **Проверяет новые задачи** в Redmine каждые 5 минут
2. **Для каждой новой задачи** смотрит, на какую группу она назначена
3. **Для каждого участника группы** создает уведомление вида:
   ```
   "В вашу группу [ГРУППА] поступила задача #[НОМЕР]
   от [АВТОР]: [ТЕМА]"
   ```

**Что НЕ делает (убрано):**
- ❌ Не отслеживает изменения статусов
- ❌ Не отслеживает комментарии
- ❌ Не хранит JSON данные
- ❌ Не различает типы уведомлений
- ❌ Не связывается с integration_id
- ❌ Не имеет сложных индексов

### Пояснение по полям old_value и new_value

**Для чего были нужны old_value и new_value:**
- Отображение изменений в формате: "Статус изменен с 'Новая' на 'В работе'"
- Показ разницы приоритетов: "Приоритет изменен с 'Обычный' на 'Высокий'"

**Почему убрали в пользу current_value:**
- **Упрощение:** Достаточно показать "Статус изменен на 'В работе'"
- **Меньше данных:** Не нужно хранить историю изменений в каждом уведомлении
- **Фокус на текущем состоянии:** Пользователю важно знать актуальный статус
- **Согласованность с "Мои заявки":** Существующие уведомления не показывают old_value

### Что убрали из структуры:
- ❌ **redmine_sync_log** - избыточна, логирование через обычные логи приложения
- ❌ **redmine_project_id** - можно получить из redmine_data при необходимости
- ❌ **old_value, new_value** - заменены на current_value
- ❌ **redmine_journal_id** - не критично для уведомлений
- ❌ **read_at, dismissed_at** - достаточно булевых флагов
- ❌ **is_dismissed, dismissed_at** - удаляем уведомления вместо скрытия
- ❌ **priority, expires_at** - не нужны для MVP
- ❌ **updated_at** - уведомления неизменяемы после создания

#### 4. Полный скрипт для импорта (упрощенная версия)

```sql
-- =======================================================================
-- ПОЛНЫЙ СКРИПТ СОЗДАНИЯ ТАБЛИЦ REDMINE ИНТЕГРАЦИИ (упрощенная версия)
-- Версия: 2.0 для Flask Helpdesk (MVP)
-- Совместимость: MySQL 5.7+, MariaDB 10.2+
-- Кодировка: UTF-8 (utf8mb4_unicode_ci)
-- =======================================================================

-- Начинаем транзакцию для атомарности операций
START TRANSACTION;

-- Устанавливаем режим SQL для совместимости
SET sql_mode = 'NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION';

-- =======================================================================
-- 1. ТАБЛИЦА НАСТРОЕК ИНТЕГРАЦИИ С REDMINE
-- =======================================================================

CREATE TABLE `redmine_integration` (
  `id` INT(11) NOT NULL AUTO_INCREMENT COMMENT 'ID интеграции',
  `user_id` INT(11) NOT NULL COMMENT 'ID пользователя Flask Helpdesk',
  `redmine_url` VARCHAR(255) NOT NULL COMMENT 'URL Redmine (https://redmine.company.com)',
  `api_key` VARCHAR(40) NOT NULL COMMENT 'API ключ Redmine',
  `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT 'Включена ли интеграция (0-нет, 1-да)',
  `last_sync` TIMESTAMP NULL COMMENT 'Время последней проверки новых задач',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Дата создания',

  PRIMARY KEY (`id`),

  -- Один пользователь - одна интеграция
  CONSTRAINT `fk_redmine_integration_user`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,

  UNIQUE KEY `uk_redmine_integration_user` (`user_id`)
    COMMENT 'Один пользователь - одна интеграция',

  -- Минимальные индексы
  INDEX `idx_redmine_integration_active` (`is_active`, `last_sync`)
    COMMENT 'Активные интеграции для синхронизации'

) ENGINE=InnoDB
  AUTO_INCREMENT=1
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Простые настройки подключения к Redmine (только URL + API ключ)';

-- =======================================================================
-- 2. ТАБЛИЦА УВЕДОМЛЕНИЙ О ЗАДАЧАХ REDMINE (МАКСИМАЛЬНО упрощенная)
-- =======================================================================

CREATE TABLE `redmine_notifications` (
  `id` INT(11) NOT NULL AUTO_INCREMENT COMMENT 'ID уведомления',
  `user_id` INT(11) NOT NULL COMMENT 'ID пользователя-получателя',
  `redmine_issue_id` INT(11) NOT NULL COMMENT 'Номер задачи в Redmine (#263117)',
  `issue_subject` VARCHAR(500) NOT NULL COMMENT 'Тема задачи',
  `issue_description` TEXT NULL COMMENT 'Описание/текст задачи',
  `author_name` VARCHAR(255) NOT NULL COMMENT 'От кого (автор задачи)',
  `author_email` VARCHAR(255) NULL COMMENT 'Email автора',
  `group_name` VARCHAR(255) NOT NULL COMMENT 'Название группы исполнителей',
  `is_read` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Прочитано (0-нет, 1-да)',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Дата создания',

  PRIMARY KEY (`id`),

  -- Внешний ключ на пользователя
  CONSTRAINT `fk_redmine_notifications_user`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,

  -- Предотвращение дублирования
  UNIQUE KEY `uk_redmine_notifications_unique` (`user_id`, `redmine_issue_id`)
    COMMENT 'Один пользователь - одно уведомление на задачу',

  -- Основные индексы
  INDEX `idx_redmine_notifications_user_unread` (`user_id`, `is_read`, `created_at` DESC)
    COMMENT 'Непрочитанные уведомления пользователя',

  INDEX `idx_redmine_notifications_created` (`created_at` DESC)
    COMMENT 'Сортировка по дате'

) ENGINE=InnoDB
  AUTO_INCREMENT=1
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Уведомления о новых задачах Redmine в группах пользователей';

-- =======================================================================
-- ЗАВЕРШЕНИЕ ТРАНЗАКЦИИ
-- =======================================================================

-- Подтверждаем все изменения
COMMIT;

-- Выводим информацию о созданных таблицах
SELECT
    'redmine_integration' as table_name,
    COUNT(*) as row_count,
    'CREATED' as status
FROM redmine_integration
UNION ALL
SELECT
    'redmine_notifications' as table_name,
    COUNT(*) as row_count,
    'CREATED' as status
FROM redmine_notifications;

-- Сообщение об успешном создании
SELECT 'Упрощенные таблицы для интеграции с Redmine успешно созданы!' as message;
```

#### 5. Скрипт удаления таблиц (для отката)

```sql
-- ====================================================================
-- СКРИПТ УДАЛЕНИЯ ТАБЛИЦ ИНТЕГРАЦИИ REDMINE (упрощенная версия)
-- Используйте с осторожностью! Все данные будут потеряны.
-- ====================================================================

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `redmine_notifications`;
DROP TABLE IF EXISTS `redmine_integration`;

SET FOREIGN_KEY_CHECKS = 1;

SELECT 'Упрощенные таблицы интеграции Redmine удалены' AS status;
```

#### 6. Скрипт проверки целостности

```sql
-- ====================================================================
-- СКРИПТ ПРОВЕРКИ ЦЕЛОСТНОСТИ ТАБЛИЦ ИНТЕГРАЦИИ REDMINE
-- ====================================================================

-- Проверяем существование таблиц
SELECT
    TABLE_NAME as 'Таблица',
    ENGINE as 'Движок',
    TABLE_COLLATION as 'Кодировка',
    CREATE_TIME as 'Дата создания'
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME LIKE 'redmine_%'
ORDER BY TABLE_NAME;

-- Проверяем внешние ключи
SELECT
    CONSTRAINT_NAME as 'Ограничение',
    TABLE_NAME as 'Таблица',
    COLUMN_NAME as 'Столбец',
    REFERENCED_TABLE_NAME as 'Ссылается на таблицу',
    REFERENCED_COLUMN_NAME as 'Ссылается на столбец'
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME LIKE 'redmine_%'
    AND REFERENCED_TABLE_NAME IS NOT NULL
ORDER BY TABLE_NAME, CONSTRAINT_NAME;

-- Проверяем индексы
SELECT
    TABLE_NAME as 'Таблица',
    INDEX_NAME as 'Индекс',
    COLUMN_NAME as 'Столбец',
    NON_UNIQUE as 'Не уникальный'
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME LIKE 'redmine_%'
ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;
```

## РЕАЛИЗАЦИЯ

### 1. Модуль RedmineClient
```python
# app/services/redmine_client.py
from redminelib import Redmine
from typing import List, Dict, Optional
import logging

class RedmineClient:
    def __init__(self, url: str, api_key: str):
        self.redmine = Redmine(url, key=api_key)
        self.logger = logging.getLogger(__name__)

    def get_group_issues(self, group_id: int, updated_since: Optional[str] = None) -> List[Dict]:
        """Получить задачи, назначенные группе"""
        try:
            # Получаем участников группы
            group = self.redmine.group.get(group_id, include=['users'])
            user_ids = [user.id for user in group.users]

            # Получаем задачи для участников группы
            issues = []
            for user_id in user_ids:
                user_issues = self.redmine.issue.filter(
                    assigned_to_id=user_id,
                    updated_on=f'>={updated_since}' if updated_since else None,
                    limit=100
                )
                issues.extend(user_issues)

            return [self._serialize_issue(issue) for issue in issues]

        except Exception as e:
            self.logger.error(f"Error fetching group issues: {e}")
            return []

    def get_issue_journals(self, issue_id: int, since_journal_id: Optional[int] = None) -> List[Dict]:
        """Получить журналы изменений задачи"""
        try:
            issue = self.redmine.issue.get(issue_id, include=['journals'])
            journals = []

            for journal in issue.journals:
                if since_journal_id and journal.id <= since_journal_id:
                    continue

                journals.append({
                    'id': journal.id,
                    'user': journal.user.name if hasattr(journal, 'user') else 'Unknown',
                    'created_on': journal.created_on.isoformat(),
                    'notes': getattr(journal, 'notes', ''),
                    'details': [
                        {
                            'property': detail.property,
                            'name': detail.name,
                            'old_value': getattr(detail, 'old_value', ''),
                            'new_value': getattr(detail, 'new_value', '')
                        }
                        for detail in getattr(journal, 'details', [])
                    ]
                })

            return journals

        except Exception as e:
            self.logger.error(f"Error fetching issue journals: {e}")
            return []
```

### 2. Сервис управления группами
```python
# app/services/group_manager.py
from app.models import User, db
from typing import List, Optional
import logging

class GroupManager:
    @staticmethod
    def get_user_groups(user_id: int) -> List[int]:
        """Получить ID групп пользователя из Redmine (через связку users-groups_users)"""
        try:
            query = """
            SELECT g.id as group_id
            FROM users g
            INNER JOIN groups_users gu ON g.id = gu.group_id
            WHERE gu.user_id = %s AND g.type = 'Group'
            """

            result = db.session.execute(query, (user_id,))
            group_ids = [row[0] for row in result.fetchall()]

            logging.info(f"User {user_id} belongs to groups: {group_ids}")
            return group_ids

        except Exception as e:
            logging.error(f"Error getting user groups for user {user_id}: {e}")
            return []

    @staticmethod
    def get_group_members(group_id: int) -> List[int]:
        """Получить участников группы"""
        try:
            query = """
            SELECT gu.user_id
            FROM groups_users gu
            WHERE gu.group_id = %s
            """

            result = db.session.execute(query, (group_id,))
            user_ids = [row[0] for row in result.fetchall()]

            logging.info(f"Group {group_id} has members: {user_ids}")
            return user_ids

        except Exception as e:
            logging.error(f"Error getting group members for group {group_id}: {e}")
            return []

    @staticmethod
    def is_user_in_group(user_id: int, group_id: int) -> bool:
        """Проверить, входит ли пользователь в группу"""
        try:
            query = """
            SELECT 1
            FROM groups_users gu
            INNER JOIN users g ON g.id = gu.group_id
            WHERE gu.user_id = %s AND gu.group_id = %s AND g.type = 'Group'
            LIMIT 1
            """

            result = db.session.execute(query, (user_id, group_id))
            is_member = result.fetchone() is not None

            logging.debug(f"User {user_id} in group {group_id}: {is_member}")
            return is_member

        except Exception as e:
            logging.error(f"Error checking if user {user_id} is in group {group_id}: {e}")
            return False
```

### 3. Процессор уведомлений
```python
# app/services/redmine_notification_processor.py
from app.models import RedmineNotification, User, db
from app.services.redmine_client import RedmineClient
from app.services.group_manager import GroupManager
from typing import List, Dict
import logging

class RedmineNotificationProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process_user_notifications(self, user_id: int):
        """Обработать уведомления для пользователя"""
        try:
            user = User.query.get(user_id)
            if not user or not user.redmine_integration:
                return

            integration = user.redmine_integration
            client = RedmineClient(integration.redmine_url, integration.api_key)

            # Получаем группы пользователя
            group_ids = GroupManager.get_user_groups(user_id)

            # Обрабатываем задачи для каждой группы
            for group_id in group_ids:
                self._process_group_issues(user_id, client, group_id)

        except Exception as e:
            self.logger.error(f"Error processing notifications for user {user_id}: {e}")

    def _process_group_issues(self, user_id: int, client: RedmineClient, group_id: int):
        """Обработать задачи группы"""
        # Получаем последнюю синхронизацию
        last_sync = self._get_last_sync_time(user_id)

        # Получаем новые/обновленные задачи
        issues = client.get_group_issues(group_id, last_sync)

        for issue in issues:
            self._create_issue_notifications(user_id, issue)
            self._process_issue_changes(user_id, client, issue['id'])

    def _create_issue_notifications(self, user_id: int, issue: Dict):
        """Создать уведомления для задачи"""
        notifications = []

        # Уведомление о новой задаче
        if self._is_new_issue(user_id, issue['id']):
            notifications.append({
                'type': 'assignment',
                'title': f"Новая задача #{issue['id']}: {issue['subject']}",
                'description': f"Приоритет: {issue.get('priority', 'N/A')}, Статус: {issue.get('status', 'N/A')}"
            })

        # Создаем записи в БД
        for notif_data in notifications:
            notification = RedmineNotification(
                user_id=user_id,
                redmine_issue_id=issue['id'],
                notification_type=notif_data['type'],
                title=notif_data['title'],
                description=notif_data['description'],
                redmine_data=issue
            )
            db.session.add(notification)

        if notifications:
            db.session.commit()
```

### 4. API Endpoints

```python
# app/api/redmine_notifications.py
from flask import Blueprint, request, jsonify, current_user
from app.services.redmine_notification_processor import RedmineNotificationProcessor
from app.models import RedmineNotification, RedmineIntegration

bp = Blueprint('redmine_notifications', __name__, url_prefix='/api/redmine')

@bp.route('/notifications', methods=['GET'])
def get_notifications():
    """Получить уведомления Redmine"""
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)

    notifications = RedmineNotification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(RedmineNotification.created_at.desc()).offset(offset).limit(limit).all()

    return jsonify({
        'success': True,
        'notifications': [n.to_dict() for n in notifications],
        'total': RedmineNotification.query.filter_by(user_id=current_user.id, is_read=False).count()
    })

@bp.route('/sync', methods=['POST'])
def manual_sync():
    """Ручная синхронизация уведомлений"""
    processor = RedmineNotificationProcessor()
    processor.process_user_notifications(current_user.id)

    return jsonify({'success': True, 'message': 'Синхронизация запущена'})

@bp.route('/integration', methods=['POST'])
def setup_integration():
    """Настройка интеграции с Redmine"""
    data = request.get_json()

    # Валидация данных
    required_fields = ['redmine_url', 'api_key']
    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    # Создание/обновление интеграции
    integration = RedmineIntegration.query.filter_by(user_id=current_user.id).first()
    if not integration:
        integration = RedmineIntegration(user_id=current_user.id)

    integration.redmine_url = data['redmine_url']
    integration.api_key = data['api_key']
    integration.is_active = data.get('is_active', True)

    db.session.add(integration)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Интеграция настроена'})
```

### 5. Планировщик задач

```python
# app/tasks/redmine_sync.py
from app import create_app, db
from app.services.redmine_notification_processor import RedmineNotificationProcessor
from app.models import User, RedmineIntegration
from apscheduler.schedulers.background import BackgroundScheduler
import logging

class RedmineSyncScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.processor = RedmineNotificationProcessor()
        self.logger = logging.getLogger(__name__)

    def start(self):
        """Запустить планировщик"""
        # Синхронизация каждые 5 минут
        self.scheduler.add_job(
            func=self.sync_all_users,
            trigger='interval',
            minutes=5,
            id='redmine_sync_all'
        )

        self.scheduler.start()
        self.logger.info("Redmine sync scheduler started")

    def sync_all_users(self):
        """Синхронизировать для всех пользователей с активной интеграцией"""
        with create_app().app_context():
            active_integrations = RedmineIntegration.query.filter_by(is_active=True).all()

            for integration in active_integrations:
                try:
                    self.processor.process_user_notifications(integration.user_id)
                    self.logger.info(f"Synced notifications for user {integration.user_id}")
                except Exception as e:
                    self.logger.error(f"Error syncing user {integration.user_id}: {e}")
```

## ЛОГИКА "МОИ ЗАДАЧИ" (аналогично "МОИ ЗАЯВКИ")

### Принцип работы
Функциональность "Мои задачи" должна полностью повторять логику "Мои заявки":

1. **Источник данных:** Задачи из Redmine вместо заявок из внутренней системы
2. **Критерий фильтрации:** Задачи, назначенные на группы пользователя
3. **Типы уведомлений:** Новые задачи, изменения статуса, комментарии
4. **Места отображения:** Виджет уведомлений + страница /notifications

### Уточненная логика получения задач
```python
# app/services/redmine_notification_processor.py
class RedmineNotificationProcessor:
    def process_user_notifications(self, user_id: int):
        """Обработать уведомления для пользователя - аналогично логике 'Мои заявки'"""
        try:
            user = User.query.get(user_id)
            if not user or not user.redmine_integration:
                return

            integration = user.redmine_integration
            client = RedmineClient(integration.redmine_url, integration.api_key)

            # Получаем группы пользователя (аналогично тому, как определяются "мои" заявки)
            group_ids = GroupManager.get_user_groups(user_id)

            for group_id in group_ids:
                # Получаем задачи, назначенные на группу
                group_issues = client.get_issues_assigned_to_group(group_id)

                for issue in group_issues:
                    # Проверяем, что пользователь действительно в этой группе
                    if GroupManager.is_user_in_group(user_id, issue.assigned_to_group_id):
                        self._process_issue_for_user(user_id, issue)

        except Exception as e:
            self.logger.error(f"Error processing notifications for user {user_id}: {e}")

    def _process_issue_for_user(self, user_id: int, issue: Dict):
        """Обработать задачу для пользователя"""
        # Проверяем, что это новая задача или есть изменения
        existing_notification = RedmineNotification.query.filter_by(
            user_id=user_id,
            redmine_issue_id=issue['id']
        ).first()

        if not existing_notification:
            # Новая задача - создаем уведомление
            self._create_assignment_notification(user_id, issue)
        else:
            # Проверяем изменения в существующей задаче
            self._check_issue_changes(user_id, issue)

    def _create_assignment_notification(self, user_id: int, issue: Dict):
        """Создать уведомление о назначении новой задачи"""
        notification = RedmineNotification(
            user_id=user_id,
            redmine_issue_id=issue['id'],
            notification_type='assignment',
            title=f"Новая задача #{issue['id']}: {issue['subject']}",
            description=f"Назначена на группу. Приоритет: {issue.get('priority', 'N/A')}, Статус: {issue.get('status', 'N/A')}",
            redmine_data=issue
        )
        db.session.add(notification)
        db.session.commit()
```

### Модификация RedmineClient для групповых задач
```python
# app/services/redmine_client.py
class RedmineClient:
    def get_issues_assigned_to_group(self, group_id: int, updated_since: Optional[str] = None) -> List[Dict]:
        """Получить задачи, назначенные на группу"""
        try:
            # Получаем задачи, назначенные на группу
            issues = self.redmine.issue.filter(
                assigned_to_id=group_id,
                updated_on=f'>={updated_since}' if updated_since else None,
                status_id='open',  # Только открытые задачи
                limit=100
            )

            serialized_issues = []
            for issue in issues:
                serialized_issues.append({
                    'id': issue.id,
                    'subject': issue.subject,
                    'description': getattr(issue, 'description', ''),
                    'status': issue.status.name,
                    'priority': issue.priority.name if hasattr(issue, 'priority') else 'Normal',
                    'assigned_to_group_id': group_id,
                    'created_on': issue.created_on.isoformat(),
                    'updated_on': issue.updated_on.isoformat(),
                    'author': issue.author.name if hasattr(issue, 'author') else 'Unknown'
                })

            return serialized_issues

        except Exception as e:
            self.logger.error(f"Error fetching group issues for group {group_id}: {e}")
            return []
```

## ИНТЕГРАЦИЯ С СУЩЕСТВУЮЩИМ ВИДЖЕТОМ

### Модификация API уведомлений
```python
# Модификация app/api/notifications.py
@bp.route('/poll', methods=['GET'])
def poll_notifications():
    """Опрос уведомлений (включая Redmine 'Мои задачи')"""

    # Существующие уведомления ("Мои заявки")
    status_notifications = get_status_notifications()
    comment_notifications = get_comment_notifications()

    # Новые уведомления Redmine ("Мои задачи")
    redmine_notifications = RedmineNotification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(RedmineNotification.created_at.desc()).limit(10).all()

    # Форматирование для виджета - аналогично существующим уведомлениям
    formatted_redmine = []
    for notif in redmine_notifications:
        formatted_redmine.append({
            'id': notif.id,
            'issue_id': notif.redmine_issue_id,
            'title': notif.title,
            'description': notif.description,
            'type': notif.notification_type,
            'date_created': notif.created_at.isoformat(),
            'source': 'redmine'  # Метка источника для различения
        })

    total_count = (len(status_notifications) +
                   len(comment_notifications) +
                   len(formatted_redmine))

    return jsonify({
        'success': True,
        'total_count': total_count,
        'notifications': {
            'status_notifications': status_notifications,      # Мои заявки
            'comment_notifications': comment_notifications,    # Мои заявки
            'redmine_notifications': formatted_redmine         # Мои задачи
        }
    })
```

### Модификация виджета для отображения "Мои задачи"
```javascript
// Добавление в виджет уведомлений
processNotifications(notifications) {
    try {
        const previousCount = this.notifications.length;
        this.notifications = [];

        // Обработка существующих уведомлений ("Мои заявки")
        if (notifications.status_notifications) {
            notifications.status_notifications.forEach(n => {
                this.notifications.push({
                    id: `status_${n.id}`,
                    type: 'status-change',
                    title: `Статус заявки #${n.issue_id} изменен`,
                    description: `${n.old_status} → ${n.new_status}`,
                    time: this.formatTime(n.date_created),
                    icon: 'fas fa-exchange-alt',
                    source: 'helpdesk'
                });
            });
        }

        // Обработка уведомлений Redmine ("Мои задачи")
        if (notifications.redmine_notifications) {
            notifications.redmine_notifications.forEach(n => {
                this.notifications.push({
                    id: `redmine_${n.id}`,
                    type: 'redmine-task',
                    title: n.title,
                    description: n.description,
                    time: this.formatTime(n.date_created),
                    icon: 'fas fa-tasks',  // Иконка для задач Redmine
                    source: 'redmine'
                });
            });
        }

        this.renderNotifications();
        this.updateBadge(this.notifications.length);

    } catch (error) {
        console.error('[ModernWidget] ❌ Ошибка обработки уведомлений:', error);
    }
}
```

## ИНТЕГРАЦИЯ СО СТРАНИЦЕЙ /notifications

### Модификация шаблона страницы уведомлений
```html
<!-- templates/notifications.html -->
<div class="notifications-page">
    <div class="nav nav-tabs">
        <a class="nav-link active" href="#my-tickets" data-toggle="tab">
            <i class="fas fa-ticket-alt"></i> Мои заявки
        </a>
        <a class="nav-link" href="#my-tasks" data-toggle="tab">
            <i class="fas fa-tasks"></i> Мои задачи
        </a>
    </div>

    <div class="tab-content">
        <!-- Существующий контент "Мои заявки" -->
        <div class="tab-pane fade show active" id="my-tickets">
            {% include '_existing_notifications.html' %}
        </div>

        <!-- Новый контент "Мои задачи" -->
        <div class="tab-pane fade" id="my-tasks">
            <div class="redmine-tasks-section">
                <div class="section-header">
                    <h4>Задачи Redmine</h4>
                    <button class="btn btn-sm btn-outline-primary" onclick="syncRedmineTasks()">
                        <i class="fas fa-sync"></i> Синхронизировать
                    </button>
                </div>

                <div id="redmine-tasks-list" class="tasks-list">
                    <!-- Динамически заполняется через JS -->
                </div>
            </div>
        </div>
    </div>
</div>

<script>
// Загрузка задач Redmine
function loadRedmineTasks() {
    fetch('/api/redmine/notifications')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderRedmineTasks(data.notifications);
            }
        })
        .catch(error => console.error('Error loading Redmine tasks:', error));
}

function renderRedmineTasks(tasks) {
    const container = document.getElementById('redmine-tasks-list');

    if (tasks.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox fa-3x text-muted"></i>
                <p class="mt-3">Нет новых задач</p>
            </div>
        `;
        return;
    }

    container.innerHTML = tasks.map(task => `
        <div class="task-item notification-item" data-id="${task.id}">
            <div class="task-icon">
                <i class="fas fa-tasks text-primary"></i>
            </div>
            <div class="task-content">
                <h6 class="task-title">${task.title}</h6>
                <p class="task-description">${task.description}</p>
                <small class="task-time text-muted">${formatTime(task.date_created)}</small>
            </div>
            <div class="task-actions">
                <button class="btn btn-sm btn-outline-success" onclick="markAsRead(${task.id})">
                    <i class="fas fa-check"></i>
                </button>
            </div>
        </div>
    `).join('');
}

// Синхронизация задач
function syncRedmineTasks() {
    fetch('/api/redmine/sync', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                setTimeout(loadRedmineTasks, 2000); // Перезагружаем через 2 секунды
            }
        });
}

// Отметить как прочитанное
function markAsRead(taskId) {
    fetch(`/api/redmine/notifications/${taskId}/read`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadRedmineTasks(); // Перезагружаем список
            }
        });
}

// Загружаем задачи при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Проверяем, есть ли интеграция с Redmine
    fetch('/api/redmine/integration/status')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.enabled) {
                loadRedmineTasks();
            } else {
                // Показываем сообщение о необходимости настройки
                document.getElementById('redmine-tasks-list').innerHTML = `
                    <div class="integration-setup">
                        <p>Для получения уведомлений о задачах Redmine необходимо настроить интеграцию.</p>
                        <a href="/settings/redmine" class="btn btn-primary">Настроить интеграцию</a>
                    </div>
                `;
            }
        });
});
</script>
```

## НАСТРОЙКИ И КОНФИГУРАЦИЯ

### Страница настроек Redmine
```html
<!-- templates/redmine_settings.html -->
<div class="redmine-integration-settings">
    <div class="card">
        <div class="card-header">
            <h4><i class="fas fa-cog"></i> Интеграция с Redmine</h4>
            <p class="text-muted">Настройте подключение к системе Redmine для получения уведомлений о задачах</p>
        </div>

        <div class="card-body">
            <form id="redmine-integration-form">
                <div class="form-group">
                    <label for="redmine_url">URL Redmine:</label>
                    <input type="url" id="redmine_url" name="redmine_url" class="form-control" required
                           placeholder="https://redmine.example.com">
                    <small class="form-text text-muted">
                        Адрес вашего сервера Redmine (с протоколом http:// или https://)
                    </small>
                </div>

                <div class="form-group">
                    <label for="api_key">API ключ:</label>
                    <input type="password" id="api_key" name="api_key" class="form-control" required>
                    <small class="form-text text-muted">
                        Получите API ключ в настройках профиля Redmine (Моя учетная запись → API ключ доступа)
                    </small>
                </div>

                <div class="form-group">
                    <div class="form-check">
                        <input type="checkbox" id="is_active" name="is_active" class="form-check-input" checked>
                        <label class="form-check-label" for="is_active">
                            Активировать интеграцию с Redmine
                        </label>
                    </div>
                    <small class="form-text text-muted">
                        При активации будет запущена автоматическая синхронизация уведомлений каждые 5 минут
                    </small>
                </div>

                <div class="form-actions">
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save"></i> Сохранить настройки
                    </button>
                    <button type="button" id="test-connection" class="btn btn-outline-secondary">
                        <i class="fas fa-plug"></i> Проверить соединение
                    </button>
                    <button type="button" id="manual-sync" class="btn btn-outline-info">
                        <i class="fas fa-sync"></i> Синхронизировать сейчас
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Статистика интеграции -->
    <div class="card mt-4">
        <div class="card-header">
            <h5>Статистика интеграции</h5>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-3">
                    <div class="stat-item">
                        <div class="stat-value" id="total-tasks">-</div>
                        <div class="stat-label">Всего задач</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-item">
                        <div class="stat-value" id="unread-notifications">-</div>
                        <div class="stat-label">Непрочитанные</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-item">
                        <div class="stat-value" id="last-sync">-</div>
                        <div class="stat-label">Последняя синхронизация</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-item">
                        <div class="stat-value" id="user-groups">-</div>
                        <div class="stat-label">Ваши группы</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
document.getElementById('redmine-integration-form').addEventListener('submit', function(e) {
    e.preventDefault();

    const formData = new FormData(this);
    const data = {
        redmine_url: formData.get('redmine_url'),
        api_key: formData.get('api_key'),
        is_active: formData.get('is_active') === 'on'
    };

    fetch('/api/redmine/integration', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Настройки сохранены успешно!');
            loadStats();
        } else {
            alert('Ошибка: ' + data.error);
        }
    });
});

document.getElementById('test-connection').addEventListener('click', function() {
    const redmineUrl = document.getElementById('redmine_url').value;
    const apiKey = document.getElementById('api_key').value;

    if (!redmineUrl || !apiKey) {
        alert('Заполните URL и API ключ');
        return;
    }

    fetch('/api/redmine/test-connection', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            redmine_url: redmineUrl,
            api_key: apiKey
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Соединение успешно установлено!');
        } else {
            alert('Ошибка соединения: ' + data.error);
        }
    });
});

function loadStats() {
    fetch('/api/redmine/stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('total-tasks').textContent = data.total_tasks;
                document.getElementById('unread-notifications').textContent = data.unread_notifications;
                document.getElementById('last-sync').textContent = data.last_sync || 'Никогда';
                document.getElementById('user-groups').textContent = data.user_groups;
            }
        });
}

// Загружаем статистику при загрузке страницы
document.addEventListener('DOMContentLoaded', loadStats);
</script>
```

## ПОШАГОВЫЙ ПЛАН РЕАЛИЗАЦИИ

### ШАГ 1: Подготовка базы данных (1 день)
- [ ] Создание миграций для трех новых таблиц MySQL
- [ ] Резервное копирование существующей БД
- [ ] Применение миграций в staging окружении
- [ ] Тестирование совместимости с существующим кодом

```sql
-- Миграция 001: Создание таблицы redmine_integration
CREATE TABLE redmine_integration (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    redmine_url VARCHAR(255) NOT NULL,
    api_key VARCHAR(255) NOT NULL,
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Миграция 002: Создание таблицы redmine_notifications
CREATE TABLE redmine_notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    redmine_issue_id INT NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    redmine_data JSON,
    is_read TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_notification (user_id, redmine_issue_id, notification_type, created_at),
    INDEX idx_user_unread (user_id, is_read),
    INDEX idx_issue_id (redmine_issue_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Миграция 003: Создание таблицы redmine_sync_log
CREATE TABLE redmine_sync_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    sync_type VARCHAR(50) NOT NULL,
    issues_processed INT DEFAULT 0,
    notifications_created INT DEFAULT 0,
    errors_count INT DEFAULT 0,
    error_details TEXT,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP NULL,
    status VARCHAR(20) DEFAULT 'running',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_status (user_id, status),
    INDEX idx_started_at (started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### ШАГ 2: Модели данных (1 день)
- [ ] Создание SQLAlchemy моделей для новых таблиц
- [ ] Добавление связей с существующими моделями
- [ ] Тестирование CRUD операций

```python
# app/models/redmine_models.py
class RedmineIntegration(db.Model):
    __tablename__ = 'redmine_integration'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    redmine_url = db.Column(db.String(255), nullable=False)
    api_key = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связь с пользователем
    user = db.relationship('User', backref='redmine_integration')

class RedmineNotification(db.Model):
    __tablename__ = 'redmine_notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    redmine_issue_id = db.Column(db.Integer, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    redmine_data = db.Column(db.JSON)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связь с пользователем
    user = db.relationship('User', backref='redmine_notifications')
```

### ШАГ 3: Базовый API клиент Redmine (2 дня)
- [ ] Установка python-redmine
- [ ] Создание RedmineClient с базовыми методами
- [ ] Тестирование подключения к Redmine
- [ ] Обработка ошибок и таймаутов

### ШАГ 4: Сервис групп (1 день)
- [ ] Реализация GroupManager
- [ ] Тестирование SQL запросов для определения групп
- [ ] Проверка логики "пользователь входит в группу"

### ШАГ 5: Базовая страница настроек (2 дня)
- [ ] Создание страницы настроек интеграции
- [ ] Форма для ввода URL Redmine и API ключа
- [ ] Валидация и сохранение настроек
- [ ] Тестирование подключения

### ШАГ 6: Процессор уведомлений (3 дня)
- [ ] Создание RedmineNotificationProcessor
- [ ] Логика получения задач для групп пользователя
- [ ] Создание уведомлений в БД
- [ ] Тестирование с реальными данными Redmine

### ШАГ 7: Интеграция с виджетом (2 дня)
- [ ] Модификация API `/api/notifications/poll`
- [ ] Добавление redmine_notifications в ответ
- [ ] Обновление виджета для отображения новых уведомлений
- [ ] Тестирование отображения в виджете

### ШАГ 8: Интеграция со страницей /notifications (2 дня)
- [ ] Модификация страницы уведомлений
- [ ] Добавление вкладки "Мои задачи"
- [ ] Отображение уведомлений Redmine
- [ ] Функция "Отметить как прочитанное"

### ШАГ 9: Планировщик задач (2 дня)
- [ ] Создание фонового планировщика
- [ ] Автоматическая синхронизация каждые 5 минут
- [ ] Логирование процесса синхронизации
- [ ] Мониторинг ошибок

### ШАГ 10: Тестирование и отладка (3 дня)
- [ ] Комплексное тестирование всей функциональности
- [ ] Проверка производительности
- [ ] Тестирование граничных случаев
- [ ] Исправление найденных ошибок

### ШАГ 11: Документация и деплой (2 дня)
- [ ] Создание документации для пользователей
- [ ] Инструкция по настройке интеграции
- [ ] Деплой в production
- [ ] Мониторинг работы в production

### КОНТРОЛЬНЫЕ ТОЧКИ

**После каждого шага:**
- [ ] Проверить, что существующая функциональность не нарушена
- [ ] Запустить тесты существующих уведомлений
- [ ] Проверить работу виджета с существующими уведомлениями
- [ ] Убедиться в отсутствии ошибок в логах

**Критерии готовности:**
- [ ] Пользователи получают уведомления только о задачах своих групп
- [ ] Уведомления отображаются в виджете и на странице /notifications
- [ ] Логика повторяет существующую для "Мои заявки"
- [ ] Нет влияния на производительность системы
- [ ] Все ошибки обрабатываются корректно

## ТРЕБОВАНИЯ К БЕЗОПАСНОСТИ

1. **Хранение API ключей:** Зашифровать API ключи в БД
2. **Валидация данных:** Проверка всех входящих данных от Redmine
3. **Rate limiting:** Ограничение запросов к API Redmine
4. **Логирование:** Подробное логирование всех операций
5. **Обработка ошибок:** Graceful handling ошибок API

## МЕТРИКИ И МОНИТОРИНГ

- Количество активных интеграций
- Частота синхронизации
- Количество созданных уведомлений
- Ошибки интеграции
- Время отклика API Redmine

## КОНТРОЛЬНЫЕ ВОПРОСЫ ДЛЯ ТЕСТИРОВАНИЯ

### Проверка корректности логики групп
1. **Тест 1:** Пользователь A входит в группу G1, задача T1 назначена на группу G1
   - ✅ Пользователь A должен получить уведомление о задаче T1

2. **Тест 2:** Пользователь B НЕ входит в группу G1, задача T1 назначена на группу G1
   - ✅ Пользователь B НЕ должен получить уведомление о задаче T1

3. **Тест 3:** Пользователь C входит в группы G1 и G2, есть задачи T1 (G1) и T2 (G2)
   - ✅ Пользователь C должен получить уведомления о задачах T1 и T2

### Проверка интеграции с виджетом
4. **Тест 4:** Виджет отображает уведомления из обеих систем
   - ✅ "Мои заявки" (существующие) отображаются корректно
   - ✅ "Мои задачи" (новые Redmine) отображаются корректно
   - ✅ Общий счетчик badge суммирует оба типа

5. **Тест 5:** Функциональность виджета не нарушена
   - ✅ Звуковые уведомления работают
   - ✅ Кнопки "Очистить", "Показать все" работают
   - ✅ Анимации и стили не нарушены

### Проверка страницы /notifications
6. **Тест 6:** Вкладки работают корректно
   - ✅ Вкладка "Мои заявки" содержит существующие уведомления
   - ✅ Вкладка "Мои задачи" содержит уведомления Redmine
   - ✅ Переключение между вкладками без ошибок

### Проверка производительности
7. **Тест 7:** Система не замедляется
   - ✅ Синхронизация не блокирует UI
   - ✅ Время загрузки страниц не увеличилось
   - ✅ Нет утечек памяти при работе планировщика

### Проверка безопасности
8. **Тест 8:** API ключи защищены
   - ✅ Ключи зашифрованы в базе данных
   - ✅ Ключи не передаются в логах
   - ✅ Доступ к интеграции только для авторизованных пользователей

## КРИТЕРИИ ПРИЕМКИ

### Обязательные требования
- [ ] Пользователи получают уведомления ТОЛЬКО о задачах своих групп
- [ ] Логика полностью аналогична существующей системе "Мои заявки"
- [ ] Уведомления отображаются в виджете И на странице /notifications
- [ ] Существующая функциональность не нарушена
- [ ] Все SQL-запросы оптимизированы для MySQL
- [ ] Система работает стабильно без ошибок

### Дополнительные требования
- [ ] Пользовательский интерфейс интуитивно понятен
- [ ] Страница настроек работает корректно
- [ ] Статистика интеграции отображается
- [ ] Логирование и мониторинг функционируют
- [ ] Документация для пользователей создана

## ПЛАН ROLLBACK

В случае критических проблем:

### Немедленный откат (< 5 минут)
1. Отключить планировщик Redmine задач
2. Скрыть вкладку "Мои задачи" на странице уведомлений
3. Исключить redmine_notifications из API /notifications/poll

### Полный откат (< 30 минут)
1. Удалить новые таблицы из базы данных
2. Откатить изменения в коде API уведомлений
3. Восстановить оригинальный виджет уведомлений
4. Удалить файлы интеграции с Redmine

### Команды для экстренного отключения
```sql
-- Отключить все интеграции
UPDATE redmine_integration SET is_active = 0;

-- Удалить все уведомления Redmine
DELETE FROM redmine_notifications;
```

## ЗАКЛЮЧЕНИЕ

Данное техническое задание описывает пошаговую интеграцию системы уведомлений Flask Helpdesk с API Redmine. Решение:

✅ **Полностью повторяет логику "Мои заявки" для "Мои задач"**
✅ **Использует MySQL с правильными индексами и типами данных**
✅ **Обеспечивает безопасную пошаговую реализацию**
✅ **Сохраняет всю существующую функциональность**

Общее время реализации: **15-20 рабочих дней** с учетом тестирования и отладки.

## ФИНАЛЬНОЕ РЕЗЮМЕ: МАКСИМАЛЬНО УПРОЩЕННАЯ ИНТЕГРАЦИЯ

### Анализ скриншота и требований

**На основе предоставленного скриншота уведомления:**
```
"В Вашу группу исполнителей ERP-аналитики поступила задача #263117
Тема: Re: * просьба изменить цены контр. цены трансфер списком_MOTUS
От: andrei.sandu@tez-tour.ro"
```

## ДОРАБОТАННАЯ ЛОГИКА: МОНИТОРИНГ ИЗМЕНЕНИЙ assigned_to_id

### Ключевые изменения в подходе

**ВМЕСТО:** Мониторинг API на предмет новых задач
**ДЕЛАЕМ:** Отслеживание изменений поля `assigned_to_id` в таблице `issues` через триггеры БД

### Логика работы функциональности

#### 1. Триггер на изменение assigned_to_id
- Создается триггер `AFTER UPDATE` на таблице `issues`
- Срабатывает ТОЛЬКО при изменении поля `assigned_to_id`
- Игнорирует все остальные изменения задачи (статус, описание, комментарии и т.д.)

#### 2. Определение типа назначения
При каждом изменении `assigned_to_id`:
```sql
SELECT type FROM users WHERE id = NEW.assigned_to_id;
```
- Если `type = 'Group'` → назначение на группу
- Если `type = 'User'` → назначение на конкретного пользователя

#### 3. Создание уведомлений для группы
Если `assigned_to_id` указывает на группу:
```sql
-- Получаем всех участников группы
SELECT u.id, u.firstname, u.lastname, u.mail
FROM users u
JOIN groups_users gu ON u.id = gu.user_id
WHERE gu.group_id = NEW.assigned_to_id;

-- Создаем уведомление для каждого участника
INSERT INTO redmine_notifications (
    user_id, redmine_issue_id, issue_subject,
    issue_description, author_name, author_email,
    group_name, is_read, created_at
) VALUES (
    [USER_ID],
    NEW.id,
    NEW.subject,
    CONCAT('В вашу группу ', group_name, ' поступила задача #', NEW.id, ' от ', author_name, ': ', NEW.subject),
    [AUTHOR_NAME],
    [AUTHOR_EMAIL],
    [GROUP_NAME],
    0,
    NOW()
);
```

**Формат уведомления для группы:**
```
"В вашу группу [ГРУППА] поступила задача #[НОМЕР]
от [АВТОР]: [ТЕМА]"
```

#### 4. Создание уведомления для пользователя
Если `assigned_to_id` указывает на конкретного пользователя:
```sql
INSERT INTO redmine_notifications (
    user_id, redmine_issue_id, issue_subject,
    issue_description, author_name, author_email,
    group_name, is_read, created_at
) VALUES (
    NEW.assigned_to_id,
    NEW.id,
    NEW.subject,
    CONCAT('★ Вы назначены исполнителем по задаче #', NEW.id, ' Тема: ', NEW.subject, ' Описание: ', NEW.description),
    [AUTHOR_NAME],
    [AUTHOR_EMAIL],
    NULL, -- группа не указывается для индивидуального назначения
    0,
    NOW()
);
```

**Формат уведомления для пользователя:**
```
★ Вы назначены исполнителем по задаче #[НОМЕР] ([кликабельная ссылка])
Тема: [ТЕМА]
Описание: [ТЕКСТ ЗАДАЧИ]
```

### План реализации

#### Этап 1: Подготовка базы данных (1 день)
1. **Создание упрощенных таблиц:**
   - `redmine_integration` (7 столбцов)
   - `redmine_notifications` (10 столбцов)

2. **Создание триггера на таблице issues:**
   ```sql
   CREATE TRIGGER trg_issue_assignment_change
   AFTER UPDATE ON issues
   FOR EACH ROW
   WHEN (OLD.assigned_to_id != NEW.assigned_to_id OR
         (OLD.assigned_to_id IS NULL AND NEW.assigned_to_id IS NOT NULL))
   BEGIN
       -- Логика создания уведомлений
   END;
   ```

#### Этап 2: Логика триггера (2 дня)
1. **Определение типа назначения** (группа/пользователь)
2. **Получение данных об авторе задачи**
3. **Формирование текста уведомления** в зависимости от типа
4. **Создание записей в redmine_notifications**

#### Этап 3: Интеграция с Flask (2 дня)
1. **Модели данных** для работы с redmine_notifications
2. **API endpoint** для получения уведомлений виджетом
3. **Модификация существующего API** `/api/notifications/poll`

#### Этап 4: Доработка виджета (1 день)
1. **Поддержка нового типа** уведомлений `redmine-assignment`
2. **Специальная иконка** для уведомлений Redmine
3. **Кликабельные ссылки** на задачи Redmine

#### Этап 5: Тестирование (2 дня)
1. **Тестирование триггера** на изменения assigned_to_id
2. **Проверка корректности** определения типа назначения
3. **Валидация формата** уведомлений

### Ключевые преимущества нового подхода

1. **Мгновенная реакция:** Триггер срабатывает сразу при изменении назначения
2. **Точность:** Уведомления создаются ТОЛЬКО при смене исполнителя
3. **Производительность:** Нет необходимости в периодических запросах к API
4. **Надежность:** Работает на уровне базы данных, не зависит от внешних сервисов
5. **Простота:** Минимум кода, максимум эффективности

### Структура триггера (псевдокод)

```sql
DELIMITER $$
CREATE TRIGGER trg_redmine_assignment_notification
AFTER UPDATE ON issues
FOR EACH ROW
BEGIN
    -- Проверяем изменение assigned_to_id
    IF OLD.assigned_to_id != NEW.assigned_to_id OR
       (OLD.assigned_to_id IS NULL AND NEW.assigned_to_id IS NOT NULL) THEN

        -- Получаем тип назначения
        SELECT type INTO @assignment_type
        FROM users
        WHERE id = NEW.assigned_to_id;

        -- Получаем данные автора
        SELECT CONCAT(firstname, ' ', lastname), mail
        INTO @author_name, @author_email
        FROM users
        WHERE id = NEW.author_id;

        IF @assignment_type = 'Group' THEN
            -- Создаем уведомления для всех участников группы
            CALL create_group_notifications(NEW.id, NEW.assigned_to_id, NEW.subject, @author_name, @author_email);
        ELSE
            -- Создаем индивидуальное уведомление
            CALL create_user_notification(NEW.assigned_to_id, NEW.id, NEW.subject, NEW.description, @author_name, @author_email);
        END IF;

    END IF;
END$$
DELIMITER ;
```

**Общее время реализации: 8 дней** (значительно меньше благодаря упрощению архитектуры)

### ✅ ОТВЕТЫ НА ВОПРОСЫ

1. **✅ Доступ к БД Redmine:** Есть, триггеры можно создавать самостоятельно
2. **✅ Формат ссылок:** `https://helpdesk.teztour.com/issues/[ID]` (например: https://helpdesk.teztour.com/issues/263116)
3. **✅ Снятие назначения:** При `assigned_to_id = NULL` уведомления НЕ создаются

## КОНКРЕТНАЯ РЕАЛИЗАЦИЯ

### 1. SQL-скрипт создания триггера

```sql
-- Создание триггера для отслеживания изменений assigned_to_id
DELIMITER $$

CREATE TRIGGER trg_redmine_assignment_notification
AFTER UPDATE ON issues
FOR EACH ROW
BEGIN
    DECLARE assignment_type VARCHAR(10);
    DECLARE author_name VARCHAR(255);
    DECLARE author_email VARCHAR(255);
    DECLARE group_name VARCHAR(255);
    DECLARE issue_url VARCHAR(500);

    -- Проверяем изменение assigned_to_id (только назначение, не снятие)
    IF (OLD.assigned_to_id != NEW.assigned_to_id OR
        (OLD.assigned_to_id IS NULL AND NEW.assigned_to_id IS NOT NULL))
       AND NEW.assigned_to_id IS NOT NULL THEN

        -- Получаем тип назначения (Group или User)
        SELECT type INTO assignment_type
        FROM users
        WHERE id = NEW.assigned_to_id;

        -- Получаем данные автора задачи
        SELECT CONCAT(IFNULL(firstname, ''), ' ', IFNULL(lastname, '')),
               IFNULL(mail, '')
        INTO author_name, author_email
        FROM users
        WHERE id = NEW.author_id;

        -- Формируем URL задачи
        SET issue_url = CONCAT('https://helpdesk.teztour.com/issues/', NEW.id);

        IF assignment_type = 'Group' THEN
            -- Получаем название группы
            SELECT IFNULL(lastname, CONCAT('Group_', NEW.assigned_to_id))
            INTO group_name
            FROM users
            WHERE id = NEW.assigned_to_id;

            -- Создаем уведомления для всех участников группы
            INSERT INTO redmine_notifications (
                user_id, redmine_issue_id, issue_subject,
                issue_description, author_name, author_email,
                group_name, is_read, created_at
            )
            SELECT
                u.id,
                NEW.id,
                NEW.subject,
                CONCAT('В вашу группу ', group_name, ' поступила задача #', NEW.id, ' от ', author_name, ': ', NEW.subject),
                author_name,
                author_email,
                group_name,
                0,
                NOW()
            FROM users u
            JOIN groups_users gu ON u.id = gu.user_id
            WHERE gu.group_id = NEW.assigned_to_id
              AND u.type = 'User'  -- только реальные пользователи
              AND u.status = 1;    -- только активные пользователи

        ELSEIF assignment_type = 'User' THEN
            -- Создаем индивидуальное уведомление
            INSERT INTO redmine_notifications (
                user_id, redmine_issue_id, issue_subject,
                issue_description, author_name, author_email,
                group_name, is_read, created_at
            ) VALUES (
                NEW.assigned_to_id,
                NEW.id,
                NEW.subject,
                CONCAT('★ Вы назначены исполнителем по задаче #', NEW.id, ' (', issue_url, ')\nТема: ', NEW.subject, '\nОписание: ', IFNULL(LEFT(NEW.description, 200), 'Без описания')),
                author_name,
                author_email,
                NULL, -- группа не указывается для индивидуального назначения
                0,
                NOW()
            );
        END IF;

    END IF;
END$$

DELIMITER ;
```

### 2. Модификация виджета уведомлений

**Добавление поддержки Redmine-уведомлений в API `/api/notifications/poll`:**

```python
# В файле routes/api.py или аналогичном
@app.route('/api/notifications/poll')
@login_required
def poll_notifications():
    try:
        # Существующие уведомления
        status_notifications = get_status_notifications(current_user.id)
        comment_notifications = get_comment_notifications(current_user.id)

        # НОВОЕ: Redmine уведомления
        redmine_notifications = get_redmine_notifications(current_user.id)

        total_count = (
            len(status_notifications) +
            len(comment_notifications) +
            len(redmine_notifications)
        )

        return jsonify({
            'success': True,
            'total_count': total_count,
            'notifications': {
                'status_notifications': status_notifications,
                'comment_notifications': comment_notifications,
                'redmine_notifications': redmine_notifications  # НОВОЕ
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def get_redmine_notifications(user_id):
    """Получение уведомлений Redmine для пользователя"""
    try:
        query = """
        SELECT id, redmine_issue_id, issue_subject, issue_description,
               author_name, author_email, group_name, created_at
        FROM redmine_notifications
        WHERE user_id = %s AND is_read = 0
        ORDER BY created_at DESC
        LIMIT 20
        """

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(query, (user_id,))
        notifications = cursor.fetchall()
        cursor.close()

        return notifications
    except Exception as e:
        print(f"Ошибка получения Redmine уведомлений: {e}")
        return []
```

### 3. Модификация JavaScript виджета

**Добавление в `processNotifications()` функцию:**

```javascript
// В файле _modern_notifications_widget.html
processNotifications(notifications) {
    try {
        const previousCount = this.notifications.length;
        this.notifications = [];

        // Существующие уведомления
        if (notifications.status_notifications) {
            notifications.status_notifications.forEach(n => {
                this.notifications.push({
                    id: `status_${n.id}`,
                    type: 'status-change',
                    title: `Статус заявки #${n.issue_id} изменен`,
                    description: `${n.old_status} → ${n.new_status}`,
                    time: this.formatTime(n.date_created),
                    icon: 'fas fa-exchange-alt'
                });
            });
        }

        if (notifications.comment_notifications) {
            notifications.comment_notifications.forEach(n => {
                this.notifications.push({
                    id: `comment_${n.id}`,
                    type: 'comment-added',
                    title: `Новый комментарий к заявке #${n.issue_id}`,
                    description: n.notes.length > 50 ? n.notes.substring(0, 50) + '...' : n.notes,
                    time: this.formatTime(n.date_created),
                    icon: 'fas fa-comment'
                });
            });
        }

        // НОВОЕ: Redmine уведомления
        if (notifications.redmine_notifications) {
            notifications.redmine_notifications.forEach(n => {
                const isGroupNotification = n.group_name !== null;

                this.notifications.push({
                    id: `redmine_${n.id}`,
                    type: 'redmine-assignment',
                    title: isGroupNotification
                        ? `Задача #${n.redmine_issue_id} для группы ${n.group_name}`
                        : `★ Вы назначены исполнителем #${n.redmine_issue_id}`,
                    description: n.issue_description.length > 100
                        ? n.issue_description.substring(0, 100) + '...'
                        : n.issue_description,
                    time: this.formatTime(n.created_at),
                    icon: 'fas fa-tasks',
                    url: `https://helpdesk.teztour.com/issues/${n.redmine_issue_id}` // Кликабельная ссылка
                });
            });
        }

        // Остальная логика обработки...
        this.renderNotifications();
        this.updateBadge(this.notifications.length);

    } catch (error) {
        console.error('[ModernWidget] ❌ Ошибка обработки уведомлений:', error);
    }
}
```

### 4. Стили для Redmine уведомлений

**Добавление в CSS:**

```css
/* Стили для Redmine уведомлений */
.notification-item.redmine-assignment {
    border-left: 4px solid #f59e0b; /* Оранжевый цвет для Redmine */
}

.notification-icon.redmine-assignment {
    background: linear-gradient(135deg, #f59e0b, #d97706);
    color: white;
}

/* Кликабельная ссылка в уведомлении */
.notification-item[data-url] {
    cursor: pointer;
}

.notification-item[data-url]:hover {
    background: rgba(245, 158, 11, 0.1);
}
```

### 5. Обработка кликов по уведомлениям

**Добавление в JavaScript:**

```javascript
// Обработка кликов по уведомлениям с URL
document.addEventListener('click', (e) => {
    const notificationItem = e.target.closest('.notification-item[data-url]');
    if (notificationItem) {
        const url = notificationItem.getAttribute('data-url');
        if (url) {
            window.open(url, '_blank'); // Открываем в новой вкладке

            // Помечаем как прочитанное
            const notificationId = notificationItem.getAttribute('data-id');
            if (notificationId.startsWith('redmine_')) {
                markRedmineNotificationAsRead(notificationId.replace('redmine_', ''));
            }
        }
    }
});

async function markRedmineNotificationAsRead(notificationId) {
    try {
        await fetch('/api/notifications/redmine/mark-read', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name=csrf-token]')?.content || ''
            },
            body: JSON.stringify({ notification_id: notificationId })
        });
    } catch (error) {
        console.error('Ошибка отметки Redmine уведомления как прочитанного:', error);
    }
}
```

### 6. API для отметки прочитанным

```python
@app.route('/api/notifications/redmine/mark-read', methods=['POST'])
@login_required
def mark_redmine_notification_read():
    try:
        data = request.get_json()
        notification_id = data.get('notification_id')

        cursor = mysql.connection.cursor()
        cursor.execute(
            "UPDATE redmine_notifications SET is_read = 1 WHERE id = %s AND user_id = %s",
            (notification_id, current_user.id)
        )
        mysql.connection.commit()
        cursor.close()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
```

## ИТОГОВАЯ АРХИТЕКТУРА

1. **Триггер в БД Redmine** → Создает записи в `redmine_notifications`
2. **Flask API** → Читает уведомления и отдает виджету
3. **JavaScript виджет** → Отображает с кликабельными ссылками
4. **Пользователь кликает** → Открывается Redmine + уведомление помечается прочитанным

**Время реализации: 6-8 дней** 🚀

### ✅ ОТВЕТЫ НА ВОПРОСЫ

1. **✅ Доступ к БД Redmine:** Есть, триггеры можно создавать самостоятельно
2. **✅ Формат ссылок:** `https://helpdesk.teztour.com/issues/[ID]` (например: https://helpdesk.teztour.com/issues/263116)
3. **✅ Снятие назначения:** При `assigned_to_id = NULL` уведомления НЕ создаются

## КОНКРЕТНАЯ РЕАЛИЗАЦИЯ

### 1. SQL-скрипт создания триггера

```sql
-- Создание триггера для отслеживания изменений assigned_to_id
DELIMITER $$

CREATE TRIGGER trg_redmine_assignment_notification
AFTER UPDATE ON issues
FOR EACH ROW
BEGIN
    DECLARE assignment_type VARCHAR(10);
    DECLARE author_name VARCHAR(255);
    DECLARE author_email VARCHAR(255);
    DECLARE group_name VARCHAR(255);
    DECLARE issue_url VARCHAR(500);

    -- Проверяем изменение assigned_to_id (только назначение, не снятие)
    IF (OLD.assigned_to_id != NEW.assigned_to_id OR
        (OLD.assigned_to_id IS NULL AND NEW.assigned_to_id IS NOT NULL))
       AND NEW.assigned_to_id IS NOT NULL THEN

        -- Получаем тип назначения (Group или User)
        SELECT type INTO assignment_type
        FROM users
        WHERE id = NEW.assigned_to_id;

        -- Получаем данные автора задачи
        SELECT CONCAT(IFNULL(firstname, ''), ' ', IFNULL(lastname, '')),
               IFNULL(mail, '')
        INTO author_name, author_email
        FROM users
        WHERE id = NEW.author_id;

        -- Формируем URL задачи
        SET issue_url = CONCAT('https://helpdesk.teztour.com/issues/', NEW.id);

        IF assignment_type = 'Group' THEN
            -- Получаем название группы
            SELECT IFNULL(lastname, CONCAT('Group_', NEW.assigned_to_id))
            INTO group_name
            FROM users
            WHERE id = NEW.assigned_to_id;

            -- Создаем уведомления для всех участников группы
            INSERT INTO redmine_notifications (
                user_id, redmine_issue_id, issue_subject,
                issue_description, author_name, author_email,
                group_name, is_read, created_at
            )
            SELECT
                u.id,
                NEW.id,
                NEW.subject,
                CONCAT('В вашу группу ', group_name, ' поступила задача #', NEW.id, ' от ', author_name, ': ', NEW.subject),
                author_name,
                author_email,
                group_name,
                0,
                NOW()
            FROM users u
            JOIN groups_users gu ON u.id = gu.user_id
            WHERE gu.group_id = NEW.assigned_to_id
              AND u.type = 'User'  -- только реальные пользователи
              AND u.status = 1;    -- только активные пользователи

        ELSEIF assignment_type = 'User' THEN
            -- Создаем индивидуальное уведомление
            INSERT INTO redmine_notifications (
                user_id, redmine_issue_id, issue_subject,
                issue_description, author_name, author_email,
                group_name, is_read, created_at
            ) VALUES (
                NEW.assigned_to_id,
                NEW.id,
                NEW.subject,
                CONCAT('★ Вы назначены исполнителем по задаче #', NEW.id, ' (', issue_url, ')\nТема: ', NEW.subject, '\nОписание: ', IFNULL(LEFT(NEW.description, 200), 'Без описания')),
                author_name,
                author_email,
                NULL, -- группа не указывается для индивидуального назначения
                0,
                NOW()
            );
        END IF;

    END IF;
END$$

DELIMITER ;
```

### 2. Модификация виджета уведомлений

**Добавление поддержки Redmine-уведомлений в API `/api/notifications/poll`:**

```python
# В файле routes/api.py или аналогичном
@app.route('/api/notifications/poll')
@login_required
def poll_notifications():
    try:
        # Существующие уведомления
        status_notifications = get_status_notifications(current_user.id)
        comment_notifications = get_comment_notifications(current_user.id)

        # НОВОЕ: Redmine уведомления
        redmine_notifications = get_redmine_notifications(current_user.id)

        total_count = (
            len(status_notifications) +
            len(comment_notifications) +
            len(redmine_notifications)
        )

        return jsonify({
            'success': True,
            'total_count': total_count,
            'notifications': {
                'status_notifications': status_notifications,
                'comment_notifications': comment_notifications,
                'redmine_notifications': redmine_notifications  # НОВОЕ
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def get_redmine_notifications(user_id):
    """Получение уведомлений Redmine для пользователя"""
    try:
        query = """
        SELECT id, redmine_issue_id, issue_subject, issue_description,
               author_name, author_email, group_name, created_at
        FROM redmine_notifications
        WHERE user_id = %s AND is_read = 0
        ORDER BY created_at DESC
        LIMIT 20
        """

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(query, (user_id,))
        notifications = cursor.fetchall()
        cursor.close()

        return notifications
    except Exception as e:
        print(f"Ошибка получения Redmine уведомлений: {e}")
        return []
```

### 3. Модификация JavaScript виджета

**Добавление в `processNotifications()` функцию:**

```javascript
// В файле _modern_notifications_widget.html
processNotifications(notifications) {
    try {
        const previousCount = this.notifications.length;
        this.notifications = [];

        // Существующие уведомления
        if (notifications.status_notifications) {
            notifications.status_notifications.forEach(n => {
                this.notifications.push({
                    id: `status_${n.id}`,
                    type: 'status-change',
                    title: `Статус заявки #${n.issue_id} изменен`,
                    description: `${n.old_status} → ${n.new_status}`,
                    time: this.formatTime(n.date_created),
                    icon: 'fas fa-exchange-alt'
                });
            });
        }

        if (notifications.comment_notifications) {
            notifications.comment_notifications.forEach(n => {
                this.notifications.push({
                    id: `comment_${n.id}`,
                    type: 'comment-added',
                    title: `Новый комментарий к заявке #${n.issue_id}`,
                    description: n.notes.length > 50 ? n.notes.substring(0, 50) + '...' : n.notes,
                    time: this.formatTime(n.date_created),
                    icon: 'fas fa-comment'
                });
            });
        }

        // НОВОЕ: Redmine уведомления
        if (notifications.redmine_notifications) {
            notifications.redmine_notifications.forEach(n => {
                const isGroupNotification = n.group_name !== null;

                this.notifications.push({
                    id: `redmine_${n.id}`,
                    type: 'redmine-assignment',
                    title: isGroupNotification
                        ? `Задача #${n.redmine_issue_id} для группы ${n.group_name}`
                        : `★ Вы назначены исполнителем #${n.redmine_issue_id}`,
                    description: n.issue_description.length > 100
                        ? n.issue_description.substring(0, 100) + '...'
                        : n.issue_description,
                    time: this.formatTime(n.created_at),
                    icon: 'fas fa-tasks',
                    url: `https://helpdesk.teztour.com/issues/${n.redmine_issue_id}` // Кликабельная ссылка
                });
            });
        }

        // Остальная логика обработки...
        this.renderNotifications();
        this.updateBadge(this.notifications.length);

    } catch (error) {
        console.error('[ModernWidget] ❌ Ошибка обработки уведомлений:', error);
    }
}
```

### 4. Стили для Redmine уведомлений

**Добавление в CSS:**

```css
/* Стили для Redmine уведомлений */
.notification-item.redmine-assignment {
    border-left: 4px solid #f59e0b; /* Оранжевый цвет для Redmine */
}

.notification-icon.redmine-assignment {
    background: linear-gradient(135deg, #f59e0b, #d97706);
    color: white;
}

/* Кликабельная ссылка в уведомлении */
.notification-item[data-url] {
    cursor: pointer;
}

.notification-item[data-url]:hover {
    background: rgba(245, 158, 11, 0.1);
}
```

### 5. Обработка кликов по уведомлениям

**Добавление в JavaScript:**

```javascript
// Обработка кликов по уведомлениям с URL
document.addEventListener('click', (e) => {
    const notificationItem = e.target.closest('.notification-item[data-url]');
    if (notificationItem) {
        const url = notificationItem.getAttribute('data-url');
        if (url) {
            window.open(url, '_blank'); // Открываем в новой вкладке

            // Помечаем как прочитанное
            const notificationId = notificationItem.getAttribute('data-id');
            if (notificationId.startsWith('redmine_')) {
                markRedmineNotificationAsRead(notificationId.replace('redmine_', ''));
            }
        }
    }
});

async function markRedmineNotificationAsRead(notificationId) {
    try {
        await fetch('/api/notifications/redmine/mark-read', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name=csrf-token]')?.content || ''
            },
            body: JSON.stringify({ notification_id: notificationId })
        });
    } catch (error) {
        console.error('Ошибка отметки Redmine уведомления как прочитанного:', error);
    }
}
```

### 6. API для отметки прочитанным

```python
@app.route('/api/notifications/redmine/mark-read', methods=['POST'])
@login_required
def mark_redmine_notification_read():
    try:
        data = request.get_json()
        notification_id = data.get('notification_id')

        cursor = mysql.connection.cursor()
        cursor.execute(
            "UPDATE redmine_notifications SET is_read = 1 WHERE id = %s AND user_id = %s",
            (notification_id, current_user.id)
        )
        mysql.connection.commit()
        cursor.close()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
```

## ИТОГОВАЯ АРХИТЕКТУРА

1. **Триггер в БД Redmine** → Создает записи в `redmine_notifications`
2. **Flask API** → Читает уведомления и отдает виджету
3. **JavaScript виджет** → Отображает с кликабельными ссылками
4. **Пользователь кликает** → Открывается Redmine + уведомление помечается прочитанным

**Время реализации: 6-8 дней** 🚀

## АНАЛИЗ ИЗБЫТОЧНОСТИ: УПРОЩЕНИЕ ДО ОДНОЙ ТАБЛИЦЫ

### ❌ Проблема с таблицей `redmine_integration`

При триггерном подходе таблица `redmine_integration` становится **полностью избыточной**:

1. **Нет API-интеграции** → не нужны `redmine_url`, `api_key`
2. **Нет настроек пользователя** → не нужны `is_active`, `last_sync`
3. **Прямая работа с БД** → не нужны связи между системами
4. **Автоматические триггеры** → не нужно отслеживание статуса подключения

### ✅ ФИНАЛЬНАЯ УПРОЩЕННАЯ СТРУКТУРА

**Нужна только ОДНА таблица: `u_redmine_notifications`**

```sql
-- ЕДИНСТВЕННАЯ ТАБЛИЦА для всей функциональности
CREATE TABLE u_redmine_notifications (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Уникальный идентификатор уведомления',
    user_id INT NOT NULL COMMENT 'ID пользователя из таблицы users Redmine',
    redmine_issue_id INT NOT NULL COMMENT 'ID задачи из таблицы issues Redmine',
    issue_subject VARCHAR(255) NOT NULL COMMENT 'Тема задачи',
    issue_description TEXT COMMENT 'Описание уведомления (готовый текст для показа)',
    author_name VARCHAR(255) COMMENT 'Имя автора задачи',
    author_email VARCHAR(255) COMMENT 'Email автора задачи',
    group_name VARCHAR(255) COMMENT 'Название группы (NULL для индивидуальных назначений)',
    is_read BOOLEAN DEFAULT FALSE COMMENT 'Прочитано ли уведомление',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Время создания уведомления',

    -- Индексы для производительности
    INDEX idx_user_unread (user_id, is_read),
    INDEX idx_issue (redmine_issue_id),
    INDEX idx_created (created_at),

    -- Уникальный ключ против дублирования
    UNIQUE KEY uk_user_issue (user_id, redmine_issue_id, created_at),

    -- Внешний ключ на пользователя Redmine
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Уведомления о назначениях задач Redmine';
```

### 🎯 Преимущества упрощения

1. **Минимализм:** Всего 10 столбцов вместо 17
2. **Простота:** Одна таблица вместо двух
3. **Производительность:** Меньше JOIN'ов в запросах
4. **Надежность:** Меньше точек отказа
5. **Скорость разработки:** 4-5 дней вместо 6-8

### 📝 Обновленная структура триггера

```sql
-- Упрощенный триггер работает напрямую с одной таблицей
DELIMITER $$

CREATE TRIGGER trg_redmine_assignment_notification
AFTER UPDATE ON issues
FOR EACH ROW
BEGIN
    DECLARE assignment_type VARCHAR(10);
    DECLARE author_name VARCHAR(255);
    DECLARE author_email VARCHAR(255);
    DECLARE group_name VARCHAR(255);

    -- Проверяем изменение assigned_to_id (только назначение, не снятие)
    IF (OLD.assigned_to_id != NEW.assigned_to_id OR
        (OLD.assigned_to_id IS NULL AND NEW.assigned_to_id IS NOT NULL))
       AND NEW.assigned_to_id IS NOT NULL THEN

        -- Получаем тип назначения
        SELECT type INTO assignment_type FROM users WHERE id = NEW.assigned_to_id;

        -- Получаем данные автора
        SELECT CONCAT(IFNULL(firstname, ''), ' ', IFNULL(lastname, '')),
               IFNULL(mail, '')
        INTO author_name, author_email
        FROM users WHERE id = NEW.author_id;

        IF assignment_type = 'Group' THEN
            -- Получаем название группы
            SELECT IFNULL(lastname, CONCAT('Group_', NEW.assigned_to_id))
            INTO group_name FROM users WHERE id = NEW.assigned_to_id;

            -- Создаем уведомления для всех участников группы
            INSERT INTO u_redmine_notifications (
                user_id, redmine_issue_id, issue_subject,
                issue_description, author_name, author_email,
                group_name, is_read, created_at
            )
            SELECT
                u.id, NEW.id, NEW.subject,
                CONCAT('В вашу группу ', group_name, ' поступила задача #', NEW.id, ' от ', author_name, ': ', NEW.subject),
                author_name, author_email, group_name, 0, NOW()
            FROM users u
            JOIN groups_users gu ON u.id = gu.user_id
            WHERE gu.group_id = NEW.assigned_to_id AND u.type = 'User' AND u.status = 1;

        ELSEIF assignment_type = 'User' THEN
            -- Создаем индивидуальное уведомление
            INSERT INTO u_redmine_notifications (
                user_id, redmine_issue_id, issue_subject,
                issue_description, author_name, author_email,
                group_name, is_read, created_at
            ) VALUES (
                NEW.assigned_to_id, NEW.id, NEW.subject,
                CONCAT('★ Вы назначены исполнителем по задаче #', NEW.id, ' (https://helpdesk.teztour.com/issues/', NEW.id, ')\nТема: ', NEW.subject, '\nОписание: ', IFNULL(LEFT(NEW.description, 200), 'Без описания')),
                author_name, author_email, NULL, 0, NOW()
            );
        END IF;

    END IF;
END$$

DELIMITER ;
```

### ⚡ Обновленный план реализации (4-5 дней)

**День 1:** Создание единственной таблицы + триггер
**День 2:** Модификация Flask API для работы с одной таблицей
**День 3:** Доработка виджета
**День 4:** Тестирование
**День 5:** Финальная отладка (при необходимости)

### 🗃️ Упрощенный Python код

```python
def get_redmine_notifications(user_id):
    """Получение уведомлений Redmine - теперь из одной таблицы"""
    try:
        query = """
        SELECT id, redmine_issue_id, issue_subject, issue_description,
               author_name, author_email, group_name, created_at
        FROM u_redmine_notifications
        WHERE user_id = %s AND is_read = 0
        ORDER BY created_at DESC
        LIMIT 20
        """

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(query, (user_id,))
        notifications = cursor.fetchall()
        cursor.close()

        return notifications
    except Exception as e:
        print(f"Ошибка получения Redmine уведомлений: {e}")
        return []

@app.route('/api/notifications/redmine/mark-read', methods=['POST'])
@login_required
def mark_redmine_notification_read():
    """Отметка уведомления как прочитанного - упрощенная версия"""
    try:
        data = request.get_json()
        notification_id = data.get('notification_id')

        cursor = mysql.connection.cursor()
        cursor.execute(
            "UPDATE u_redmine_notifications SET is_read = 1 WHERE id = %s AND user_id = %s",
            (notification_id, current_user.id)
        )
        mysql.connection.commit()
        cursor.close()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
```

## ИТОГОВЫЕ ХАРАКТЕРИСТИКИ

- **1 таблица** вместо 2
- **10 столбцов** вместо 17
- **4 индекса** вместо 8+
- **Время реализации: 4-5 дней** вместо 6-8
- **Простота поддержки:** Минимальная архитектура

**Вы правы - это максимально упрощенное и эффективное решение!** 🎯

## ПОЛНЫЙ SQL-КОД ДЛЯ СОЗДАНИЯ ОБЪЕКТОВ

### 1. Создание таблицы u_redmine_notifications

```sql
-- Создание таблицы для уведомлений Redmine
CREATE TABLE u_redmine_notifications (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Уникальный идентификатор уведомления',
    user_id INT NOT NULL COMMENT 'ID пользователя из таблицы users Redmine',
    redmine_issue_id INT NOT NULL COMMENT 'ID задачи из таблицы issues Redmine',
    issue_subject VARCHAR(255) NOT NULL COMMENT 'Тема задачи',
    issue_description TEXT COMMENT 'Описание уведомления (готовый текст для показа)',
    author_name VARCHAR(255) COMMENT 'Имя автора задачи',
    author_email VARCHAR(255) COMMENT 'Email автора задачи',
    group_name VARCHAR(255) COMMENT 'Название группы (NULL для индивидуальных назначений)',
    is_read BOOLEAN DEFAULT FALSE COMMENT 'Прочитано ли уведомление',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Время создания уведомления',

    -- Индексы для производительности
    INDEX idx_user_unread (user_id, is_read),
    INDEX idx_issue (redmine_issue_id),
    INDEX idx_created (created_at),

    -- Уникальный ключ против дублирования
    UNIQUE KEY uk_user_issue (user_id, redmine_issue_id, created_at),

    -- Внешний ключ на пользователя Redmine
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Уведомления о назначениях задач Redmine';
```

### 2. Создание триггера

```sql
-- Создание триггера для отслеживания изменений assigned_to_id
DELIMITER $$

CREATE TRIGGER trg_redmine_assignment_notification
AFTER UPDATE ON issues
FOR EACH ROW
BEGIN
    DECLARE assignment_type VARCHAR(10);
    DECLARE author_name VARCHAR(255);
    DECLARE author_email VARCHAR(255);
    DECLARE group_name VARCHAR(255);

    -- Проверяем изменение assigned_to_id (только назначение, не снятие)
    IF (OLD.assigned_to_id != NEW.assigned_to_id OR
        (OLD.assigned_to_id IS NULL AND NEW.assigned_to_id IS NOT NULL))
       AND NEW.assigned_to_id IS NOT NULL THEN

        -- Получаем тип назначения
        SELECT type INTO assignment_type FROM users WHERE id = NEW.assigned_to_id;

        -- Получаем данные автора
        SELECT CONCAT(IFNULL(firstname, ''), ' ', IFNULL(lastname, '')),
               IFNULL(mail, '')
        INTO author_name, author_email
        FROM users WHERE id = NEW.author_id;

        IF assignment_type = 'Group' THEN
            -- Получаем название группы
            SELECT IFNULL(lastname, CONCAT('Group_', NEW.assigned_to_id))
            INTO group_name FROM users WHERE id = NEW.assigned_to_id;

            -- Создаем уведомления для всех участников группы
            INSERT INTO u_redmine_notifications (
                user_id, redmine_issue_id, issue_subject,
                issue_description, author_name, author_email,
                group_name, is_read, created_at
            )
            SELECT
                u.id, NEW.id, NEW.subject,
                CONCAT('В вашу группу ', group_name, ' поступила задача #', NEW.id, ' от ', author_name, ': ', NEW.subject),
                author_name, author_email, group_name, 0, NOW()
            FROM users u
            JOIN groups_users gu ON u.id = gu.user_id
            WHERE gu.group_id = NEW.assigned_to_id AND u.type = 'User' AND u.status = 1;

        ELSEIF assignment_type = 'User' THEN
            -- Создаем индивидуальное уведомление
            INSERT INTO u_redmine_notifications (
                user_id, redmine_issue_id, issue_subject,
                issue_description, author_name, author_email,
                group_name, is_read, created_at
            ) VALUES (
                NEW.assigned_to_id, NEW.id, NEW.subject,
                CONCAT('★ Вы назначены исполнителем по задаче #', NEW.id, ' (https://helpdesk.teztour.com/issues/', NEW.id, ')\nТема: ', NEW.subject, '\nОписание: ', IFNULL(LEFT(NEW.description, 200), 'Без описания')),
                author_name, author_email, NULL, 0, NOW()
            );
        END IF;

    END IF;
END$$

DELIMITER ;
```

### 3. Python код для работы с таблицей

```python
def get_redmine_notifications(user_id):
    """Получение уведомлений Redmine"""
    try:
        query = """
        SELECT id, redmine_issue_id, issue_subject, issue_description,
               author_name, author_email, group_name, created_at
        FROM u_redmine_notifications
        WHERE user_id = %s AND is_read = 0
        ORDER BY created_at DESC
        LIMIT 20
        """

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(query, (user_id,))
        notifications = cursor.fetchall()
        cursor.close()

        return notifications
    except Exception as e:
        print(f"Ошибка получения Redmine уведомлений: {e}")
        return []

@app.route('/api/notifications/redmine/mark-read', methods=['POST'])
@login_required
def mark_redmine_notification_read():
    """Отметка уведомления как прочитанного"""
    try:
        data = request.get_json()
        notification_id = data.get('notification_id')

        cursor = mysql.connection.cursor()
        cursor.execute(
            "UPDATE u_redmine_notifications SET is_read = 1 WHERE id = %s AND user_id = %s",
            (notification_id, current_user.id)
        )
        mysql.connection.commit()
        cursor.close()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/notifications/redmine/clear', methods=['POST'])
@login_required
def clear_redmine_notifications():
    """Очистка всех Redmine уведомлений пользователя"""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute(
            "UPDATE u_redmine_notifications SET is_read = 1 WHERE user_id = %s",
            (current_user.id,)
        )
        mysql.connection.commit()
        cursor.close()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
```

### 4. Полный скрипт создания (выполнить в указанном порядке)

```sql
-- ПОЛНЫЙ СКРИПТ СОЗДАНИЯ ОБЪЕКТОВ
-- Выполнять команды по очереди

-- 1. Создание таблицы
CREATE TABLE u_redmine_notifications (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Уникальный идентификатор уведомления',
    user_id INT NOT NULL COMMENT 'ID пользователя из таблицы users Redmine',
    redmine_issue_id INT NOT NULL COMMENT 'ID задачи из таблицы issues Redmine',
    issue_subject VARCHAR(255) NOT NULL COMMENT 'Тема задачи',
    issue_description TEXT COMMENT 'Описание уведомления (готовый текст для показа)',
    author_name VARCHAR(255) COMMENT 'Имя автора задачи',
    author_email VARCHAR(255) COMMENT 'Email автора задачи',
    group_name VARCHAR(255) COMMENT 'Название группы (NULL для индивидуальных назначений)',
    is_read BOOLEAN DEFAULT FALSE COMMENT 'Прочитано ли уведомление',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Время создания уведомления',

    INDEX idx_user_unread (user_id, is_read),
    INDEX idx_issue (redmine_issue_id),
    INDEX idx_created (created_at),
    UNIQUE KEY uk_user_issue (user_id, redmine_issue_id, created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Уведомления о назначениях задач Redmine';

-- 2. Создание триггера
DELIMITER $$

CREATE TRIGGER trg_redmine_assignment_notification
AFTER UPDATE ON issues
FOR EACH ROW
BEGIN
    DECLARE assignment_type VARCHAR(10);
    DECLARE author_name VARCHAR(255);
    DECLARE author_email VARCHAR(255);
    DECLARE group_name VARCHAR(255);

    IF (OLD.assigned_to_id != NEW.assigned_to_id OR
        (OLD.assigned_to_id IS NULL AND NEW.assigned_to_id IS NOT NULL))
       AND NEW.assigned_to_id IS NOT NULL THEN

        SELECT type INTO assignment_type FROM users WHERE id = NEW.assigned_to_id;

        SELECT CONCAT(IFNULL(firstname, ''), ' ', IFNULL(lastname, '')),
               IFNULL(mail, '')
        INTO author_name, author_email
        FROM users WHERE id = NEW.author_id;

        IF assignment_type = 'Group' THEN
            SELECT IFNULL(lastname, CONCAT('Group_', NEW.assigned_to_id))
            INTO group_name FROM users WHERE id = NEW.assigned_to_id;

            INSERT INTO u_redmine_notifications (
                user_id, redmine_issue_id, issue_subject,
                issue_description, author_name, author_email,
                group_name, is_read, created_at
            )
            SELECT
                u.id, NEW.id, NEW.subject,
                CONCAT('В вашу группу ', group_name, ' поступила задача #', NEW.id, ' от ', author_name, ': ', NEW.subject),
                author_name, author_email, group_name, 0, NOW()
            FROM users u
            JOIN groups_users gu ON u.id = gu.user_id
            WHERE gu.group_id = NEW.assigned_to_id AND u.type = 'User' AND u.status = 1;

        ELSEIF assignment_type = 'User' THEN
            INSERT INTO u_redmine_notifications (
                user_id, redmine_issue_id, issue_subject,
                issue_description, author_name, author_email,
                group_name, is_read, created_at
            ) VALUES (
                NEW.assigned_to_id, NEW.id, NEW.subject,
                CONCAT('★ Вы назначены исполнителем по задаче #', NEW.id, ' (https://helpdesk.teztour.com/issues/', NEW.id, ')\nТема: ', NEW.subject, '\nОписание: ', IFNULL(LEFT(NEW.description, 200), 'Без описания')),
                author_name, author_email, NULL, 0, NOW()
            );
        END IF;

    END IF;
END$$

DELIMITER ;
```

## ✅ ИТОГОВЫЕ ХАРАКТЕРИСТИКИ

- **Таблица:** `u_redmine_notifications` (10 столбцов)
- **Триггер:** `trg_redmine_assignment_notification`
- **Python API:** 3 функции для работы с уведомлениями
- **Время реализации:** 4-5 дней

**Готово к реализации с нуля!** 🚀

## ⚠️ РЕШЕНИЕ ПРОБЛЕМЫ С МНОЖЕСТВЕННЫМИ ТРИГГЕРАМИ

### Проблема
```
This version of MySQL doesn't yet support 'multiple triggers with the same action time and event for one table'
```

**Причина:** На таблице `issues` уже существует триггер `AFTER UPDATE`, а в старых версиях MySQL можно иметь только один триггер на событие.

### 🔍 Диагностика существующих триггеров

```sql
-- Проверка существующих триггеров на таблице issues
SHOW TRIGGERS WHERE `Table` = 'issues';

-- Или более детально
SELECT TRIGGER_NAME, EVENT_MANIPULATION, ACTION_TIMING
FROM INFORMATION_SCHEMA.TRIGGERS
WHERE TABLE_NAME = 'issues'
AND TABLE_SCHEMA = DATABASE();
```

### 🛠️ РЕШЕНИЕ 1: Модификация существующего триггера (РЕКОМЕНДУЕТСЯ)

```sql
-- 1. Сначала получаем код существующего триггера
SHOW CREATE TRIGGER [имя_существующего_триггера];

-- 2. Удаляем существующий триггер
DROP TRIGGER [имя_существующего_триггера];

-- 3. Создаем объединенный триггер с нашей логикой
DELIMITER $$

CREATE TRIGGER [имя_существующего_триггера]
AFTER UPDATE ON issues
FOR EACH ROW
BEGIN
    -- СУЩЕСТВУЮЩАЯ ЛОГИКА (копируем из старого триггера)
    -- ... код существующего триггера ...

    -- НОВАЯ ЛОГИКА для уведомлений Redmine
    DECLARE assignment_type VARCHAR(10);
    DECLARE author_name VARCHAR(255);
    DECLARE author_email VARCHAR(255);
    DECLARE group_name VARCHAR(255);

    -- Проверяем изменение assigned_to_id (только назначение, не снятие)
    IF (OLD.assigned_to_id != NEW.assigned_to_id OR
        (OLD.assigned_to_id IS NULL AND NEW.assigned_to_id IS NOT NULL))
       AND NEW.assigned_to_id IS NOT NULL THEN

        -- Получаем тип назначения
        SELECT type INTO assignment_type FROM users WHERE id = NEW.assigned_to_id;

        -- Получаем данные автора
        SELECT CONCAT(IFNULL(firstname, ''), ' ', IFNULL(lastname, '')),
               IFNULL(mail, '')
        INTO author_name, author_email
        FROM users WHERE id = NEW.author_id;

        IF assignment_type = 'Group' THEN
            -- Получаем название группы
            SELECT IFNULL(lastname, CONCAT('Group_', NEW.assigned_to_id))
            INTO group_name FROM users WHERE id = NEW.assigned_to_id;

            -- Создаем уведомления для всех участников группы
            INSERT INTO u_redmine_notifications (
                user_id, redmine_issue_id, issue_subject,
                issue_description, author_name, author_email,
                group_name, is_read, created_at
            )
            SELECT
                u.id, NEW.id, NEW.subject,
                CONCAT('В вашу группу ', group_name, ' поступила задача #', NEW.id, ' от ', author_name, ': ', NEW.subject),
                author_name, author_email, group_name, 0, NOW()
            FROM users u
            JOIN groups_users gu ON u.id = gu.user_id
            WHERE gu.group_id = NEW.assigned_to_id AND u.type = 'User' AND u.status = 1;

        ELSEIF assignment_type = 'User' THEN
            -- Создаем индивидуальное уведомление
            INSERT INTO u_redmine_notifications (
                user_id, redmine_issue_id, issue_subject,
                issue_description, author_name, author_email,
                group_name, is_read, created_at
            ) VALUES (
                NEW.assigned_to_id, NEW.id, NEW.subject,
                CONCAT('★ Вы назначены исполнителем по задаче #', NEW.id, ' (https://helpdesk.teztour.com/issues/', NEW.id, ')\nТема: ', NEW.subject, '\nОписание: ', IFNULL(LEFT(NEW.description, 200), 'Без описания')),
                author_name, author_email, NULL, 0, NOW()
            );
        END IF;

    END IF;
END$$

DELIMITER ;
```

### 🛠️ РЕШЕНИЕ 2: Использование BEFORE UPDATE триггера

```sql
-- Альтернативный вариант с BEFORE UPDATE
DELIMITER $$

CREATE TRIGGER trg_redmine_assignment_before
BEFORE UPDATE ON issues
FOR EACH ROW
BEGIN
    -- Сохраняем информацию об изменении в временную таблицу
    IF (OLD.assigned_to_id != NEW.assigned_to_id OR
        (OLD.assigned_to_id IS NULL AND NEW.assigned_to_id IS NOT NULL))
       AND NEW.assigned_to_id IS NOT NULL THEN

        -- Создаем временную запись для обработки в AFTER триггере
        INSERT INTO temp_assignment_changes (
            issue_id, old_assigned_to, new_assigned_to, change_time
        ) VALUES (
            NEW.id, OLD.assigned_to_id, NEW.assigned_to_id, NOW()
        );
    END IF;
END$$

DELIMITER ;

-- Потребуется создать временную таблицу
CREATE TABLE temp_assignment_changes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    issue_id INT,
    old_assigned_to INT,
    new_assigned_to INT,
    change_time TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE
);
```

### 🛠️ РЕШЕНИЕ 3: Планировщик событий (EVENT SCHEDULER)

```sql
-- Включаем планировщик событий
SET GLOBAL event_scheduler = ON;

-- Создаем событие для обработки изменений каждые 30 секунд
DELIMITER $$

CREATE EVENT process_assignment_changes
ON SCHEDULE EVERY 30 SECOND
DO
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_issue_id INT;
    DECLARE v_assigned_to_id INT;
    DECLARE assignment_type VARCHAR(10);
    DECLARE author_name VARCHAR(255);
    DECLARE author_email VARCHAR(255);
    DECLARE group_name VARCHAR(255);

    DECLARE cur CURSOR FOR
        SELECT issue_id, new_assigned_to
        FROM temp_assignment_changes
        WHERE processed = FALSE;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cur;

    read_loop: LOOP
        FETCH cur INTO v_issue_id, v_assigned_to_id;
        IF done THEN
            LEAVE read_loop;
        END IF;

        -- Обработка логики уведомлений (аналогично триггеру)
        -- ... код обработки ...

        -- Помечаем как обработанное
        UPDATE temp_assignment_changes
        SET processed = TRUE
        WHERE issue_id = v_issue_id AND new_assigned_to = v_assigned_to_id;

    END LOOP;

    CLOSE cur;

    -- Очищаем старые записи (старше 1 часа)
    DELETE FROM temp_assignment_changes
    WHERE change_time < DATE_SUB(NOW(), INTERVAL 1 HOUR);
END$$

DELIMITER ;
```

### 🎯 РЕКОМЕНДУЕМАЯ ПОСЛЕДОВАТЕЛЬНОСТЬ ДЕЙСТВИЙ

1. **Сначала диагностика:**
   ```sql
   SHOW TRIGGERS WHERE `Table` = 'issues';
   ```

2. **Получить код существующего триггера:**
   ```sql
   SHOW CREATE TRIGGER [имя_триггера];
   ```

3. **Создать резервную копию** существующего триггера

4. **Модифицировать существующий триггер**, добавив нашу логику

5. **Тестировать** на тестовых данных

### ⚡ БЫСТРОЕ РЕШЕНИЕ (если существующий триггер простой)

```sql
-- Проверяем существующие триггеры
SHOW TRIGGERS WHERE `Table` = 'issues';

-- Если триггер простой или неважный, можно его заменить
DROP TRIGGER [имя_существующего_триггера];

-- Создаем наш триггер
-- ... код нашего триггера ...
```

**Какой вариант предпочтительнее для вашей ситуации?** Нужно сначала посмотреть, что делает существующий триггер.
