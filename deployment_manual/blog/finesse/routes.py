import os
import json
from flask import Blueprint, render_template, jsonify, current_app, request, Response
from flask_cors import CORS
import requests

finesse = Blueprint(
    "finesse", __name__, static_folder="static", template_folder="templates"
)
CORS(finesse, origins=["http://127.0.0.1:5000", "http://localhost:5000"])
# Разрешить CORS для указанных URL
CORS(
    finesse,
    resources={
        r"/finesse/call-transfer": {"origins": ["*"]},
        r"/finesse/config": {"origins": ["*"]},
        r"/finesse/proxy/dialogs": {"origins": ["*"]},
    },
)


@finesse.route("/call-transfer")
def call_transfer():
    return render_template("finesse/callTransfer.html")


@finesse.route("/config")
def get_config():
    try:
        config_path = os.path.join(
            current_app.root_path, "finesse", "static", "config", "config.json"
        )
        print(f"Путь к конфигурационному файлу: {config_path}")  # Для отладки
        with open(config_path, "r", encoding="utf-8") as config_file:
            config_data = json.load(config_file)
        return jsonify(config_data)
    except FileNotFoundError:
        print("Конфигурационный файл не найден")  # Для отладки
        return jsonify({"error": "Configuration file not found"}), 404
    except json.JSONDecodeError:
        print("Некорректный формат конфигурационного файла")  # Для отладки
        return jsonify({"error": "Invalid configuration file"}), 500
    except Exception as e:
        print(f"Ошибка: {str(e)}")  # Для отладки
        return jsonify({"error": str(e)}), 500


@finesse.route("/proxy/dialogs", methods=["GET"])
def proxy_dialogs():
    finesse_url = "http://uccx1.teztour.com:8082/finesse/api/User/test/Dialogs"
    auth = ("test", "test")

    try:
        response = requests.get(finesse_url, auth=auth, timeout=10)
        return Response(
            response.text, content_type="application/xml", status=response.status_code
        )
    except requests.Timeout:
        return jsonify({"error": "Request timed out"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@finesse.route("/proxy/transfer", methods=["PUT", "OPTIONS"])
def proxy_transfer():
    if request.method == "OPTIONS":
        response = current_app.make_default_options_response()
        response.headers["Access-Control-Allow-Methods"] = (
            "PUT"
        )
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    try:
        data = request.json
        call_id = data.get("callId")
        destination = data.get("destination")

        if not call_id or not destination:
            return jsonify({"error": "Нет callId"}), 400

        finesse_url = (
            f"http://uccx1.teztour.com:8082/finesse/api/User/test/Dialogs/{call_id}"
        )
        auth = ("test", "test")
        # Используем JSON как payload и указываем заголовки соответствующие
        transfer_payload = {
            "Dialog": {"targetMediaAddress": destination, "requestedAction": "TRANSFER"}
        }

        finesse_response = requests.put(
            finesse_url,
            json=transfer_payload,  # Передача данных в JSON
            auth=auth,
            timeout=10,
            headers={
                "Content-Type": "application/json"
            },  # Добавлен заголовок для Finesse API
        )
        # Вернем ответ с корректным статусом и контент-типом
        return Response(
            finesse_response.text,
            content_type="application/xml",
            status=finesse_response.status_code,
        )

    except requests.Timeout:
        return jsonify({"error": "Request to Finesse timed out"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500
