from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship, aliased, scoped_session
from sqlalchemy.exc import OperationalError
from config import get  # Исправленный импорт

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
        max_overflow=10
    )

quality_engine = setup_quality_engine()
QualitySession = scoped_session(sessionmaker(bind=quality_engine))

def init_quality_db():
    QualityBase.metadata.create_all(quality_engine)

Base = declarative_base()
DATABASE_URL = (
    "mysql+mysqlconnector://easyredmine:QhAKtwCLGW@helpdesk.teztour.com/redmine"
)

engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)
Session = sessionmaker(bind=engine)

QUALITY_DATABASE_URL = (
    "mysql+mysqlconnector://easyredmine:QhAKtwCLGW@quality.teztour.com/redmine"
)
quality_engine = create_engine(QUALITY_DATABASE_URL, pool_size=10, max_overflow=20)
QualitySession = sessionmaker(bind=quality_engine)

def get_quality_connection():
    try:
        session = QualitySession()
        return session
    except Exception as e:
        print(f"Ошибка подключения к базе quality: {str(e)}")
        return None


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
