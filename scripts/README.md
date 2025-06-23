# 🗄️ Скрипты управления базой данных Flask Helpdesk

Коллекция скриптов для автоматизации работы с базой данных при деплое и разработке.

## 📋 Обзор скриптов

### 🔧 `init_database.py` - Инициализация базы данных
Создает новую базу данных с нуля или из SQL дампа.

**Основные функции:**
- ✅ Создание БД из SQL дампа (`blog/db/blog.db.sql`)
- ✅ Инициализация через Flask-Migrate
- ✅ Создание администратора по умолчанию
- ✅ Проверка целостности БД
- ✅ Автоматическое резервное копирование

**Использование:**
```bash
# Проверка существующей БД
python scripts/init_database.py --check-only

# Создание новой БД из SQL дампа
python scripts/init_database.py --from-sql --force

# Создание через миграции
python scripts/init_database.py --force

# Справка
python scripts/init_database.py --help
```

### 🔄 `migrate_database.py` - Миграция базы данных
Обновляет схему базы данных при изменениях в моделях.

**Основные функции:**
- ✅ Применение миграций Flask-Migrate
- ✅ Автоматическая генерация миграций
- ✅ Откат к предыдущей версии
- ✅ Проверка целостности после миграции
- ✅ Резервное копирование перед миграцией

**Использование:**
```bash
# Применение всех доступных миграций
python scripts/migrate_database.py

# Проверка целостности миграций
python scripts/migrate_database.py --check-only

# Автоматическая генерация миграции
python scripts/migrate_database.py --auto-generate -m "Описание изменений"

# Откат к предыдущей версии
python scripts/migrate_database.py --rollback

# Откат к конкретной версии
python scripts/migrate_database.py --rollback 0b429be4bc23
```

### 🗄️ `manage_data.py` - Управление данными
Экспорт, импорт и управление данными в базе.

**Основные функции:**
- ✅ Экспорт данных в JSON/SQL
- ✅ Импорт данных из файлов
- ✅ Очистка таблиц
- ✅ Создание тестовых данных
- ✅ Статистика по БД

### 🔍 `monitor_database.py` - Мониторинг базы данных
Контролирует состояние и производительность БД.

**Основные функции:**
- ✅ Проверка здоровья БД
- ✅ Анализ производительности
- ✅ Мониторинг резервных копий
- ✅ Генерация отчетов
- ✅ Рекомендации по оптимизации

### 🚀 `deploy_automation.py` - Автоматизация развертывания
Объединяет все скрипты в единый процесс развертывания.

**Основные функции:**
- ✅ Полная автоматизация развертывания
- ✅ Новая установка и обновления
- ✅ Безопасное развертывание с бэкапами
- ✅ Проверки после развертывания
- ✅ Отчеты о развертывании

**Использование:**
```bash
# Статистика БД
python scripts/manage_data.py stats

# Экспорт всех данных в JSON
python scripts/manage_data.py export --format json

# Экспорт конкретных таблиц в SQL
python scripts/manage_data.py export --tables users posts --format sql

# Импорт данных из файла
python scripts/manage_data.py import blog/db/exports/export_20241201_120000.json

# Импорт с очисткой таблиц
python scripts/manage_data.py import data.json --clear

# Создание тестовых данных
python scripts/manage_data.py create-test

# Очистка всех таблиц (требует подтверждения)
python scripts/manage_data.py clear --confirm

# Очистка конкретных таблиц
python scripts/manage_data.py clear --tables posts notifications --confirm
```

**Использование monitor_database.py:**
```bash
# Проверка здоровья БД
python scripts/monitor_database.py health

# Проверка производительности
python scripts/monitor_database.py performance

# Проверка резервных копий
python scripts/monitor_database.py backups

# Полный отчет о состоянии БД
python scripts/monitor_database.py report
```

**Использование deploy_automation.py:**
```bash
# Новая установка с нуля
python scripts/deploy_automation.py fresh

# Обновление существующей установки
python scripts/deploy_automation.py update

# Безопасное обновление с резервной копией
python scripts/deploy_automation.py update-safe

# Только проверки после развертывания
python scripts/deploy_automation.py check

# Полный цикл развертывания с проверками
python scripts/deploy_automation.py full --mode update

# Генерация отчета о развертывании
python scripts/deploy_automation.py report
```

## 🚀 Сценарии использования

### 📦 Первый деплой (новый сервер)
```bash
# 1. Создание БД из SQL дампа
python scripts/init_database.py --from-sql --force

# 2. Проверка корректности
python scripts/init_database.py --check-only

# 3. Создание тестовых данных (опционально)
python scripts/manage_data.py create-test
```

### 🔄 Обновление существующего деплоя
```bash
# 1. Проверка текущего состояния
python scripts/migrate_database.py --check-only

# 2. Применение миграций
python scripts/migrate_database.py

# 3. Проверка после миграции
python scripts/migrate_database.py --check-only
```

### 🧪 Разработка и тестирование
```bash
# Создание чистой БД для разработки
python scripts/init_database.py --force

# Заполнение тестовыми данными
python scripts/manage_data.py create-test

# Экспорт данных для переноса
python scripts/manage_data.py export --format json

# Очистка для новых тестов
python scripts/manage_data.py clear --confirm
```

### 💾 Резервное копирование и восстановление
```bash
# Экспорт всех данных
python scripts/manage_data.py export --format sql

# Статистика перед бэкапом
python scripts/manage_data.py stats

# Восстановление из бэкапа
python scripts/manage_data.py import backup_file.sql --clear
```

## 🔧 Интеграция с GitLab CI

Скрипты автоматически интегрированы в `.gitlab-ci.yml`:

```yaml
# Автоматическая инициализация БД при деплое
- python scripts/init_database.py --check-only || python scripts/init_database.py --from-sql --force

# Применение миграций
- python scripts/migrate_database.py
```

## 📁 Структура файлов

```
scripts/
├── init_database.py      # Инициализация БД
├── migrate_database.py   # Миграции БД
├── manage_data.py        # Управление данными
├── monitor_database.py   # Мониторинг БД
├── deploy_automation.py  # Автоматизация развертывания
└── README.md            # Документация

blog/db/
├── blog.db              # Основная БД (создается автоматически)
├── blog.db.sql          # SQL дамп для инициализации
├── exports/             # Директория экспортов
└── blog_backup_*.db     # Автоматические бэкапы
```

## 🛡️ Безопасность

### 🔒 Автоматические бэкапы
- ✅ Все скрипты создают резервные копии перед изменениями
- ✅ Бэкапы содержат timestamp в имени файла
- ✅ Старые бэкапы автоматически удаляются (хранятся последние 3)

### ⚠️ Подтверждения операций
- ✅ Деструктивные операции требуют флага `--confirm`
- ✅ Перезапись БД требует флага `--force`
- ✅ Интерактивные подтверждения в критических случаях

### 📋 Логирование
- ✅ Подробное логирование всех операций
- ✅ Логи сохраняются в файлы
- ✅ Цветное форматирование для консоли

## 🐛 Устранение неполадок

### ❌ "База данных не найдена"
```bash
# Создайте БД из SQL дампа
python scripts/init_database.py --from-sql --force
```

### ❌ "Ошибка миграции"
```bash
# Проверьте целостность
python scripts/migrate_database.py --check-only

# Откатитесь к предыдущей версии
python scripts/migrate_database.py --rollback
```

### ❌ "Не удается импортировать Flask приложение"
```bash
# Убедитесь, что FLASK_APP установлена
export FLASK_APP=app.py

# Активируйте виртуальное окружение
source venv/bin/activate
```

### ❌ "Ошибка доступа к файлам"
```bash
# Проверьте права доступа
chmod +x scripts/*.py

# Убедитесь в существовании директорий
mkdir -p blog/db/exports
```

## 🔗 Связанные файлы

- **`.gitlab-ci.yml`** - Конфигурация CI/CD с интеграцией скриптов
- **`blog/settings.py`** - Конфигурация путей к БД
- **`migrations/`** - Директория миграций Flask-Migrate
- **`blog/models.py`** - Модели данных SQLAlchemy

## 📞 Поддержка

При возникновении проблем:

1. 📋 Проверьте логи в файлах `*.log`
2. 🔍 Используйте флаг `--check-only` для диагностики
3. 💾 Восстановите из резервной копии при критических ошибках
4. 📧 Обратитесь к команде разработки с подробным описанием проблемы

---

*Автоматизация базы данных Flask Helpdesk - надежно, безопасно, эффективно! 🚀*
