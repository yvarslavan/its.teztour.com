@echo off
rem ============================================================================
rem Простой скрипт очистки временных файлов для Windows
rem Автор: Flask Helpdesk Development Team
rem Версия: 1.0 (упрощенная)
rem ============================================================================

chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ════════════════════════════════════════════════════════════
echo            🧹 БЫСТРАЯ ОЧИСТКА СРЕДЫ РАЗРАБОТКИ
echo ════════════════════════════════════════════════════════════
echo.

rem Подсчет файлов для удаления
set /a file_count=0
set /a dir_count=0

echo 🔍 Сканирование временных файлов...
echo.

rem Поиск и подсчет файлов
for /r . %%f in (*.tmp *.temp *.bak *.backup *.old *.log *.pyc *.pyo *.cache) do (
    if exist "%%f" (
        set /a file_count+=1
        echo   📄 %%~nxf
    )
)

echo.
echo 🔍 Сканирование временных папок...
echo.

rem Поиск папок __pycache__
for /f "delims=" %%d in ('dir /b /s /a:d __pycache__ 2^>nul') do (
    set /a dir_count+=1
    echo   📂 %%d
)

rem Поиск папок .vs
for /f "delims=" %%d in ('dir /b /s /a:d .vs 2^>nul') do (
    set /a dir_count+=1
    echo   📂 %%d
)

rem Поиск папок flask_session
for /f "delims=" %%d in ('dir /b /s /a:d flask_session 2^>nul') do (
    set /a dir_count+=1
    echo   📂 %%d
)

echo.
echo ════════════════════════════════════════════════════════════
echo 📊 НАЙДЕНО ДЛЯ ОЧИСТКИ:
echo    Файлов: !file_count!
echo    Папок: !dir_count!
echo ════════════════════════════════════════════════════════════

if !file_count! equ 0 if !dir_count! equ 0 (
    echo.
    echo ✨ Временные файлы не найдены! Среда разработки уже чистая.
    echo.
    pause
    exit /b 0
)

echo.
echo ⚠️  ВНИМАНИЕ: Это действие необратимо!
set /p confirm="💬 Продолжить очистку? [Y/N]: "

if /i not "%confirm%"=="Y" if /i not "%confirm%"=="Yes" if /i not "%confirm%"=="Да" (
    echo ❌ Очистка отменена пользователем.
    pause
    exit /b 0
)

echo.
echo 🔄 ВЫПОЛНЕНИЕ ОЧИСТКИ...
echo ════════════════════════════════════════════════════════════

rem Счетчики успешных удалений
set /a deleted_files=0
set /a deleted_dirs=0
set /a failed_count=0

echo.
echo 🗑️  Удаление временных файлов...

rem Удаление файлов
for /r . %%f in (*.tmp *.temp *.bak *.backup *.old *.log *.pyc *.pyo *.cache) do (
    if exist "%%f" (
        del /f /q "%%f" 2>nul
        if !errorlevel! equ 0 (
            set /a deleted_files+=1
            echo   ✅ %%~nxf
        ) else (
            set /a failed_count+=1
            echo   ❌ Ошибка при удалении %%~nxf
        )
    )
)

echo.
echo 📁 Удаление временных папок...

rem Удаление папок __pycache__
for /f "delims=" %%d in ('dir /b /s /a:d __pycache__ 2^>nul') do (
    rd /s /q "%%d" 2>nul
    if !errorlevel! equ 0 (
        set /a deleted_dirs+=1
        echo   ✅ __pycache__
    ) else (
        set /a failed_count+=1
        echo   ❌ Ошибка при удалении %%d
    )
)

rem Удаление папок .vs
for /f "delims=" %%d in ('dir /b /s /a:d .vs 2^>nul') do (
    rd /s /q "%%d" 2>nul
    if !errorlevel! equ 0 (
        set /a deleted_dirs+=1
        echo   ✅ .vs
    ) else (
        set /a failed_count+=1
        echo   ❌ Ошибка при удалении %%d
    )
)

rem Удаление папок flask_session (только файлы внутри)
for /f "delims=" %%d in ('dir /b /s /a:d flask_session 2^>nul') do (
    echo   🧹 Очистка flask_session...
    del /f /q "%%d\*.*" 2>nul
    if !errorlevel! equ 0 (
        echo   ✅ Файлы сессий удалены
    ) else (
        echo   ⚠️  Некоторые файлы сессий не удалены
    )
)

echo.
echo ════════════════════════════════════════════════════════════
echo 📊 ФИНАЛЬНЫЙ ОТЧЕТ
echo ════════════════════════════════════════════════════════════
echo Файлов удалено: !deleted_files!/!file_count!
echo Папок удалено: !deleted_dirs!/!dir_count!
echo Ошибок: !failed_count!

if !failed_count! equ 0 (
    echo ✅ Очистка среды разработки завершена успешно!
) else (
    echo ⚠️  Очистка завершена с ошибками. Проверьте права доступа.
)

echo ════════════════════════════════════════════════════════════
echo.
echo 🎯 Для дополнительных возможностей используйте:
echo    cleanup_dev_environment.ps1 -Verbose
echo.
pause
