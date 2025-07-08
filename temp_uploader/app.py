#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 ВРЕМЕННОЕ ПРИЛОЖЕНИЕ ДЛЯ ДЕПЛОЯ FLASK HELPDESK
"""

import os
import subprocess
import tarfile
from flask import Flask, request, jsonify, render_template_string
from werkzeug.utils import secure_filename
import shutil
import stat

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# HTML шаблон (встроенный)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Flask Helpdesk Deployment Uploader</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { color: #333; text-align: center; }
        .upload-area {
            border: 2px dashed #ccc;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            margin: 20px 0;
            background: #fafafa;
        }
        .upload-area:hover {
            border-color: #007bff;
            background: #f0f8ff;
        }
        input[type="file"] {
            margin: 20px 0;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            width: 100%;
        }
        .btn {
            background: #007bff;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        .btn:hover { background: #0056b3; }
        .instructions {
            background: #e9ecef;
            padding: 20px;
            border-radius: 5px;
            margin-top: 20px;
        }
        .code {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 3px;
            font-family: monospace;
            border-left: 4px solid #007bff;
            margin: 10px 0;
            white-space: pre-wrap;
        }
        .status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 5px;
            font-weight: bold;
        }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Flask Helpdesk Deployment Uploader</h1>

        <div class="upload-area">
            <h3>📦 Загрузите файл деплоя</h3>
            <p>Выберите файл <strong>deployment_manual_updated.tar.gz</strong></p>
            <form id="uploadForm" enctype="multipart/form-data">
                <input type="file" id="fileInput" name="file" accept=".tar.gz,.tar,.gz" required />
                <button type="submit" class="btn">🚀 Загрузить и деплоить</button>
            </form>
        </div>

        <div id="status"></div>

        <div class="instructions">
            <h3>📋 Что происходит при загрузке:</h3>
            <ol>
                <li><strong>Загрузка файла</strong> в /tmp/</li>
                <li><strong>Остановка старого сервиса</strong> flask-helpdesk</li>
                <li><strong>Распаковка в /opt/www</strong></li>
                <li><strong>Установка зависимостей</strong> pip install</li>
                <li><strong>Настройка прав доступа</strong></li>
                <li><strong>Запуск нового сервиса</strong></li>
                <li><strong>Восстановление SSH ключей</strong></li>
            </ol>

            <h3>🔧 Ручные команды (если что-то пошло не так):</h3>
            <div class="code">cd /tmp/
sudo systemctl stop flask-helpdesk
cd /opt/www
sudo tar -xzf /tmp/deployment_manual_updated.tar.gz
sudo pip install -r requirements.txt
sudo chown -R deploy:deploy /opt/www
sudo chmod +x /opt/www/restore_ssh.sh
sudo systemctl start flask-helpdesk
sudo systemctl status flask-helpdesk</div>
        </div>
    </div>

    <script>
        document.getElementById('uploadForm').addEventListener('submit', function(e) {
            e.preventDefault();
            uploadFile();
        });

        function uploadFile() {
            const fileInput = document.getElementById('fileInput');
            const file = fileInput.files[0];
            const statusDiv = document.getElementById('status');

            if (!file) {
                showStatus('Пожалуйста, выберите файл для загрузки', 'error');
                return;
            }

            if (!file.name.includes('.tar.gz')) {
                showStatus('Пожалуйста, выберите файл .tar.gz', 'error');
                return;
            }

            const formData = new FormData();
            formData.append('file', file);

            // Показать прогресс
            const button = document.querySelector('.btn');
            button.disabled = true;
            button.innerHTML = '⏳ Загружаем и деплоим...';
            showStatus('⏳ Загружаем файл и выполняем деплой...', 'info');

            fetch('/upload-deploy', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showStatus('✅ Деплой выполнен успешно!\\n\\n' + data.message, 'success');
                    button.innerHTML = '✅ Готово!';
                } else {
                    showStatus('❌ Ошибка: ' + data.message, 'error');
                    button.disabled = false;
                    button.innerHTML = '🚀 Загрузить и деплоить';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showStatus('❌ Ошибка загрузки: ' + error.message, 'error');
                button.disabled = false;
                button.innerHTML = '🚀 Загрузить и деплоить';
            });
        }

        function showStatus(message, type) {
            const statusDiv = document.getElementById('status');
            statusDiv.innerHTML = '<div class="status ' + type + '">' + message + '</div>';
        }
    </script>
</body>
</html>
"""

def run_command(command, description):
    """Выполнить команду и вернуть результат"""
    try:
        print(f"🔧 {description}")
        print(f"   Команда: {command}")

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )

        print(f"   Код выхода: {result.returncode}")
        print(f"   Вывод: {result.stdout}")
        if result.stderr:
            print(f"   Ошибки: {result.stderr}")

        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Команда выполнялась слишком долго (timeout 300s)"
    except Exception as e:
        return False, "", str(e)

@app.route('/')
def index():
    """Главная страница с формой загрузки"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload-deploy', methods=['POST'])
def upload_deploy():
    """Загрузка файла и выполнение деплоя"""
    try:
        # Проверяем файл
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'Файл не выбран'})

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Файл не выбран'})

        if not file.filename.endswith('.tar.gz'):
            return jsonify({'success': False, 'message': 'Неверный формат файла. Нужен .tar.gz'})

        # Сохраняем файл
        filename = secure_filename(file.filename)
        upload_path = f'/tmp/{filename}'
        file.save(upload_path)

        print(f"✅ Файл сохранен: {upload_path}")

        deployment_log = []

        # 1. Остановка старого сервиса
        success, stdout, stderr = run_command(
            'sudo systemctl stop flask-helpdesk',
            'Остановка Flask Helpdesk сервиса'
        )
        deployment_log.append(f"🛑 Остановка сервиса: {'✅' if success else '❌'}")
        if stderr and 'not found' not in stderr.lower():
            deployment_log.append(f"   Ошибка: {stderr}")

        # 2. Создание бэкапа (если существует)
        if os.path.exists('/opt/www'):
            success, stdout, stderr = run_command(
                f'sudo cp -r /opt/www /opt/www_backup_{int(time.time())}',
                'Создание бэкапа'
            )
            deployment_log.append(f"💾 Бэкап: {'✅' if success else '❌'}")

        # 3. Создание директории
        success, stdout, stderr = run_command(
            'sudo mkdir -p /opt/www',
            'Создание директории /opt/www'
        )
        deployment_log.append(f"📁 Создание директории: {'✅' if success else '❌'}")

        # 4. Распаковка архива
        success, stdout, stderr = run_command(
            f'cd /opt/www && sudo tar -xzf {upload_path}',
            'Распаковка архива'
        )
        deployment_log.append(f"📦 Распаковка: {'✅' if success else '❌'}")
        if not success:
            deployment_log.append(f"   Ошибка: {stderr}")
            return jsonify({
                'success': False,
                'message': 'Ошибка распаковки архива: ' + stderr
            })

        # 5. Установка зависимостей
        if os.path.exists('/opt/www/requirements.txt'):
            success, stdout, stderr = run_command(
                'cd /opt/www && sudo pip install -r requirements.txt',
                'Установка зависимостей'
            )
            deployment_log.append(f"📋 Зависимости: {'✅' if success else '❌'}")

        # 6. Настройка прав доступа
        success, stdout, stderr = run_command(
            'sudo chown -R deploy:deploy /opt/www',
            'Настройка прав доступа'
        )
        deployment_log.append(f"🔐 Права доступа: {'✅' if success else '❌'}")

        # 7. Копирование systemd сервиса
        if os.path.exists('/opt/www/flask-helpdesk.service'):
            success, stdout, stderr = run_command(
                'sudo cp /opt/www/flask-helpdesk.service /etc/systemd/system/',
                'Установка systemd сервиса'
            )
            deployment_log.append(f"⚙️ Systemd сервис: {'✅' if success else '❌'}")

            # Перезагрузка systemd
            run_command('sudo systemctl daemon-reload', 'Перезагрузка systemd')

        # 8. Запуск сервиса
        success, stdout, stderr = run_command(
            'sudo systemctl start flask-helpdesk',
            'Запуск Flask Helpdesk сервиса'
        )
        deployment_log.append(f"🚀 Запуск сервиса: {'✅' if success else '❌'}")

        # 9. Включение автозапуска
        success, stdout, stderr = run_command(
            'sudo systemctl enable flask-helpdesk',
            'Включение автозапуска'
        )
        deployment_log.append(f"🔄 Автозапуск: {'✅' if success else '❌'}")

        # 10. Проверка статуса
        success, stdout, stderr = run_command(
            'sudo systemctl status flask-helpdesk',
            'Проверка статуса сервиса'
        )
        deployment_log.append(f"📊 Статус сервиса: {'✅' if success else '❌'}")

        # 11. Восстановление SSH ключей
        if os.path.exists('/opt/www/restore_ssh.sh'):
            success, stdout, stderr = run_command(
                'chmod +x /opt/www/restore_ssh.sh && /opt/www/restore_ssh.sh',
                'Восстановление SSH ключей'
            )
            deployment_log.append(f"🔑 SSH ключи: {'✅' if success else '❌'}")

        # Очистка временного файла
        try:
            os.remove(upload_path)
        except:
            pass

        message = "\\n".join(deployment_log)
        message += "\\n\\n🎉 Деплой завершен! Проверьте http://its.tez-tour.com"

        return jsonify({
            'success': True,
            'message': message
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка деплоя: {str(e)}'
        })

@app.route('/health')
def health():
    """Проверка работоспособности"""
    return jsonify({'status': 'ok', 'service': 'deployment_uploader'})

if __name__ == '__main__':
    import time
    print("🚀 Запуск временного деплой-сервера...")
    print("📡 Откройте в браузере: http://its.tez-tour.com:5000")
    print("📁 Загрузите файл: deployment_manual_updated.tar.gz")
    print("⚠️  После деплоя этот сервер автоматически остановится")

    # Запуск на всех интерфейсах, порт 5000
    app.run(host='0.0.0.0', port=5000, debug=False)
