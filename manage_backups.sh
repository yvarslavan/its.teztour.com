#!/bin/bash

# Скрипт для управления бэкапами Flask Helpdesk
# Использование: bash manage_backups.sh [list|clean|keep-latest]

set -e

BACKUP_DIR="/var/www"
BACKUP_PREFIX="flask_helpdesk_backup_"
CURRENT_DIR="flask_helpdesk"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🗂️  Менеджер бэкапов Flask Helpdesk${NC}"
echo "=================================="

# Функция для отображения списка бэкапов
list_backups() {
    echo -e "${YELLOW}📋 Список текущих бэкапов:${NC}"
    echo ""

    cd "$BACKUP_DIR"

    if ls ${BACKUP_PREFIX}* 1> /dev/null 2>&1; then
        echo -e "Директория\t\t\tРазмер\t\tДата создания"
        echo "------------------------------------------------------------"

        for backup in ${BACKUP_PREFIX}*; do
            if [ -d "$backup" ]; then
                size=$(du -sh "$backup" | cut -f1)
                # Извлекаем дату из имени бэкапа
                date_str=$(echo "$backup" | sed "s/${BACKUP_PREFIX}//")
                formatted_date=$(echo "$date_str" | sed 's/\([0-9]\{4\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)-\([0-9]\{2\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)/\3.\2.\1 \4:\5:\6/')
                echo -e "$backup\t$size\t\t$formatted_date"
            fi
        done | sort -k3,3r  # Сортируем по дате (новые сверху)

        echo ""
        total_size=$(du -sh ${BACKUP_PREFIX}* 2>/dev/null | awk '{sum+=$1} END {print sum}' || echo "0")
        echo -e "${BLUE}📊 Общий размер бэкапов: $(du -ch ${BACKUP_PREFIX}* 2>/dev/null | tail -1 | cut -f1)${NC}"

        backup_count=$(ls -d ${BACKUP_PREFIX}* 2>/dev/null | wc -l)
        echo -e "${BLUE}📦 Количество бэкапов: $backup_count${NC}"
    else
        echo -e "${YELLOW}⚠️  Бэкапы не найдены${NC}"
    fi
}

# Функция для очистки старых бэкапов (оставляем только последние N)
keep_latest() {
    local keep_count=${1:-3}  # По умолчанию оставляем 3 последних

    echo -e "${YELLOW}🧹 Очистка старых бэкапов (оставляем последние $keep_count)...${NC}"

    cd "$BACKUP_DIR"

    if ! ls ${BACKUP_PREFIX}* 1> /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Бэкапы не найдены${NC}"
        return
    fi

    # Получаем список бэкапов, отсортированный по дате (новые сверху)
    backups=($(ls -dt ${BACKUP_PREFIX}* 2>/dev/null))
    total_backups=${#backups[@]}

    if [ $total_backups -le $keep_count ]; then
        echo -e "${GREEN}✅ Количество бэкапов ($total_backups) не превышает лимит ($keep_count)${NC}"
        return
    fi

    echo -e "${BLUE}📦 Найдено бэкапов: $total_backups${NC}"
    echo -e "${BLUE}🎯 Оставляем: $keep_count${NC}"
    echo -e "${RED}🗑️  Удаляем: $((total_backups - keep_count))${NC}"
    echo ""

    # Показываем, что будет удалено
    echo -e "${YELLOW}Будут удалены следующие бэкапы:${NC}"
    for ((i=$keep_count; i<$total_backups; i++)); do
        backup=${backups[$i]}
        size=$(du -sh "$backup" | cut -f1)
        echo -e "${RED}❌ $backup ($size)${NC}"
    done

    echo ""
    read -p "Продолжить удаление? (y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        freed_space=0
        for ((i=$keep_count; i<$total_backups; i++)); do
            backup=${backups[$i]}
            size=$(du -sm "$backup" | cut -f1)  # Размер в MB
            freed_space=$((freed_space + size))
            echo -e "${RED}🗑️  Удаляем: $backup${NC}"
            rm -rf "$backup"
        done
        echo ""
        echo -e "${GREEN}✅ Очистка завершена!${NC}"
        echo -e "${GREEN}💾 Освобождено места: ${freed_space}MB${NC}"
    else
        echo -e "${YELLOW}❌ Операция отменена${NC}"
    fi
}

# Функция для полной очистки всех бэкапов (кроме последнего)
clean_all_except_latest() {
    echo -e "${RED}🚨 ВНИМАНИЕ: Будут удалены ВСЕ бэкапы кроме самого последнего!${NC}"
    keep_latest 1
}

# Функция для удаления бэкапов старше N дней
clean_old() {
    local days=${1:-7}  # По умолчанию старше 7 дней

    echo -e "${YELLOW}🧹 Удаление бэкапов старше $days дней...${NC}"

    cd "$BACKUP_DIR"

    old_backups=$(find . -maxdepth 1 -name "${BACKUP_PREFIX}*" -type d -mtime +$days 2>/dev/null || true)

    if [ -z "$old_backups" ]; then
        echo -e "${GREEN}✅ Старых бэкапов (>$days дней) не найдено${NC}"
        return
    fi

    echo -e "${YELLOW}Найдены старые бэкапы:${NC}"
    echo "$old_backups" | while read backup; do
        if [ -n "$backup" ] && [ "$backup" != "." ]; then
            size=$(du -sh "$backup" | cut -f1)
            echo -e "${RED}❌ $backup ($size)${NC}"
        fi
    done

    echo ""
    read -p "Удалить эти бэкапы? (y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        find . -maxdepth 1 -name "${BACKUP_PREFIX}*" -type d -mtime +$days -exec rm -rf {} + 2>/dev/null || true
        echo -e "${GREEN}✅ Старые бэкапы удалены${NC}"
    else
        echo -e "${YELLOW}❌ Операция отменена${NC}"
    fi
}

# Основная логика
case "${1:-list}" in
    "list"|"ls")
        list_backups
        ;;
    "clean")
        keep_latest ${2:-3}
        ;;
    "clean-all")
        clean_all_except_latest
        ;;
    "clean-old")
        clean_old ${2:-7}
        ;;
    "keep-latest")
        keep_latest ${2:-3}
        ;;
    "help"|"--help"|"-h")
        echo "Использование: $0 [команда] [параметр]"
        echo ""
        echo "Команды:"
        echo "  list, ls              - Показать список всех бэкапов"
        echo "  clean [N]             - Оставить только N последних бэкапов (по умолчанию 3)"
        echo "  clean-all             - Удалить все бэкапы кроме самого последнего"
        echo "  clean-old [N]         - Удалить бэкапы старше N дней (по умолчанию 7)"
        echo "  keep-latest [N]       - То же что и clean [N]"
        echo "  help                  - Показать эту справку"
        echo ""
        echo "Примеры:"
        echo "  $0 list               - Показать все бэкапы"
        echo "  $0 clean 2            - Оставить только 2 последних бэкапа"
        echo "  $0 clean-old 3        - Удалить бэкапы старше 3 дней"
        ;;
    *)
        echo -e "${RED}❌ Неизвестная команда: $1${NC}"
        echo "Используйте '$0 help' для справки"
        exit 1
        ;;
esac
