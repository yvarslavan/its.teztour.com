from flask_sqlalchemy import SQLAlchemy

# Создаем экземпляр SQLAlchemy с явными настройками
db = SQLAlchemy(
    engine_options={
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
)
