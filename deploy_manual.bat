@echo off
chcp 65001 >nul
echo.
echo 🚀 Ручной деплой Flask Helpdesk на Red Hat сервер
echo ================================================
echo.

REM Проверяем текущую директорию
echo 📁 Текущая директория: %CD%
echo.

REM Создаем папку для деплоя
echo 📦 Создаем папку deployment_manual...
if exist deployment_manual rmdir /s /q deployment_manual
mkdir deployment_manual

echo.
echo 📋 Копируем файлы проекта:
echo.

REM Копируем основные файлы
if exist app.py (
    copy app.py deployment_manual\ >nul
    echo ✅ app.py
) else (
    echo ⚠️ app.py не найден
)

if exist requirements.txt (
    copy requirements.txt deployment_manual\ >nul
    echo ✅ requirements.txt
) else (
    echo ⚠️ requirements.txt не найден
)

if exist config.ini (
    copy config.ini deployment_manual\ >nul
    echo ✅ config.ini
) else (
    echo ⚠️ config.ini не найден
)

REM Копируем все Python файлы
echo 📄 Копируем Python файлы...
for %%f in (*.py) do (
    copy "%%f" deployment_manual\ >nul 2>&1
)
echo ✅ Python файлы скопированы

echo.
echo 📂 Копируем директории:

REM Копируем директории если есть
if exist blog (
    xcopy /E /I /Q blog deployment_manual\blog >nul 2>&1
    echo ✅ blog/
) else (
    echo ℹ️ blog/ не найдена
)

if exist static (
    xcopy /E /I /Q static deployment_manual\static >nul 2>&1
    echo ✅ static/
) else (
    echo ℹ️ static/ не найдена
)

if exist templates (
    xcopy /E /I /Q templates deployment_manual\templates >nul 2>&1
    echo ✅ templates/
) else (
    echo ℹ️ templates/ не найдена
)

if exist migrations (
    xcopy /E /I /Q migrations deployment_manual\migrations >nul 2>&1
    echo ✅ migrations/
) else (
    echo ℹ️ migrations/ не найдена
)

echo.
echo 🔧 Копируем конфигурационные файлы:

if exist flask-helpdesk.service.redhat (
    copy flask-helpdesk.service.redhat deployment_manual\flask-helpdesk.service >nul
    echo ✅ flask-helpdesk.service
) else (
    echo ℹ️ flask-helpdesk.service.redhat не найден
)

if exist flask-helpdesk.nginx.conf (
    copy flask-helpdesk.nginx.conf deployment_manual\ >nul
    echo ✅ flask-helpdesk.nginx.conf
) else (
    echo ℹ️ flask-helpdesk.nginx.conf не найден
)

echo.
echo 📦 Создаем архив...

REM Проверяем наличие 7-Zip
if exist "C:\Program Files\7-Zip\7z.exe" (
    "C:\Program Files\7-Zip\7z.exe" a -ttar deployment_manual.tar deployment_manual\* >nul
    "C:\Program Files\7-Zip\7z.exe" a -tgzip deployment_manual.tar.gz deployment_manual.tar >nul
    del deployment_manual.tar >nul 2>&1
    echo ✅ Архив deployment_manual.tar.gz создан с помощью 7-Zip
) else if exist "C:\Program Files (x86)\7-Zip\7z.exe" (
    "C:\Program Files (x86)\7-Zip\7z.exe" a -ttar deployment_manual.tar deployment_manual\* >nul
    "C:\Program Files (x86)\7-Zip\7z.exe" a -tgzip deployment_manual.tar.gz deployment_manual.tar >nul
    del deployment_manual.tar >nul 2>&1
    echo ✅ Архив deployment_manual.tar.gz создан с помощью 7-Zip
) else (
    echo ⚠️ 7-Zip не найден, создайте архив deployment_manual.tar.gz вручную
    echo 📋 Содержимое папки deployment_manual:
    dir deployment_manual
)

echo.
echo 📊 Статистика:
if exist deployment_manual.tar.gz (
    for %%A in (deployment_manual.tar.gz) do echo 📦 Размер архива: %%~zA байт
)
echo 📁 Файлов в deployment_manual:
dir deployment_manual /B | find /C /V ""

echo.
echo ================================================================
echo 🎉 ПОДГОТОВКА К ДЕПЛОЮ ЗАВЕРШЕНА!
echo ================================================================
echo.
echo 🔧 СЛЕДУЮЩИЕ ШАГИ:
echo.
echo 1️⃣ Передайте файл на сервер:
echo    scp deployment_manual.tar.gz deploy@10.7.74.252:/tmp/
echo.
echo 2️⃣ Подключитесь к серверу:
echo    ssh deploy@10.7.74.252
echo.
echo 3️⃣ Выполните деплой на сервере:
echo    sudo systemctl stop its.teztour.com
echo    cd /opt/www/its.teztour.com/
echo    sudo tar -xzf /tmp/deployment_manual.tar.gz
echo    sudo chown -R deploy:deploy /opt/www/its.teztour.com/
echo    sudo chmod -R 755 /opt/www/its.teztour.com/
echo    sudo systemctl start its.teztour.com
echo    sudo systemctl status its.teztour.com
echo.
echo 4️⃣ Проверьте сайт:
echo    curl -I http://its.tez-tour.com
echo.
echo 📋 Подробные инструкции в файле: MANUAL_DEPLOY.md
echo.
echo ✅ Готово к деплою!
echo.
pause
