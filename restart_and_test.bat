@echo off
REM Скрипт для перезапуска сервиса и тестирования CSRF

echo 🔄 Перезапуск сервиса flask-helpdesk...
net stop flask-helpdesk
net start flask-helpdesk

echo ⏳ Ожидание запуска сервиса...
timeout /t 5 /nobreak

echo 🧪 Запуск теста CSRF...
python test_csrf.py

echo ✅ Скрипт завершен
pause
