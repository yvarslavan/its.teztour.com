#!/bin/bash

################################################################################
# Flask Helpdesk Production Deployment Script
# Развертывание на: /opt/www/its.teztour.com/
# Date: 2026-01-25
# Usage: ./deploy.sh [--dry-run] [--skip-backup] [--skip-tests]
################################################################################

set -o pipefail

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

# Пути
PROJECT_DIR="/opt/www/its.teztour.com"
BACKUP_DIR="/opt/backups/its-teztour"
LOG_DIR="/var/log/its-teztour"
VENV_DIR="${PROJECT_DIR}/venv"
BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Сервис
SERVICE_NAME="its-teztour"
SERVICE_USER="www-data"
SERVICE_GROUP="www-data"

# Параметры
DRY_RUN=false
SKIP_BACKUP=false
SKIP_TESTS=false
VERBOSE=true

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# ФУНКЦИИ ЛОГИРОВАНИЯ
# ============================================================================

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $*"
}

success() {
    echo -e "${GREEN}[✓]${NC} $*"
}

error() {
    echo -e "${RED}[✗] ERROR:${NC} $*" >&2
}

warning() {
    echo -e "${YELLOW}[!] WARNING:${NC} $*"
}

section() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}▶ $*${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
}

# ============================================================================
# ОБРАБОТКА АРГУМЕНТОВ
# ============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            log "Режим DRY-RUN: изменения не будут применены"
            shift
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            warning "Пропуск бэкапов! Используйте осторожно!"
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            warning "Пропуск тестов после деплоя"
            shift
            ;;
        *)
            error "Неизвестный аргумент: $1"
            exit 1
            ;;
    esac
done

# ============================================================================
# ПРЕДВАРИТЕЛЬНЫЕ ПРОВЕРКИ
# ============================================================================

section "ПРЕДВАРИТЕЛЬНЫЕ ПРОВЕРКИ"

# Проверка прав доступа
if [[ $EUID -ne 0 ]]; then
    error "Этот скрипт должен быть запущен от root'а (используйте sudo)"
    exit 1
fi
success "Запущен от root'а"

# Проверка существования директории проекта
if [[ ! -d "$PROJECT_DIR" ]]; then
    error "Директория проекта не найдена: $PROJECT_DIR"
    exit 1
fi
success "Директория проекта найдена: $PROJECT_DIR"

# Проверка наличия git
if ! command -v git &> /dev/null; then
    error "git не установлен"
    exit 1
fi
success "git установлен"

# Проверка наличия python
if ! command -v python3 &> /dev/null; then
    error "python3 не установлен"
    exit 1
fi
success "python3 установлен: $(python3 --version)"

# Создание директорий логирования и бэкапов
mkdir -p "$LOG_DIR" "$BACKUP_DIR"
chmod 755 "$LOG_DIR" "$BACKUP_DIR"
success "Директории логирования и бэкапов готовы"

# ============================================================================
# ЭТАП 1: ПОДГОТОВКА К ДЕПЛОЮ
# ============================================================================

section "ЭТАП 1: ПОДГОТОВКА К ДЕПЛОЮ"

log "Проверка статуса сервиса..."
if systemctl is-active --quiet $SERVICE_NAME; then
    success "Сервис $SERVICE_NAME запущен"
    SERVICE_WAS_RUNNING=true
else
    warning "Сервис $SERVICE_NAME не запущен"
    SERVICE_WAS_RUNNING=false
fi

# Проверка наличия изменений в git
log "Проверка изменений git..."
cd "$PROJECT_DIR" || exit 1

if ! git status &>/dev/null; then
    error "Не git репозиторий: $PROJECT_DIR"
    exit 1
fi

CHANGES=$(git status --short)
if [[ -n "$CHANGES" && "$DRY_RUN" != true ]]; then
    warning "Обнаружены незакоммиченные изменения:"
    echo "$CHANGES"
    read -p "Продолжить? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        error "Деплой отменён пользователем"
        exit 1
    fi
fi
success "Проверка git завершена"

# ============================================================================
# ЭТАП 2: СОЗДАНИЕ БЭКАПОВ
# ============================================================================

section "ЭТАП 2: СОЗДАНИЕ БЭКАПОВ"
warning "Пропуск создания бэкапов (отключено)"

# ============================================================================
# ЭТАП 3: ОСТАНОВКА СЕРВИСА
# ============================================================================

section "ЭТАП 3: ОСТАНОВКА СЕРВИСА"

if [[ "$SERVICE_WAS_RUNNING" == true ]]; then
    log "Остановка сервиса $SERVICE_NAME..."
    if [[ "$DRY_RUN" == true ]]; then
        log "[DRY-RUN] systemctl stop $SERVICE_NAME"
    else
        if systemctl stop "$SERVICE_NAME"; then
            success "Сервис $SERVICE_NAME остановлен"
            # Дождаться завершения процессов
            sleep 2
        else
            error "Не удалось остановить сервис $SERVICE_NAME"
            exit 1
        fi
    fi
else
    warning "Сервис уже был остановлен"
fi

# ============================================================================
# ЭТАП 4: ОБНОВЛЕНИЕ КОДА
# ============================================================================

section "ЭТАП 4: ОБНОВЛЕНИЕ КОДА ИЗ GITHUB"

cd "$PROJECT_DIR" || exit 1

log "Проверка git статуса..."
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
CURRENT_COMMIT=$(git rev-parse --short HEAD)
log "Текущая ветка: $CURRENT_BRANCH @ $CURRENT_COMMIT"

log "Обновление git..."
if [[ "$DRY_RUN" == true ]]; then
    log "[DRY-RUN] git fetch origin"
    log "[DRY-RUN] git pull origin $CURRENT_BRANCH"
else
    if ! git fetch origin; then
        error "Не удалось получить обновления из репозитория"
        exit 1
    fi
    success "Git fetch завершён"

    if ! git pull origin "$CURRENT_BRANCH"; then
        error "Не удалось выполнить git pull"
        exit 1
    fi
    
    NEW_COMMIT=$(git rev-parse --short HEAD)
    if [[ "$CURRENT_COMMIT" != "$NEW_COMMIT" ]]; then
        success "Код обновлён: $CURRENT_COMMIT → $NEW_COMMIT"
    else
        log "Код уже актуален (нет новых коммитов)"
    fi
fi

# ============================================================================
# ЭТАП 5: ОБНОВЛЕНИЕ ЗАВИСИМОСТЕЙ PYTHON
# ============================================================================

section "ЭТАП 5: ОБНОВЛЕНИЕ ЗАВИСИМОСТЕЙ PYTHON"

log "Проверка виртуального окружения..."
if [[ ! -d "$VENV_DIR" ]]; then
    warning "Виртуальное окружение не найдено, создание..."
    if [[ "$DRY_RUN" == true ]]; then
        log "[DRY-RUN] python3 -m venv $VENV_DIR"
    else
        if ! python3 -m venv "$VENV_DIR"; then
            error "Не удалось создать виртуальное окружение"
            exit 1
        fi
        success "Виртуальное окружение создано"
    fi
fi

log "Активация виртуального окружения..."
if [[ "$DRY_RUN" == true ]]; then
    log "[DRY-RUN] source $VENV_DIR/bin/activate"
else
    # shellcheck disable=SC1090
    source "$VENV_DIR/bin/activate" || exit 1
    success "Виртуальное окружение активировано"
fi

log "Обновление pip, setuptools, wheel..."
if [[ "$DRY_RUN" == true ]]; then
    log "[DRY-RUN] pip install --upgrade pip setuptools wheel"
else
    if ! pip install --upgrade pip setuptools wheel &>/dev/null; then
        error "Не удалось обновить pip"
        exit 1
    fi
    success "pip, setuptools, wheel обновлены"
fi

log "Установка зависимостей из requirements.txt..."
if [[ ! -f "${PROJECT_DIR}/requirements.txt" ]]; then
    error "requirements.txt не найден"
    exit 1
fi

if [[ "$DRY_RUN" == true ]]; then
    log "[DRY-RUN] pip install -r requirements.txt"
else
    if pip install -r "${PROJECT_DIR}/requirements.txt" >> "${LOG_DIR}/pip-install-${BACKUP_TIMESTAMP}.log" 2>&1; then
        success "Зависимости установлены"
    else
        error "Не удалось установить зависимости (см. ${LOG_DIR}/pip-install-${BACKUP_TIMESTAMP}.log)"
        exit 1
    fi
fi

# ============================================================================
# ЭТАП 6: ПРОВЕРКА КОНФИГУРАЦИИ
# ============================================================================

section "ЭТАП 6: ПРОВЕРКА КОНФИГУРАЦИИ"

log "Проверка файла .env..."
if [[ ! -f "${PROJECT_DIR}/.env" ]]; then
    error "Файл .env не найден!"
    echo "Требуются следующие переменные окружения:"
    echo "  - FLASK_ENV (production)"
    echo "  - FLASK_DEBUG (0)"
    echo "  - SECRET_KEY (надежная строка)"
    echo "  - MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE"
    echo "  - MYSQL_QUALITY_HOST, MYSQL_QUALITY_USER, MYSQL_QUALITY_PASSWORD, MYSQL_QUALITY_DATABASE"
    echo "  - REDMINE_URL, REDMINE_API_KEY"
    echo ""
    exit 1
fi
success "Файл .env найден"

# Проверка критических переменных окружения
log "Проверка критических переменных окружения..."
REQUIRED_VARS=("FLASK_ENV" "SECRET_KEY" "MYSQL_HOST" "MYSQL_USER" "MYSQL_DATABASE")

for var in "${REQUIRED_VARS[@]}"; do
    if ! grep -q "^${var}=" "${PROJECT_DIR}/.env"; then
        warning "Переменная $var не найдена в .env"
    fi
done
success "Проверка переменных окружения завершена"

log "Проверка подключения к Flask приложению..."
if [[ "$SKIP_TESTS" == true ]]; then
    log "[SKIP-TESTS] Пропуск проверки Flask приложения"
elif [[ "$DRY_RUN" == true ]]; then
    log "[DRY-RUN] python -c 'from blog import create_app; app = create_app()'"
else
    cd "$PROJECT_DIR" || exit 1
    export FLASK_APP=app.py
    
    # Загрузить переменные окружения из .env файла
    if [[ -f "${PROJECT_DIR}/.env" ]]; then
        set -a
        source "${PROJECT_DIR}/.env"
        set +a
    fi
    
    if python -c "from blog import create_app; app = create_app()" >> "${LOG_DIR}/app-import-${BACKUP_TIMESTAMP}.log" 2>&1; then
        success "Flask приложение загружается успешно"
    else
        error "Ошибка при загрузке Flask приложения (см. ${LOG_DIR}/app-import-${BACKUP_TIMESTAMP}.log)"
        cat "${LOG_DIR}/app-import-${BACKUP_TIMESTAMP}.log"
        exit 1
    fi
fi

# ============================================================================
# ЭТАП 7: ОЧИСТКА КЭША И СЕССИЙ
# ============================================================================

section "ЭТАП 7: ОЧИСТКА КЭША И СЕССИЙ"

log "Удаление Python кэша..."
if [[ "$DRY_RUN" == true ]]; then
    log "[DRY-RUN] find $PROJECT_DIR -type d -name __pycache__ -exec rm -rf {} +"
    log "[DRY-RUN] find $PROJECT_DIR -type f -name '*.pyc' -delete"
else
    find "$PROJECT_DIR" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
    find "$PROJECT_DIR" -type f -name '*.pyc' -delete 2>/dev/null
    success "Python кэш удален"
fi

log "Очистка сессий Flask..."
if [[ "$DRY_RUN" == true ]]; then
    log "[DRY-RUN] rm -rf ${PROJECT_DIR}/flask_session/*"
else
    rm -rf "${PROJECT_DIR}/flask_session"/* 2>/dev/null
    success "Сессии Flask очищены"
fi

# ============================================================================
# ЭТАП 8: НАСТРОЙКА ПРАВ ДОСТУПА
# ============================================================================

section "ЭТАП 8: НАСТРОЙКА ПРАВ ДОСТУПА"

log "Установка прав доступа для $SERVICE_USER:$SERVICE_GROUP..."

if [[ "$DRY_RUN" == true ]]; then
    log "[DRY-RUN] chown -R $SERVICE_USER:$SERVICE_GROUP $PROJECT_DIR"
    log "[DRY-RUN] chmod -R 755 $PROJECT_DIR"
    log "[DRY-RUN] chmod -R 775 ${PROJECT_DIR}/logs"
    log "[DRY-RUN] chmod -R 775 ${PROJECT_DIR}/blog/db"
else
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$PROJECT_DIR"
    chmod -R 755 "$PROJECT_DIR"
    chmod -R 775 "${PROJECT_DIR}/logs"
    chmod -R 775 "${PROJECT_DIR}/blog/db"
    
    # Убедиться, что скрипты исполняемы
    chmod +x "${PROJECT_DIR}/scripts"/*.py 2>/dev/null
    
    success "Права доступа установлены"
fi

# ============================================================================
# ЭТАП 9: СОЗДАНИЕ/ОБНОВЛЕНИЕ RUNTIME ДИРЕКТОРИЙ
# ============================================================================

section "ЭТАП 9: СОЗДАНИЕ RUNTIME ДИРЕКТОРИЙ"

log "Создание директории для Gunicorn сокета..."
if [[ "$DRY_RUN" == true ]]; then
    log "[DRY-RUN] mkdir -p /run/its-teztour"
    log "[DRY-RUN] chown $SERVICE_USER:$SERVICE_GROUP /run/its-teztour"
    log "[DRY-RUN] chmod 755 /run/its-teztour"
else
    mkdir -p /run/its-teztour
    chown "$SERVICE_USER:$SERVICE_GROUP" /run/its-teztour
    chmod 755 /run/its-teztour
    success "Runtime директория готова: /run/its-teztour"
fi

# ============================================================================
# ЭТАП 10: ПРОВЕРКА КОНФИГУРАЦИИ СЕРВИСА
# ============================================================================

section "ЭТАП 10: ПРОВЕРКА КОНФИГУРАЦИИ СЕРВИСА"

log "Проверка systemd сервиса $SERVICE_NAME..."
if [[ -f "/etc/systemd/system/${SERVICE_NAME}.service" ]]; then
    success "Systemd сервис найден: $SERVICE_NAME"
    
    log "Содержимое сервиса:"
    systemctl cat "$SERVICE_NAME" | grep -E "^(ExecStart|WorkingDirectory|Environment)" || true
else
    error "Systemd сервис не найден: $SERVICE_NAME"
    echo "Убедитесь, что файл сервиса установлен в /etc/systemd/system/"
    exit 1
fi

log "Проверка Nginx конфигурации..."
if [[ -f "/etc/nginx/sites-enabled/flask-helpdesk" ]] || [[ -f "/etc/nginx/sites-available/flask-helpdesk" ]]; then
    success "Nginx конфигурация найдена"
    
    if [[ "$DRY_RUN" != true ]]; then
        if nginx -t 2>&1 | grep -q "successful"; then
            success "Nginx конфигурация корректна"
        else
            warning "Nginx конфигурация может содержать ошибки"
        fi
    fi
else
    warning "Nginx конфигурация не найдена, проверьте настройки вручную"
fi

# ============================================================================
# ЭТАП 11: ПЕРЕЗАГРУЗКА SYSTEMD
# ============================================================================

section "ЭТАП 11: ПЕРЕЗАГРУЗКА SYSTEMD"

log "Перезагрузка systemd..."
if [[ "$DRY_RUN" == true ]]; then
    log "[DRY-RUN] systemctl daemon-reload"
else
    if systemctl daemon-reload; then
        success "systemd перезагружен"
    else
        error "Не удалось перезагрузить systemd"
        exit 1
    fi
fi

# ============================================================================
# ЭТАП 12: ЗАПУСК СЕРВИСА
# ============================================================================

section "ЭТАП 12: ЗАПУСК СЕРВИСА"

if [[ "$SERVICE_WAS_RUNNING" == true ]]; then
    log "Запуск сервиса $SERVICE_NAME..."
    if [[ "$DRY_RUN" == true ]]; then
        log "[DRY-RUN] systemctl start $SERVICE_NAME"
    else
        if systemctl start "$SERVICE_NAME"; then
            success "Сервис $SERVICE_NAME запущен"
            sleep 2
        else
            error "Не удалось запустить сервис $SERVICE_NAME"
            echo "Проверьте логи: journalctl -u $SERVICE_NAME -f"
            exit 1
        fi
    fi
else
    log "Сервис был остановлен, оставляем его остановленным"
fi

# ============================================================================
# ЭТАП 13: ПРОВЕРКА СТАТУСА СЕРВИСА
# ============================================================================

section "ЭТАП 13: ПРОВЕРКА СТАТУСА СЕРВИСА"

if [[ "$DRY_RUN" != true ]] && [[ "$SERVICE_WAS_RUNNING" == true ]]; then
    sleep 3
    
    log "Проверка статуса сервиса..."
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        success "Сервис $SERVICE_NAME активен"
        
        # Проверить использование портов
        log "Статус сокета Gunicorn:"
        if [[ -S "/run/its-teztour/gunicorn.sock" ]]; then
            success "Сокет Gunicorn существует: /run/its-teztour/gunicorn.sock"
        else
            warning "Сокет Gunicorn не найден"
        fi
    else
        error "Сервис $SERVICE_NAME не активен"
        echo ""
        echo "Последние логи:"
        journalctl -u "$SERVICE_NAME" -n 20 --no-pager
        exit 1
    fi
else
    log "Проверка статуса пропущена (dry-run или сервис был остановлен)"
fi

# ============================================================================
# ЭТАП 14: ПРОВЕРКА ЛОГОВ
# ============================================================================

section "ЭТАП 14: ПРОВЕРКА ЛОГОВ"

if [[ "$DRY_RUN" != true ]]; then
    log "Проверка логов приложения на ошибки..."
    
    if [[ -f "${PROJECT_DIR}/logs/app.log" ]]; then
        log "Последние 10 строк лога приложения:"
        tail -n 10 "${PROJECT_DIR}/logs/app.log" || true
    fi
    
    log "Проверка systemd логов..."
    if [[ "$SERVICE_WAS_RUNNING" == true ]]; then
        journalctl -u "$SERVICE_NAME" -n 10 --no-pager || true
    fi
else
    log "Проверка логов пропущена (dry-run)"
fi

# ============================================================================
# ЭТАП 15: ФИНАЛЬНЫЕ ТЕСТЫ (опционально)
# ============================================================================

if [[ "$SKIP_TESTS" == false ]]; then
    section "ЭТАП 15: ФИНАЛЬНЫЕ ТЕСТЫ"

    if [[ "$DRY_RUN" != true ]] && [[ "$SERVICE_WAS_RUNNING" == true ]]; then
        log "Попытка подключения к приложению..."
        
        # Проверить HTTPS (требуется curl)
        if command -v curl &> /dev/null; then
            log "Отправка тестового запроса..."
            if curl -sk https://localhost/ -o /dev/null -w "%{http_code}\n" 2>/dev/null; then
                success "Приложение отвечает на HTTPS запросы"
            else
                warning "Не удалось проверить HTTPS (может быть блокирует брандмауэр)"
            fi
        fi
    else
        log "Тесты пропущены (dry-run или сервис был остановлен)"
    fi
fi

# ============================================================================
# ФИНАЛЬНЫЙ ОТЧЕТ
# ============================================================================

section "✓ ДЕПЛОЙ ЗАВЕРШЁН"

success "Все этапы выполнены успешно!"
echo ""
echo "📊 Сводка:"
echo "  Project:     $PROJECT_DIR"
echo "  Service:     $SERVICE_NAME"
echo "  Branch:      $CURRENT_BRANCH"
echo "  Commit:      $(git rev-parse --short HEAD)"
echo "  Timestamp:   $BACKUP_TIMESTAMP"
echo ""
echo "📁 Бэкапы находятся в: $BACKUP_DIR"
echo "📝 Логи находятся в: $LOG_DIR"
echo ""

if [[ "$DRY_RUN" == true ]]; then
    warning "Это был DRY-RUN. Никакие изменения не были применены."
    echo "Для реального деплоя запустите без флага --dry-run"
else
    echo "✅ Приложение готово к использованию!"
    echo ""
    echo "🔍 Для проверки статуса используйте:"
    echo "   systemctl status $SERVICE_NAME"
    echo "   journalctl -u $SERVICE_NAME -f"
    echo ""
    echo "📋 Для просмотра логов приложения:"
    echo "   tail -f ${PROJECT_DIR}/logs/app.log"
fi

exit 0