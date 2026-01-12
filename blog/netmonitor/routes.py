import platform
import subprocess
import time
import json
import logging
from datetime import datetime
from flask import render_template, request, jsonify, current_app, Blueprint

# Создаем Blueprint вместо импорта
netmonitor = Blueprint("netmonitor", __name__)

# Настройка логгирования
logging.basicConfig(level=logging.DEBUG)
# Импортируем декораторы для защиты отладочных эндпоинтов
from blog.utils.decorators import debug_only, development_only, admin_required_in_production
logger = logging.getLogger(__name__)

# Глобальные переменные для хранения истории пингов
ping_history = []  # История пингов
max_history_length = 100  # Максимальная длина истории

# Настройки пинга
PING_TARGETS = {
    "finesse": "uccx1.teztour.com"  # Сервер Finesse
}

DEFAULT_TARGET = "finesse"  # Цель для пинга по умолчанию


def ping(host):
    """
    Выполняет пинг до указанного хоста и возвращает результаты
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    start_time = time.time()

    try:
        # Определяем параметры команды ping в зависимости от ОС
        if platform.system().lower() == "windows":
            command = ["ping", "-n", "1", "-w", "1000", host]
        else:
            command = ["ping", "-c", "1", "-W", "1", host]

        # Выполняем команду
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()

        # Получаем время выполнения и статус
        elapsed_time = int((time.time() - start_time) * 1000)  # в миллисекундах
        success = process.returncode == 0

        # Формируем результат
        result = {
            "timestamp": timestamp,
            "target": host,
            "success": success,
            "time_ms": elapsed_time if success else -1,
            "error": stderr.decode("utf-8", errors="ignore") if stderr else None
        }

        # Добавляем в историю
        ping_history.append(result)
        # Ограничиваем размер истории
        if len(ping_history) > max_history_length:
            ping_history.pop(0)

        return result

    except Exception as e:
        logger.error(f"Ошибка при выполнении пинга: {str(e)}")
        return {
            "timestamp": timestamp,
            "target": host,
            "success": False,
            "time_ms": -1,
            "error": str(e)
        }


@netmonitor.route("/network-monitor")
@admin_required_in_production
def network_monitor():
    """Страница мониторинга сети"""
    return render_template(
        "network_monitor.html",
        title="Мониторинг сети",
        ping_targets=PING_TARGETS
    )


@netmonitor.route("/api/ping", methods=["GET"])
@admin_required_in_production
def api_ping():
    """API для выполнения пинга"""
    target = request.args.get("target", DEFAULT_TARGET)

    # Получаем целевой хост из настроек
    host = PING_TARGETS.get(target, PING_TARGETS[DEFAULT_TARGET])

    # Выполняем пинг
    result = ping(host)

    return jsonify(result)


@netmonitor.route("/api/ping-history", methods=["GET"])
@admin_required_in_production
def api_ping_history():
    """API для получения истории пингов"""
    target = request.args.get("target", DEFAULT_TARGET)
    limit = request.args.get("limit", 50, type=int)

    # Фильтруем историю по целевому хосту
    host = PING_TARGETS.get(target, PING_TARGETS[DEFAULT_TARGET])
    filtered_history = [ping for ping in ping_history if ping["target"] == host]

    # Ограничиваем количество записей
    limited_history = filtered_history[-limit:] if limit > 0 else filtered_history

    return jsonify({
        "target": target,
        "host": host,
        "history": limited_history
    })


@netmonitor.route("/api/status", methods=["GET"])
@admin_required_in_production
def api_status():
    """API для получения текущего статуса соединения"""
    statuses = {}

    for target_name, target_host in PING_TARGETS.items():
        # Выполняем пинг для каждой цели
        result = ping(target_host)

        # Определяем статус на основе успешности и времени пинга
        if result["success"]:
            if result["time_ms"] < 100:
                status = "excellent"
            elif result["time_ms"] < 200:
                status = "good"
            elif result["time_ms"] < 500:
                status = "average"
            else:
                status = "poor"
        else:
            status = "disconnected"

        statuses[target_name] = {
            "status": status,
            "time_ms": result["time_ms"],
            "timestamp": result["timestamp"],
            "success": result["success"]
        }

    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "targets": statuses
    })
