#!/bin/bash
# Скрипт для очистки временных файлов, созданных при попытках исправления CSRF

echo "🧹 Очистка временных файлов от предыдущих попыток исправления CSRF..."
echo ""

# Список файлов для удаления
TEMP_FILES=(
    "analyze_env_settings.py"
    "create_fixed_env.py"
    "debug_csrf_server.py"
    "debug_errors.sh"
    "disable_csrf_completely.py"
    "final_csrf_fix.py"
    "final_csrf_middleware_fix.py"
    "final_disable_csrf.py"
    "final_simple_fix.py"
    "fix_app_config_error.py"
    "fix_context_processor.py"
    "fix_csrf_disabled.py"
    "fix_csrf_template.py"
    "fix_env_domain.py"
    "fix_gunicorn_socket.sh"
    "fix_server_csrf.py"
    "fix_syntax_error.py"
    "fix_template_csrf_token.py"
    "quick_fix_csrf.py"
    "restart_and_test.bat"
    "restart_and_test.sh"
    "restore_and_fix_indentation.py"
    "restore_and_fix_simple.py"
    "restore_from_git.py"
    "setup_prod_dirs.sh"
    "simple_fix_remove_context_processor.py"
    "test_and_restart.sh"
    "test_config.py"
    "test_csrf.py"
    "test_csrf_browser.py"
    "test_csrf_simple.py"
    "test_dev_csrf.py"
    "ultimate_csrf_fix.py"
    "QUICK_DEPLOY.sh"
    "CSRF_FIX_INSTRUCTIONS.md"
    "DEPLOYMENT_FIX.md"
    "FINAL_CSRF_FIX.md"
)

# Счетчик удаленных файлов
deleted_count=0
not_found_count=0

echo "Проверка и удаление временных файлов:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for file in "${TEMP_FILES[@]}"; do
    if [ -f "$file" ]; then
        rm "$file"
        echo "✅ Удален: $file"
        ((deleted_count++))
    else
        echo "⏭️  Пропущен: $file (не найден)"
        ((not_found_count++))
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Итого:"
echo "   ✅ Удалено файлов: $deleted_count"
echo "   ⏭️  Пропущено (не найдено): $not_found_count"
echo ""

# Список файлов, которые нужно ОСТАВИТЬ (актуальные исправления)
echo "📂 Актуальные файлы (оставлены):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
KEEP_FILES=(
    "CSRF_SOLUTION.md"
    "CSRF_FIX_SUMMARY.md"
    "DEPLOYMENT_CHECKLIST.md"
    "QUICK_FIX.md"
    "test_csrf_production.py"
    "blog/__init__.py"
    "blog/user/routes.py"
)

for file in "${KEEP_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "✗ $file (НЕ НАЙДЕН!)"
    fi
done

echo ""
echo "✅ Очистка завершена!"
echo ""
echo "📝 Следующие шаги:"
echo "   1. Проверьте изменения: git status"
echo "   2. Добавьте в git: git add ."
echo "   3. Закоммитьте: git commit -m 'Fix: CSRF production issue'"
echo "   4. Отправьте на сервер: git push origin main"
echo "   5. Разверните на сервере (см. QUICK_FIX.md)"
