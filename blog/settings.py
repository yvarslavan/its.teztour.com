import os
from pathlib import Path
import sys

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_dir = os.path.join(base_dir, 'blog', 'db')
os.makedirs(db_dir, exist_ok=True)

class Config:
    SECRET_KEY = os.urandom(36)
    SESSION_TYPE = 'filesystem'
    # SQLite соединение
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(db_dir, "blog.db")}'

    # Проверяем наличие переменных и устанавливаем безопасные значения для разработки,
    # чтобы избежать ошибок при импорте модулей

    # Oracle CRM соединение
    _oracle_crm = os.environ.get("SQLALCHEMY_DATABASE_URI_ORACLE_CRM")
    if _oracle_crm:
        SQLALCHEMY_DATABASE_URI_ORACLE_CRM = _oracle_crm
    else:
        print("ВНИМАНИЕ: SQLALCHEMY_DATABASE_URI_ORACLE_CRM не установлена!")
        # Фиктивное соединение для безопасного импорта (не будет использоваться)
        SQLALCHEMY_DATABASE_URI_ORACLE_CRM = "sqlite:///db/dummy_oracle.db"

    # Oracle SALES соединение
    _oracle_sales = os.environ.get("SQLALCHEMY_SALES_SCHEMA_URI_ORACLE_SALES")
    if _oracle_sales:
        SQLALCHEMY_SALES_SCHEMA_URI_ORACLE_SALES = _oracle_sales
    else:
        print("ВНИМАНИЕ: SQLALCHEMY_SALES_SCHEMA_URI_ORACLE_SALES не установлена!")
        # Фиктивное соединение для безопасного импорта (не будет использоваться)
        SQLALCHEMY_SALES_SCHEMA_URI_ORACLE_SALES = "sqlite:///db/dummy_sales.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = os.environ.get("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # VAPID ключи для браузерных пуш-уведомлений
    try:
        from blog.config.vapid_keys import VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY, VAPID_CLAIMS
    except ImportError:
        VAPID_PUBLIC_KEY = os.environ.get(
            "VAPID_PUBLIC_KEY",
            "BNTSbYqtXosdptrmO9bfxysrYft2H-JsFWqHB8oA0Ex_X6jEDjfF0YndzMPAN9SJP8uhzmZn6g_xdDD17aZaxNc"
        )
        VAPID_PRIVATE_KEY = os.environ.get(
            "VAPID_PRIVATE_KEY",
            "MxKfyWZ6RF1WOZ0dWE5h99Z0pY5G997MeG93PyOO2qA"
        )
        VAPID_CLAIMS = {
            "sub": "mailto:y.varslavan@tez-tour.com"
        }
