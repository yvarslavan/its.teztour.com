@echo off
REM Скрипт для очистки временных файлов на Windows

echo Очистка временных файлов от предыдущих попыток исправления CSRF...
echo.

set deleted_count=0
set not_found_count=0

echo Проверка и удаление временных файлов:
echo ================================================================

REM Список файлов для удаления
call :delete_file "analyze_env_settings.py"
call :delete_file "create_fixed_env.py"
call :delete_file "debug_csrf_server.py"
call :delete_file "debug_errors.sh"
call :delete_file "disable_csrf_completely.py"
call :delete_file "final_csrf_fix.py"
call :delete_file "final_csrf_middleware_fix.py"
call :delete_file "final_disable_csrf.py"
call :delete_file "final_simple_fix.py"
call :delete_file "fix_app_config_error.py"
call :delete_file "fix_context_processor.py"
call :delete_file "fix_csrf_disabled.py"
call :delete_file "fix_csrf_template.py"
call :delete_file "fix_env_domain.py"
call :delete_file "fix_gunicorn_socket.sh"
call :delete_file "fix_server_csrf.py"
call :delete_file "fix_syntax_error.py"
call :delete_file "fix_template_csrf_token.py"
call :delete_file "quick_fix_csrf.py"
call :delete_file "restart_and_test.bat"
call :delete_file "restart_and_test.sh"
call :delete_file "restore_and_fix_indentation.py"
call :delete_file "restore_and_fix_simple.py"
call :delete_file "restore_from_git.py"
call :delete_file "setup_prod_dirs.sh"
call :delete_file "simple_fix_remove_context_processor.py"
call :delete_file "test_and_restart.sh"
call :delete_file "test_config.py"
call :delete_file "test_csrf.py"
call :delete_file "test_csrf_browser.py"
call :delete_file "test_csrf_simple.py"
call :delete_file "test_dev_csrf.py"
call :delete_file "ultimate_csrf_fix.py"
call :delete_file "QUICK_DEPLOY.sh"
call :delete_file "CSRF_FIX_INSTRUCTIONS.md"
call :delete_file "DEPLOYMENT_FIX.md"
call :delete_file "FINAL_CSRF_FIX.md"

echo.
echo ================================================================
echo Итого:
echo    Удалено файлов: %deleted_count%
echo    Пропущено (не найдено): %not_found_count%
echo.

echo Актуальные файлы (оставлены):
echo ================================================================
call :check_file "CSRF_SOLUTION.md"
call :check_file "CSRF_FIX_SUMMARY.md"
call :check_file "DEPLOYMENT_CHECKLIST.md"
call :check_file "QUICK_FIX.md"
call :check_file "test_csrf_production.py"
call :check_file "blog\__init__.py"
call :check_file "blog\user\routes.py"

echo.
echo ✅ Очистка завершена!
echo.
echo 📝 Следующие шаги:
echo    1. Проверьте изменения: git status
echo    2. Добавьте в git: git add .
echo    3. Закоммитьте: git commit -m "Fix: CSRF production issue"
echo    4. Отправьте на сервер: git push origin main
echo    5. Разверните на сервере (см. QUICK_FIX.md)
echo.

pause
exit /b

:delete_file
if exist %~1 (
    del %~1
    echo ✅ Удален: %~1
    set /a deleted_count+=1
) else (
    echo ⏭️  Пропущен: %~1 ^(не найден^)
    set /a not_found_count+=1
)
exit /b

:check_file
if exist %~1 (
    echo ✓ %~1
) else (
    echo ✗ %~1 ^(НЕ НАЙДЕН!^)
)
exit /b
