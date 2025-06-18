@echo off
echo ====================================
echo    FLASK DEVELOPMENT SERVER
echo ====================================
echo Запуск сервера в режиме разработки...
echo.

REM Активируем виртуальное окружение если оно есть
if exist "venv\Scripts\activate.bat" (
    echo Активация виртуального окружения...
    call venv\Scripts\activate.bat
)

REM Устанавливаем переменные окружения для режима разработки
set FLASK_APP=run_dev.py
set FLASK_ENV=development
set FLASK_DEBUG=1
set FLASK_RUN_HOST=127.0.0.1
set FLASK_RUN_PORT=5000

echo.
echo Сервер будет доступен по адресу:
echo   ^> http://localhost:5000
echo   ^> http://127.0.0.1:5000
echo.
echo Нажмите Ctrl+C для остановки сервера
echo ====================================
echo.

REM Запуск Flask с правильными настройками
flask run

pause
