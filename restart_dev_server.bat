@echo off
echo === Перезапуск сервера разработки с очисткой кэша ===
echo.

REM Останавливаем все процессы Python
echo Останавливаем текущие процессы Python...
taskkill /F /IM python.exe 2>nul

REM Очищаем кэш Python
echo Очищаем кэш Python...
rd /s /q __pycache__ 2>nul
rd /s /q blog\__pycache__ 2>nul
rd /s /q blog\static\__pycache__ 2>nul

REM Удаляем скомпилированные файлы
echo Удаляем скомпилированные файлы...
del /s /q *.pyc 2>nul

REM Очищаем временные файлы Flask
echo Очищаем временные файлы Flask...
rd /s /q flask_session 2>nul

REM Устанавливаем переменные окружения для отключения кэша
echo Настраиваем окружение...
set FLASK_ENV=development
set FLASK_DEBUG=1
set PYTHONDONTWRITEBYTECODE=1

REM Дополнительные переменные для отключения всех видов кэша
set FLASK_TEMPLATES_AUTO_RELOAD=1
set TEMPLATES_AUTO_RELOAD=1

REM Очищаем кэш Jinja шаблонов
echo Очищаем кэш Jinja шаблонов...
rd /s /q blog\__pycache__ 2>nul
del /s /q blog\*.pyc 2>nul

REM Запускаем сервер
echo.
echo Запускаем сервер разработки...
echo Сервер будет доступен по адресу: http://localhost:5000
echo.
echo Для применения изменений CSS:
echo 1. Используйте Ctrl+F5 в браузере для жесткой перезагрузки
echo 2. Или нажмите кнопку "Обновить CSS" внизу справа на странице
echo.
echo Нажмите Ctrl+C для остановки сервера
echo.

REM Активируем виртуальное окружение и запускаем сервер
call venv\Scripts\activate && python wsgi.py
