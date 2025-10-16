import time
import logging
from contextlib import contextmanager
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship, aliased, scoped_session
from sqlalchemy.exc import OperationalError, DatabaseError
from config import get  # Исправленный импорт
import configparser
from configparser import ConfigParser
import os

# Настройка логирования
logger = logging.getLogger(__name__)

class DatabaseConnectionManager:
    """Менеджер подключений к базе данных с обработкой ошибок и повторными попытками"""

    def __init__(self, max_retries=3, retry_delay=1.0, backoff_factor=2.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor
        self._connection_errors = {}

    def execute_with_retry(self, operation, session_factory, operation_name="database operation"):
        """
        Выполняет операцию с базой данных с повторными попытками

        Args:
            operation: Функция для выполнения (принимает session как аргумент)
            session_factory: Фабрика сессий
            operation_name: Название операции для логирования

        Returns:
            Результат операции или None в случае неудачи
        """
        last_exception = None
        delay = self.retry_delay

        for attempt in range(self.max_retries + 1):
            try:
                session = session_factory()
                try:
                    result = operation(session)
                    # Сброс счетчика ошибок при успешном выполнении
                    if operation_name in self._connection_errors:
                        del self._connection_errors[operation_name]
                    return result
                finally:
                    session.close()

            except (OperationalError, DatabaseError) as e:
                last_exception = e
                error_code = getattr(e.orig, 'errno', None) if hasattr(e, 'orig') else None

                # Увеличиваем счетчик ошибок
                self._connection_errors[operation_name] = self._connection_errors.get(operation_name, 0) + 1

                if attempt < self.max_retries:
                    logger.warning(
                        f"Попытка {attempt + 1}/{self.max_retries + 1} для {operation_name} неудачна. "
                        f"Ошибка: {str(e)}. Повтор через {delay:.1f}с"
                    )
                    time.sleep(delay)
                    delay *= self.backoff_factor
                else:
                    logger.error(
                        f"Все попытки ({self.max_retries + 1}) для {operation_name} исчерпаны. "
                        f"Последняя ошибка: {str(e)}"
                    )

            except Exception as e:
                logger.error(f"Неожиданная ошибка при выполнении {operation_name}: {str(e)}")
                last_exception = e
                break

        return None

    def get_connection_status(self):
        """Возвращает статус подключений"""
        return {
            'total_errors': sum(self._connection_errors.values()),
            'error_details': dict(self._connection_errors)
        }

# Глобальный менеджер подключений
db_manager = DatabaseConnectionManager()

# Создаем отдельный базовый класс для качества
QualityBase = declarative_base()

def setup_quality_engine():
    return create_engine(
        "mysql+mysqlconnector://{user}:{password}@{host}/{database}".format(
            user=get('mysql_quality', 'user'),
            password=get('mysql_quality', 'password'),
            host=get('mysql_quality', 'host'),
            database=get('mysql_quality', 'database')
        ),
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,  # Проверка соединений перед использованием
        pool_recycle=3600,   # Переподключение каждый час
        connect_args={
            'connect_timeout': 10,
            'autocommit': True
        }
    )

quality_engine = setup_quality_engine()
QualitySession = scoped_session(sessionmaker(bind=quality_engine))

def init_quality_db():
    QualityBase.metadata.create_all(quality_engine)

@contextmanager
def get_quality_session_safe():
    """Безопасное получение сессии качества с обработкой ошибок"""
    session = None
    try:
        session = QualitySession()
        yield session
    except Exception as e:
        logger.error(f"Ошибка при работе с сессией качества: {str(e)}")
        if session:
            session.rollback()
        raise
    finally:
        if session:
            session.close()

Base = declarative_base()

def get_database_config():
    """
    Получает конфигурацию базы данных из безопасного источника или config.ini.
    Приоритет отдается безопасной конфигурации из переменных окружения.
    Файл config.ini используется как фоллбэк для локальной разработки.
    """
    # Сначала пробуем безопасную конфигурацию
    try:
        from secure_config import get_config
        secure_config = get_config()

        # Проверяем наличие обязательных переменных
        missing = secure_config.validate_required_vars()
        if not missing:
            print("✅ Используется безопасная конфигурация из переменных окружения")

            return {
                'mysql': secure_config.get_mysql_config(),
                'mysql_quality': {
                    'host': secure_config.mysql_quality_host,
                    'database': secure_config.mysql_quality_database,
                    'user': secure_config.mysql_quality_user,
                    'password': secure_config.mysql_quality_password
                }
            }
        else:
            print(f"⚠️ Отсутствуют переменные окружения: {', '.join(missing)}")
            raise ImportError("Неполная безопасная конфигурация")

    except ImportError:
        print("⚠️ Используется устаревшая конфигурация config.ini")

        # Проверка наличия основных переменных окружения для MySQL
        mysql_host_env = os.getenv('MYSQL_HOST')
        mysql_quality_host_env = os.getenv('MYSQL_QUALITY_HOST')

        if mysql_host_env and mysql_quality_host_env:
            print("✅ Конфигурация MySQL загружается из переменных окружения (Production mode).")
            return {
                'mysql': {
                    'host': mysql_host_env,
                    'database': os.getenv('MYSQL_DATABASE'),
                    'user': os.getenv('MYSQL_USER'),
                    'password': os.getenv('MYSQL_PASSWORD')
                },
                'mysql_quality': {
                    'host': mysql_quality_host_env,
                    'database': os.getenv('MYSQL_QUALITY_DATABASE'),
                    'user': os.getenv('MYSQL_QUALITY_USER'),
                    'password': os.getenv('MYSQL_QUALITY_PASSWORD')
                }
            }

        print("ℹ️ Переменные окружения для БД не найдены, используется config.ini (Development mode).")
        config = configparser.ConfigParser()

        # Пробуем найти config.ini в нескольких стандартных местах
        possible_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini'),
            os.path.join(os.getcwd(), 'config.ini'),
            'config.ini'
        ]

        config_path = None
        for path in possible_paths:
            if os.path.exists(path):
                config_path = path
                break

        # Если файл не найден, вызываем ошибку
        if not config_path:
            print("--- [DIAGNOSTIC ERROR] ---")
            print("❌ Файл config.ini не найден ни по одному из путей:")
            for path in possible_paths:
                print(f"  - {path}")
            print(f"Текущая рабочая директория: {os.getcwd()}")
            print(f"Содержимое директории: {os.listdir('.')}")
            print("--------------------------")
            raise FileNotFoundError("Не найден файл конфигурации config.ini")

        # Читаем найденный файл
        config.read(config_path, encoding='utf-8')

        # Проверяем наличие секции [mysql] и выводим содержимое файла при ошибке
        if not config.has_section('mysql'):
            print("--- [DIAGNOSTIC ERROR] ---")
            print(f"❌ Секция [mysql] не найдена в файле: {config_path}")
            print("🔍 Полное содержимое файла:")
            with open(config_path, 'r', encoding='utf-8') as f:
                print(f.read())
            print(f"Найденные секции: {config.sections()}")
            print("--------------------------")
            raise configparser.NoSectionError('mysql')

        print(f"✅ Конфигурация успешно загружена из {config_path}")
        print(f"ℹ️ Найдены секции: {config.sections()}")

        # Возвращаем конфигурацию из файла
        return {
            'mysql': {
                'host': config.get('mysql', 'host'),
                'database': config.get('mysql', 'database'),
                'user': config.get('mysql', 'user'),
                'password': config.get('mysql', 'password')
            },
            'mysql_quality': {
                'host': config.get('mysql_quality', 'host'),
                'database': config.get('mysql_quality', 'database'),
                'user': config.get('mysql_quality', 'user'),
                'password': config.get('mysql_quality', 'password')
            }
        }

# Получаем конфигурацию
db_config = get_database_config()

# ИСПРАВЛЕНИЕ: Формируем URL соединения из конфигурации
DATABASE_URL = (
    f"mysql+mysqlconnector://{db_config['mysql']['user']}:"
    f"{db_config['mysql']['password']}@{db_config['mysql']['host']}/"
    f"{db_config['mysql']['database']}"
)

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        'connect_timeout': 10,
        'autocommit': True
    }
)
Session = sessionmaker(bind=engine)

# ИСПРАВЛЕНИЕ: Формируем URL соединения для quality из конфигурации
QUALITY_DATABASE_URL = (
    f"mysql+mysqlconnector://{db_config['mysql_quality']['user']}:"
    f"{db_config['mysql_quality']['password']}@{db_config['mysql_quality']['host']}/"
    f"{db_config['mysql_quality']['database']}"
)

quality_engine = create_engine(
    QUALITY_DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        'connect_timeout': 10,
        'autocommit': True
    }
)
QualitySession = sessionmaker(bind=quality_engine)

def get_quality_connection():
    """Устаревшая функция - используйте execute_quality_query_safe()"""
    try:
        session = QualitySession()
        return session
    except Exception as e:
        logger.error(f"Ошибка подключения к базе quality: {str(e)}")
        return None

def execute_quality_query_safe(query_func, operation_name="quality query"):
    """
    Безопасное выполнение запроса к базе качества

    Args:
        query_func: Функция, принимающая session и возвращающая результат
        operation_name: Название операции для логирования

    Returns:
        Результат запроса или None в случае ошибки
    """
    return db_manager.execute_with_retry(
        query_func,
        QualitySession,
        operation_name
    )

def execute_main_query_safe(query_func, operation_name="main query"):
    """
    Безопасное выполнение запроса к основной базе

    Args:
        query_func: Функция, принимающая session и возвращающая результат
        operation_name: Название операции для логирования

    Returns:
        Результат запроса или None в случае ошибки
    """
    return db_manager.execute_with_retry(
        query_func,
        Session,
        operation_name
    )

class Status(Base):
    __tablename__ = "u_statuses"  # Название таблицы

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=False, nullable=False)
    # Связь с Issue
    issues = relationship("Issue", back_populates="status")

    def __repr__(self):
        return f"Status({self.id}, {self.name})"


class Priority(Base):
    __tablename__ = "u_Priority"  # Название таблицы

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=False, nullable=False)
    # Связь с Issue
    issues = relationship("Issue", back_populates="priority")

    def __repr__(self):
        return f"Status({self.id}, {self.name})"


class Users(Base):
    __tablename__ = "users"  # Название таблицы

    id = Column(Integer, primary_key=True)
    login = Column(String(255), unique=False, nullable=False)
    firstname = Column(String(30), unique=False, nullable=False)
    lastname = Column(String(255), unique=False, nullable=False)
    # Связь с Issue
    issues = relationship(
        "Issue", back_populates="user"
    )  # 'user' здесь должен совпадать с атрибутом в классе Issue

    def __repr__(self):
        return f"Users({self.id},{self.login}, {self.firstname}, {self.lastname})"


# Определение модели Issues
class Issue(Base):
    __tablename__ = "issues"  # Название таблицы

    id = Column(Integer, primary_key=True)
    created_on = Column(String(30), nullable=False)
    subject = Column(String(255), unique=False, nullable=True)
    updated_on = Column(DateTime, nullable=True)
    project_id = Column(Integer, nullable=False)
    description = Column(String(255), unique=False, nullable=True)
    assigned_to_id = Column(Integer, nullable=True)
    # priority_id = Column(Integer, nullable=False)
    author_id = Column(Integer, nullable=False)
    start_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    closed_on = Column(DateTime, nullable=True)
    easy_status_updated_on = Column(DateTime)
    easy_last_updated_by_id = Column(Integer, nullable=True)
    easy_email_to = Column(String(255))
    easy_email_cc = Column(String(255))
    # Связь с Status
    status_id = Column(Integer, ForeignKey("u_statuses.id"))  # Внешний ключ
    status = relationship("Status", back_populates="issues")
    # Связь с Prority
    priority_id = Column(Integer, ForeignKey("u_Priority.id"))  # Внешний ключ
    priority = relationship("Priority", back_populates="issues")
    # Связь с Users
    assigned_to_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("Users", back_populates="issues")

    def __repr__(self):
        return (
            f"Issues({self.id}, {self.created_on}, {self.subject}, {self.status_id}, {self.easy_status_updated_on},"
            f" {self.project_id}, {self.description}, {self.assigned_to_id}, {self.priority_id}, {self.author_id}, "
            f" {self.updated_on}, {self.start_date}, {self.due_date}, {self.closed_on}, {self.easy_last_updated_by_id},"
            f" {self.easy_email_to}, {self.easy_email_cc})"
        )


# Определение модели Notifications
class Notifications(Base):
    __tablename__ = "u_its_update_status"  # Название таблицы

    id = Column(Integer, primary_key=True)
    IssueID = Column(Integer, nullable=True)
    Subj = Column(String(500))
    OldStatus = Column(String(255))
    NewStatus = Column(String(255))
    DateCreated = Column(String(255))
    OldSubj = Column(String(500))
    UserRedmine = Column(Integer, nullable=True)
    UserID = Column(Integer, nullable=True)

    def __repr__(self):
        return (
            f"Issues({self.id}, {self.IssueID}, {self.Subj}, {self.OldStatus}, {self.NewStatus},"
            f" {self.DateCreated}, {self.OldSubj}, {self.UserRedmine}, {self.UserID}"
        )


def get_issue_details(issue_id):
    try:
        with Session() as session:
            # Создаем алиасы для таблицы Users
            users_assigned_to = aliased(Users)
            users_author = aliased(Users)
            users_last_updated_by = aliased(Users)

            issue_detail = (
                session.query(
                    Issue.id,
                    Issue.subject,
                    Issue.description,
                    Status.name.label("status_name"),
                    Priority.name.label("priority_name"),
                    Issue.author_id,
                    Issue.created_on,
                    Issue.updated_on,
                    Issue.closed_on,
                    Issue.start_date,
                    Issue.due_date,
                    Issue.easy_email_to,
                    Issue.easy_email_cc,
                    Issue.easy_last_updated_by_id,
                    users_assigned_to.lastname.label("assigned_to_lastname"),
                    users_assigned_to.firstname.label("assigned_to_firstname"),
                    users_last_updated_by.lastname.label("last_updated_by_lastname"),
                    users_last_updated_by.firstname.label("last_updated_by_firstname"),
                    users_author.lastname.label("author_lastname"),
                    users_author.firstname.label("author_firstname"),
                    users_author.login.label("author_login"),
                )
                .outerjoin(
                    users_assigned_to, Issue.assigned_to_id == users_assigned_to.id
                )
                .outerjoin(
                    users_last_updated_by,
                    Issue.easy_last_updated_by_id == users_last_updated_by.id,
                )
                .outerjoin(users_author, Issue.author_id == users_author.id)
                .join(Status, Issue.status_id == Status.id)
                .join(Priority, Issue.priority_id == Priority.id)
                .filter(Issue.id == issue_id)
                .first()
            )
    except OperationalError:
        engine.dispose()  # Закрываем текущее соединение
        session = Session()  # Создаем новую сессию
        issue_detail = get_issue_details(issue_id)  # Повторяем запрос
    return issue_detail


class CustomValue(Base):
    __tablename__ = 'custom_values'

    id = Column(Integer, primary_key=True)
    customized_type = Column(String(30))
    customized_id = Column(Integer)
    custom_field_id = Column(Integer)
    value = Column(String(255))

    def __repr__(self):
        return f"CustomValue({self.id}, {self.value})"


class Tracker(Base):
    __tablename__ = 'trackers'

    id = Column(Integer, primary_key=True)
    name = Column(String(30))
    default_status_id = Column(Integer)

    def __repr__(self):
        return f"Tracker({self.id}, {self.name})"
