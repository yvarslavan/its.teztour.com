import logging
import re
import datetime
import traceback
from collections import defaultdict
import sys
import os
from contextlib import contextmanager
from typing import Dict, Any, List, Optional, Literal, Union
from sqlalchemy.sql import func
from sqlalchemy import select, MetaData, Table, desc, case, text, Column, Integer, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session as flask_session,
    current_app,
    jsonify,
    Response,
    Flask,
)
import requests
from lxml import etree
from blog.models import AgencyPhone, CallInfo

from flask_cors import CORS
import pymysql
from pymysql.cursors import DictCursor
import xmltodict
import uuid
import time
from flask_session import Session
import base64
import threading
from blog.migrations import engine_oracle_crm, engine_sales_schema  # Использовать готовые движки


# Константы для работы с XML API
XML_AUTH_URL = "http://xml.teztour.com/xmlgate/auth_data.jsp?j_login_request=1&j_login=cmcrm&j_passwd=eGUEbmsQA"

# Хранилище активных сессий
active_sessions = {}

# Глобальные переменные для путей логов
stat_log_path = os.path.join(os.getcwd(), "stat.log")
error_log_path = os.path.join(os.getcwd(), "app_err.log")

# Настройка логирования ошибок
logging.basicConfig(
    filename=error_log_path,
    level=logging.DEBUG, # <<< Меняем уровень на DEBUG
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True # Добавляем force=True для перенастройки, если basicConfig уже был вызван где-то еще
)
logger = logging.getLogger(__name__)

calls = Blueprint("calls", __name__, template_folder="templates")

CORS(
    calls,
    resources={
        r"/contact-center/vilnius/tel/*": {
            "origins": ["*"],  # Разрешаем все источники
            "supports_credentials": True, # Corrected from allow_credentials
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "Accept"],
            "expose_headers": ["Content-Type"],
        },
        r"/api/*": {
            "origins": ["https://its.tez-tour.com", "http://localhost:5000"],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    },
)
PHONE_PREFIX = "+"

# Создайте Session для Oracle баз данных
SessionOracleCRM = sessionmaker(bind=engine_oracle_crm)
SessionSalesSchema = sessionmaker(bind=engine_sales_schema)
# Определение таблицы звонков (call_info)
# Определяем вручную, чтобы обойти проблемы с autoload
metadata = MetaData()
try:
    call_info_table = Table(
        "T_CALL_INFO",
        metadata,
        Column("call_info_id", Integer, primary_key=True), # Нужен для where
        Column("time_end", DateTime), # Нужен для values
        # Добавьте другие колонки здесь, если они понадобятся
        # например, Column("some_other_column", String)
        schema='SALES' # Указываем схему
    )
    print("DEBUG: Таблица T_CALL_INFO определена вручную.")
except Exception as e:
    call_info_table = None # Оставляем None в случае ошибки определения
    detailed_error = traceback.format_exc()
    logging.error(
        "Ошибка при ручном определении таблицы T_CALL_INFO. "
        "Продолжаем запуск приложения. Ошибка: %s\nTraceback:\n%s",
        e, detailed_error
    )
# Настройка логгера
logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
# URL с параметрами запроса
# url_with_params = "http://xml.teztour.com/xmlgate/auth_data.jsp?j_login_request=1&j_login=cmcrm&j_passwd=eGUEbmsQA"

# Определяем путь к файлу лога относительно текущей директории
log_file_path = os.path.join(os.getcwd(), "stat.log")

# Настройки подключения к базе данных tez_tour_cc
MYSQL_CONFIG = {
    "host": "voipcrm.tez-tour.com",
    "user": "root",
    "password": "weo2ik3jc",
    "db": "tez_tour_cc",
    "port": 3306,
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor  # Добавляем это
}

def get_db_connection():
    """Создает и возвращает соединение с базой данных MySQL"""
    try:
        connection = pymysql.connect(**MYSQL_CONFIG)
        return connection
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {str(e)}")
        return None


# Создаем привязки к моделям для Oracle
def get_session_with_bind(bind_key):
    try:
        if bind_key == "oracle_crm":
            return SessionOracleCRM()
        if bind_key == "sales_schema":
            return SessionSalesSchema()
        raise ValueError(f"Unknown bind key: {bind_key}")
    except Exception as e:
        logger.error("Error in get_session_with_bind: %s", {str(e)})
        raise


def write_log(message):
    try:
        ct = datetime.datetime.now()
        curt = ct.strftime("%Y-%m-%d %H:%M:%S")
        mess_log = f"{curt} tel: '{message}'\n"
        with open(stat_log_path, "a", encoding="utf-8") as f:
            f.write(mess_log)
    except IOError as e:
        logger.error("Не удалось записать в файл лога stat.log: %s", {str(e)})


def get_agency_id_by_ani(ani) -> Union[Any, Literal['0']]:
    # Проверяем формат номера
    ani_str = str(ani) if ani is not None else ""

    # Удаляем пробелы из номера перед обработкой
    ani_str = ani_str.replace(" ", "")

    # Проверка на Unknown или пустые значения
    if not ani_str or ani_str.lower() == "unknown" or len(ani_str) < 5:
        logger.warning(f"Номер телефона пустой или некорректный: '{ani_str}'")
        return '0'

    # Добавляем префикс только если номер не начинается с +
    if not ani_str.startswith('+'):
        ani = PHONE_PREFIX + ani_str
    else:
        ani = ani_str  # оставляем как есть, если номер уже с +

    try:
        session_with_oracle_crm_schema = get_session_with_bind("oracle_crm")
        agency_phone = session_with_oracle_crm_schema.query(AgencyPhone)\
            .filter_by(agency_phone=ani)\
            .order_by(AgencyPhone.agency_id.desc())\
            .first()

        if agency_phone:
            return agency_phone.agency_id

        return '0'
    except Exception as e:
        logger.error(f"Ошибка в функции get_agency_id_by_ani: {str(e)}")
        return '0'


def get_xml_agency_not_blacklist(agency_id):
    # Игнорируем предупреждения Pylint о неизвестных членах lxml.etree
    # pylint: disable=I1101
    try:
        auth_url = XML_AUTH_URL
        response = requests.get(auth_url, timeout=10)
        sess_id = etree.fromstring(response.content).findtext("sessionId")

        agency_url = f"http://xml.teztour.com/xmlgate/agency/view?agencyId={agency_id}&aid={sess_id}"
        response_agency = requests.get(agency_url, timeout=10)
        root = etree.fromstring(response_agency.content)
        root_mess = root.findtext("agency/blaсkList")

        return root_mess == "false"
    except Exception as err:
        logger.error("Error in get_xml_agency_not_blacklist:%s", {str(err)})
        return False


def handle_endcall():
    try:
        pk_record = get_pk_record()
        # Получаем ANI из сессии Flask для вывода номера телефона
        ani = flask_session.get("ANI", "")

        if pk_record is not None:
            write_end_call(pk_record, engine_sales_schema)
            # Получаем информацию о звонке для отображения на странице
            with session_scope() as db_session:
                call_info = (
                    db_session.query(CallInfo).filter(CallInfo.id == pk_record).first()
                )
                call_dict = call_info.__dict__ if call_info else {}
                # Удаляем ненужные атрибуты SQLAlchemy
                if "_sa_instance_state" in call_dict:
                    del call_dict["_sa_instance_state"]

                # Добавляем номер телефона, если его нет в данных звонка
                # или заменяем существующий, если номер пришел из URL
                if ani:
                    call_dict["phone_number"] = ani

                return render_template("endcall.html", call=call_dict)

        # Если pk_record is None, возвращаем шаблон с номером из URL
        return render_template("endcall.html", call={"phone_number": ani})
    except Exception as e:
        logger.error("Error in handle_endcall: %s", str(e))
        return render_template("endcall.html", call={"phone_number": ani}, error=str(e))


def handle_agency_not_found(ani):
    try:
        flask_session["agency_data"] = {}
        return render_template(
            "agency_not_found.html",
            ani="+" + ani[0:12],
            agency_data=flask_session.get("agency_data", {}),
        )
    except Exception as e:
        logger.error("Error in handle_agency_not_found: %s", {str(e)})
        raise


def handle_newcall(curator: str, ag_id: str, ani: str, tel: int):
    try:
        # Добавляем логирование входных параметров
        logger.info(
            f"Starting handle_newcall with params: curator={curator}, ag_id={ag_id}, ani={ani}, tel={tel}"
        )

        # Запись статистики в базу данных
        with session_scope() as db_session:
            pk_record = record_stat_to_db(db_session, curator, ag_id, tel)
            logger.info(f"Successfully recorded stats to db, pk_record={pk_record}")

        # Получаем данные агентства
        try:
            agency_data = parse_xml_data(pk_record, ani, ag_id)
            logger.info(f"Agency data received: {agency_data}")

            if not agency_data:
                logger.error(f"No agency data found for ANI: {ani}")
                return handle_agency_not_found(ani)

            agency_name = agency_data.get("agency_name", "default-agency")
        except Exception as e:
            logger.error(f"Error parsing XML data: {str(e)}")
            return handle_agency_not_found(ani)

        # Получаем историю звонков
        last_calls = []
        if ag_id and ag_id.isdigit():
            try:
                calls = get_last_calls(ag_id)
                if len(calls) > 0:
                    last_calls = calls[1:6]
                logger.info(f"Retrieved {len(last_calls)} last calls")
            except Exception as e:
                logger.error(f"Error getting call history: {str(e)}")

        # Настройка сессии Flask
        flask_session.permanent = True
        current_app.permanent_session_lifetime = 86400

        # Сохранение данных в сессии Flask
        flask_session.update(
            {
                "pk_record": pk_record,
                "agency_id": ag_id,
                "ANI": tel,
                "curator": curator,
                "agency_data": agency_data,
                "agency_name": agency_name,
            }
        )

        # Проверяем наличие данных агентства перед рендерингом
        if not agency_data or not agency_name:
            logger.error(
                f"Missing required agency data. agency_data={bool(agency_data)}, agency_name={bool(agency_name)}"
            )
            return handle_agency_not_found(ani)

        logger.info(f"Rendering template with agency_name={agency_name}")
        return render_template(
            "agency_data.html",
            agency=agency_data,
            call=last_calls[0] if last_calls else None,
            calls=last_calls,
            agency_name=agency_name,
        )

    except Exception as e:
        logger.error(f"Error in handle_newcall: {str(e)}")
        return handle_agency_not_found(ani)


def get_pk_record():
    try:
        with session_scope() as db_session:
            max_id = db_session.query(func.max(CallInfo.id)).scalar()
            return max_id if max_id is not None else 0
    except Exception as e:
        logger.error("Error getting max call info ID: %s", {str(e)})
        raise


@calls.route("/contact-center/vilnius")
def contact_center():
    last_calls = []
    calls_count = 0
    last_call = None
    recent_calls = []
    error_message = None

    # Проверяем, загрузилась ли таблица
    if call_info_table is None:
        error_message = "Ошибка: Не удалось загрузить информацию о звонках (T_CALL_INFO). Проверьте подключение к БД."
        logger.error(error_message) # Логируем ошибку
    else:
        try:
            last_calls = get_last_calls_all()
            calls_count = len(last_calls)

            if calls_count > 0:
                last_call = last_calls[0]
                recent_calls = last_calls[0:5]

        except Exception as e:
            error_message = f"Ошибка при получении истории звонков: {str(e)}"
            logger.error(error_message)
            # Не перенаправляем, остаемся на странице

    return render_template(
        "contact_center.html",
        call=last_call,
        calls=recent_calls,
        error_message=error_message # Передаем сообщение об ошибке в шаблон
    )


def get_last_calls(agency_id: str, limit: int = 6) -> List[Dict[str, Any]]:
    """Получение последних звонков для агентства с защитой от None"""
    try:
        # Проверяем, что таблица инициализирована
        if call_info_table is None:
            logger.error("Таблица T_CALL_INFO не доступна")
            return []

        # Используем текущий код только если таблица инициализирована
        duration_in_seconds = (
            call_info_table.time_end - call_info_table.time_begin
        ) * 86400

        # Преобразование длительности в минуты и секунды
        duration_expression = case(
            [
                (
                    duration_in_seconds < 60,
                    func.to_char(func.trunc(duration_in_seconds)) + " seconds",
                )
            ],
            else_=(
                func.to_char(func.trunc(duration_in_seconds / 60))
                + " minutes "
                + func.to_char(func.mod(func.trunc(duration_in_seconds), 60))
                + " seconds"
            ),
        ).label("call_duration")
        query = (
            select(
                [
                    call_info_table.time_begin,
                    call_info_table.time_end,
                    call_info_table.phone_number,
                    call_info_table.currator,
                    call_info_table.theme,
                    call_info_table.region,
                    call_info_table.agency_manager,
                    call_info_table.agency_id,
                    call_info_table.agency_name,
                    duration_expression,
                ]
            )
            .where(call_info_table.agency_id == agency_id)
            .order_by(desc(call_info_table.call_info_id))
            .limit(limit)
        )
        result = engine_sales_schema.execute(query).fetchall()
        return [dict(row) for row in result]
    except Exception as e:
        logger.error(f"Ошибка при получении истории звонков: {str(e)}")
        # Используем прямой SQL запрос как резервный вариант
        try:
            with SessionSalesSchema() as session:
                query = text("""
                SELECT CALL_INFO_ID, TIME_BEGIN, TIME_END, PHONE_NUMBER,
                       CURRATOR, THEME, REGION, AGENCY_MANAGER, AGENCY_NAME
                FROM T_CALL_INFO
                WHERE AGENCY_ID = :agency_id
                ORDER BY CALL_INFO_ID DESC
                FETCH FIRST :limit ROWS ONLY
                """)
                result = session.execute(query, {"agency_id": agency_id, "limit": limit}).fetchall()
                return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"Резервный SQL запрос также не удался: {str(e)}")
            return []


def get_last_calls_all(limit: int = 5) -> List[Dict[str, Any]]:
    """Получение последних N звонков для всех агентств (не зависит от call_info_table)"""
    try:
        with SessionSalesSchema() as session:
            query = text("""
            SELECT
                CALL_INFO_ID, TIME_BEGIN, TIME_END, PHONE_NUMBER,
                CURRATOR, THEME, REGION, AGENCY_MANAGER, AGENCY_NAME
            FROM T_CALL_INFO
            ORDER BY CALL_INFO_ID DESC
            FETCH FIRST :limit ROWS ONLY
            """)
            result = session.execute(query, {"limit": limit}).fetchall()
            # Преобразуем строки в словари
            return [dict(row._mapping) for row in result]
    except Exception as e:
        logger.error(f"Ошибка при получении всех последних звонков: {str(e)}")
        # В случае ошибки возвращаем пустой список, чтобы страница не падала
        return []


@calls.route("/call-show/<string:agency_name>/")
def show_agency_data(agency_name: str):
    agency_data: Dict[str, Any] = flask_session.get("agency_data", {})
    agency_id: Optional[str] = flask_session.get("agency_id")
    pk_record = flask_session.get("pk_record")

    last_call: Optional[Dict[str, Any]] = None
    last_calls: List[Dict[str, Any]] = []
    agency_name = agency_data.get("agency_name", agency_name)

    if agency_id and agency_id.isdigit():
        try:
            calls = get_last_calls(agency_id)
            calls_count = len(calls)

            if calls_count > 0:
                last_call = calls[1]
                last_calls = calls[1:6]
        except Exception as e:
            print(f"Error getting call info: {e}")
            # Здесь можно добавить логирование ошибки

    return render_template(
        "agency_data.html",
        agency=agency_data,
        call=last_call,
        calls=last_calls,
        agency_name=agency_name,
        pk_record=pk_record,
    )


def fetch_and_parse_xml(url: str) -> Optional[etree.Element]:
    # Игнорируем предупреждения Pylint о неизвестных членах lxml.etree
    # pylint: disable=I1101
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return etree.fromstring(response.content)
    except (requests.RequestException, etree.XMLSyntaxError) as e:
        logger.error("Ошибка при получении или разборе XML: %s", e)
        return None  # Возвращаем None в случае ошибки


def process_xml_data(url: str) -> None:
    xml_tree = fetch_and_parse_xml(url)
    if xml_tree is not None:
        root = xml_tree.getroot()
        logger.info("Корневой элемент: %s", root.tag)
        for child in root:
            logger.info("%s: %s", child.tag, child.text)
    else:
        logger.error("Не удалось получить или разобрать XML данные.")


def parse_xml_data(pk_record, ani: str, agency_id: str) -> dict:
    # Игнорируем предупреждения Pylint о неизвестных членах lxml.etree
    # pylint: disable=I1101
    try:
        jsession_agency_id = authenticate_and_get_session_id()
        root = fetch_agency_data(agency_id, jsession_agency_id)

        value = defaultdict(str)
        extract_agency_data(pk_record, root, value)
        extract_contact_info(pk_record, root, ani, value)
        extract_managers(root, value)

        return dict(value)
    except requests.exceptions.RequestException as e:
        logger.error("Network error in parse_xml_data: %s", e)
        return {"error": "Network error occurred while fetching data"}
    except etree.XMLSyntaxError as e:
        logger.error("XML parsing error in parse_xml_data: %s", e)
        return {"error": "Error parsing XML data"}
    except Exception as e:
        logger.exception("Unexpected error in parse_xml_data")
        return {
            "error": "An unexpected error occurred",
            "error_details": str(e),
            "error_type": type(e).__name__,
        }


def authenticate_and_get_session_id() -> str:
    # Используем константу вместо жесткого URL
    response = requests.get(XML_AUTH_URL, timeout=10)
    response.raise_for_status()
    sess = etree.fromstring(response.content)
    return sess.find(".//sessionId").text


def fetch_agency_data(agency_id: str, jsession_agency_id: str) -> etree.Element:
    # Игнорируем предупреждения Pylint о неизвестных членах lxml.etree
    # pylint: disable=I1101
    agency_url = f"http://xml.teztour.com/xmlgate/agency/view?agencyId={agency_id}&aid={jsession_agency_id}"
    response = requests.get(agency_url, timeout=10)
    response.raise_for_status()
    return etree.fromstring(response.content)


def extract_agency_data(pk_record, root: etree.Element, value: defaultdict) -> None:
    # Игнорируем предупреждения Pylint о неизвестных членах lxml.etree
    # pylint: disable=I1101
    xpath_mappings = {
        "agency_name": "./name",
        "company_name_en": "./nameEng",
        "agency_city": "./city",
        "agency_percent": "./percent",
        "agency_front_office": "./frontOffice",
        "agency_contract": "./contract",
        "agency_quantity_tourists": "./sentTourists",
        "agency_boss": "./boss",
        "agency_curator_name": "./curator/fullName",
        "agency_blacklist": "./blackList",
    }
    # Извлекаем имя агентства
    agency_name_element = root.find(xpath_mappings["agency_name"])
    if agency_name_element is not None and agency_name_element.text:
        agency_name = agency_name_element.text.strip()
        # Передаем имя агентства в функцию
        write_agency_name(pk_record, agency_name, engine_sales_schema)
        logger.info(
            "Agency name extracted and passed to write_agency_name: %s", agency_name
        )
    else:
        logger.warning(
            "XPath %s returned no results for agency_name",
            xpath_mappings["agency_name"],
        )
    # Извлечение остальных данных
    for key, xpath in xpath_mappings.items():
        try:
            result = root.find(xpath)
            if result is not None and result.text:
                value[key] = result.text.strip()
                logger.info("Extracted %s: %s", key, value[key])
            else:
                logger.warning("XPath %s returned no results for %s", xpath, key)
        except Exception as e:
            logger.error("Error processing XPath %s for %s: %s", xpath, key, e)


def extract_contact_info(
    pk_record, root: etree.Element, ani: str, value: defaultdict
) -> None:
    # Игнорируем предупреждения Pylint о неизвестных членах lxml.etree
    # pylint: disable=I1101
    ani = "+" + re.sub(r"\s", "", ani)  # Удаляем все пробельные символы из входного ani
    contact_xpath = ".//contacts/contact"
    try:
        contacts = root.findall(contact_xpath)
        for contact in contacts:
            value_elem = contact.find("value")
            if value_elem is not None and value_elem.text == ani:
                extract_contact_details(pk_record, contact, value)
                break
        else:
            logger.warning("Contact information not found for ANI: %s", ani)
    except Exception as e:
        logger.error("Error processing contact information for ANI: %s: %s", ani, e)


def extract_contact_details(
    pk_record, contact: etree.Element, value: defaultdict
) -> None:
    # Игнорируем предупреждения Pylint о неизвестных членах lxml.etree
    # pylint: disable=I1101
    person_result = contact.find("person")
    if person_result is not None and person_result.text:
        value["agency_contact_person"] = person_result.text.strip()
        write_agency_manager(
            pk_record, value.get("agency_contact_person"), engine_sales_schema
        )
        logger.info(
            "Extracted agency_contact_person: %s", value["agency_contact_person"]
        )
    else:
        logger.warning("Contact person not found")

    description_result = contact.find("description")
    if description_result is not None and description_result.text:
        value["agency_contact_description"] = description_result.text.strip()
        logger.info(
            "Extracted agency_contact_description: %s",
            value["agency_contact_description"],
        )
    else:
        logger.warning("Contact description not found")


def extract_managers(root: etree.Element, value: defaultdict) -> None:
    # Игнорируем предупреждения Pylint о неизвестных членах lxml.etree
    # pylint: disable=I1101
    try:
        managers = root.findall("./managers/manager")
        agency_employee = " / ".join([m.text.strip() for m in managers[:10] if m.text])
        value["agency_employee"] = agency_employee
        logger.info("Extracted agency_employee: %s", agency_employee)
    except Exception as e:
        logger.error("Error processing agency_employee: %s", e)


def log_network_error(error: Exception) -> None:
    logger.error("Network error in parse_xml_data: %s", error)


def log_xml_error(error: Exception) -> None:
    logger.error("XML parsing error in parse_xml_data: %s", error)


def log_unexpected_error(error: Exception) -> None:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    tb_text = "".join(tb_lines)
    logger.error("Unexpected error in parse_xml_data: %s", error)
    logger.error("Traceback:\n%s", tb_text)


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    db_session = SessionSalesSchema()
    try:
        yield db_session
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        logger.error("Error in database transaction: %s", {str(e)})
        raise
    finally:
        db_session.close()


def get_max_call_info_id(db_session):
    try:
        max_id = db_session.query(func.max(CallInfo.id)).scalar()
        return max_id if max_id is not None else 0
    except Exception as e:
        logger.error("Error getting max call info ID: %s", {str(e)})
        raise


def record_stat_to_db(
    session, curator=None, ag_id=None, tel=None, theme=None, region="lt"
):
    """Записывает информацию о звонке в базу данных"""
    try:
        # Проверяем и очищаем номер телефона
        if not tel or tel == "+" or len(tel) < 3:
            logger.warning(f"Отклонена запись с некорректным номером телефона: '{tel}'")
            return None  # Прекращаем создание записи, возвращаем None

        # Получаем максимальный ID в таблице и увеличиваем на 1
        max_id_query = text("SELECT NVL(MAX(CALL_INFO_ID), 0) FROM T_CALL_INFO")
        max_id_result = session.execute(max_id_query).scalar()
        new_id = (max_id_result or 0) + 1

        time_now = datetime.datetime.now()

        # Создаем запись с явным указанием ID
        insert_query = text("""
        INSERT INTO T_CALL_INFO
        (CALL_INFO_ID, TIME_BEGIN, TIME_END, PHONE_NUMBER, CURRATOR, THEME, AGENCY_ID, REGION)
        VALUES (:id, :time_begin, :time_end, :phone, :curator, :theme, :agency_id, :region)
        """)

        params = {
            'id': new_id,
            'time_begin': time_now,
            'time_end': time_now,
            'phone': tel,
            'curator': curator if curator else None,
            'theme': theme if theme else None,
            'agency_id': str(ag_id) if ag_id else None,  # Преобразуем в строку, т.к. колонка VARCHAR2
            'region': region
        }

        # Выполняем запрос
        session.execute(insert_query, params)

        # Только логируем - не делаем commit здесь, т.к. это может делаться в контексте
        logger.info(f"Создана новая запись звонка с ID: {new_id} для номера {tel}")

        return new_id
    except Exception as e:
        logger.error(f"Ошибка при создании записи звонка: {str(e)}")
        traceback.print_exc()
        session.rollback()  # Откатываем транзакцию при ошибке
        return None


def write_end_call(pk_record, sales_schema):
    try:
        update_stmt = (
            call_info_table.update()
            .where(call_info_table.call_info_id == pk_record)
            .values(time_end=func.sysdate)
        )
        sales_schema.execute(update_stmt)
    except Exception as e:
        logger.error("Error updating end call: %s", e)
    return 0


@calls.route("/update_call_theme", methods=["POST"])
def update_call_theme():
    try:
        pk_record = flask_session.get("pk_record")
        theme = request.form.get("theme", "")

        if not pk_record:
            logger.error("pk_record отсутствует в сессии")
            return (
                jsonify({"status": "error", "message": "Запись звонка не найдена"}),
                400,
            )

        logger.info(f"Обновление темы: pk_record={pk_record}, тема: {theme}")

        # Прямой SQL запрос без использования ORM
        with engine_sales_schema.connect() as connection:
            # Формируем SQL запрос напрямую к таблице
            sql = """
            UPDATE T_CALL_INFO
            SET THEME = :theme
            WHERE CALL_INFO_ID = :pk_record
            """
            result = connection.execute(sql, {"theme": theme, "pk_record": pk_record})
            affected_rows = result.rowcount

            logger.info(f"SQL-запрос выполнен, затронуто строк: {affected_rows}")

            if affected_rows == 0:
                return (
                    jsonify(
                        {
                            "status": "warning",
                            "message": "Запись не найдена или тема не изменилась",
                        }
                    ),
                    200,
                )

            return jsonify({"status": "success"})
    except Exception as e:
        logger.exception(f"Ошибка при обновлении темы: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


def write_agency_name(call_id, agency_name, engine):
    """Обновляет имя агентства для записи о звонке"""
    try:
        # Исправляем SQL-запрос, добавляя точное соответствие ID
        update_query = text("""
        UPDATE T_CALL_INFO
        SET AGENCY_NAME = :agency_name
        WHERE CALL_INFO_ID = :call_id
        """)

        # Выполняем запрос с explicit commit
        with engine.begin() as conn:  # begin() автоматически делает commit при выходе
            conn.execute(update_query, {"agency_name": agency_name, "call_id": call_id})

        logger.info(f"Обновлено имя агентства для звонка {call_id}: {agency_name}")

        # Проверяем, действительно ли данные записались
        with engine.connect() as conn:
            verify_query = text("""
            SELECT AGENCY_NAME FROM T_CALL_INFO
            WHERE CALL_INFO_ID = :call_id
            """)
            result = conn.execute(verify_query, {"call_id": call_id}).fetchone()
            if result and result[0] == agency_name:
                logger.info(f"✅ Проверка: имя агентства {agency_name} успешно записано в БД")
            else:
                logger.warning(f"❌ Проверка: имя агентства НЕ было записано в БД (результат: {result[0] if result else 'None'})")

        return True
    except Exception as e:
        logger.warning(f"Error updating agency name: {str(e)}")
        traceback.print_exc()
        return False


def write_agency_manager(call_id, manager_name, engine):
    """Обновляет имя менеджера агентства для записи о звонке"""
    try:
        # Используем begin() вместо connect() для автоматического commit
        update_query = text("""
        UPDATE T_CALL_INFO
        SET AGENCY_MANAGER = :manager_name
        WHERE CALL_INFO_ID = :call_id
        """)

        # Выполняем запрос с explicit commit
        with engine.begin() as conn:
            conn.execute(update_query, {"manager_name": manager_name, "call_id": call_id})

        logger.info(f"Обновлен менеджер агентства для звонка {call_id}: {manager_name}")
        return True
    except Exception as e:
        logger.warning(f"Error updating agency manager: {str(e)}")
        traceback.print_exc()
        return False


@calls.route('/get_latest_calls')
def get_latest_calls():
    try:
        # Используем безопасную версию получения истории звонков
        calls_data = []

        # Безопасный запрос к базе данных
        with SessionSalesSchema() as session:
            query = text("""
            SELECT
                CALL_INFO_ID, TIME_BEGIN, TIME_END, PHONE_NUMBER,
                CURRATOR, THEME, REGION, AGENCY_MANAGER, AGENCY_NAME
            FROM T_CALL_INFO
            ORDER BY CALL_INFO_ID DESC
            FETCH FIRST 5 ROWS ONLY
            """)

            result = session.execute(query).fetchall()

            # Правильное преобразование результатов запроса в словари
            for row in result:
                # Создаем словарь вручную
                call_dict = {}
                for column_name in row._fields:
                    # Преобразуем имена полей в верхний регистр
                    call_dict[column_name.upper()] = getattr(row, column_name)

                # Преобразуем datetime в строки для JSON
                if 'TIME_BEGIN' in call_dict and call_dict['TIME_BEGIN']:
                    call_dict['TIME_BEGIN'] = call_dict['TIME_BEGIN'].strftime('%d.%m.%Y %H:%M')
                else:
                    call_dict['TIME_BEGIN'] = 'N/A'

                if 'TIME_END' in call_dict and call_dict['TIME_END']:
                    call_dict['TIME_END'] = call_dict['TIME_END'].strftime('%d.%m.%Y %H:%M')
                else:
                    call_dict['TIME_END'] = 'N/A'

                calls_data.append(call_dict)

        return jsonify({"calls": calls_data})

    except Exception as e:
        logger.error(f"Ошибка при получении обновленных данных: {str(e)}")
        traceback.print_exc()  # Добавляем полный стек ошибки для отладки
        return jsonify({"error": str(e)}), 500


@calls.route("/contact-center/moscow")
@calls.route("/contact-center/moscow/<ani>/<agent_id>")
def contact_center_moscow(ani=None, agent_id=None):
    # Без блока try-except для диагностики

    # Получаем соединение с БД
    connection = get_db_connection()
    connection_error = None
    moscow_calls = []

    if connection:
        try:
            with connection.cursor() as cursor:
                # Получаем звонки за текущие сутки
                # Добавляем cls.result и CASE для call_result_text
                query = """
                SELECT cls.id,
                       t.number AS ani,
                       op.name AS agent_id,
                       cls.datetime AS timestamp,
                       cls.card_id,
                       cls.privat_processing_id,
                       cls.result, -- Добавляем поле result
                       CASE cls.result -- Добавляем CASE для текстового описания
                           WHEN 0 THEN 'Сорвался'
                           WHEN 1 THEN 'Обработано'
                           WHEN 2 THEN 'Клиент положил трубку'
                           WHEN 3 THEN 'Не работает интернет'
                           WHEN 4 THEN 'Сорвался-обрыв'
                           WHEN 5 THEN 'Сорвался-плохая слышимость'
                           WHEN 6 THEN 'Сорвался-тишина'
                           ELSE 'Неизвестный результат'
                       END AS call_result_text,
                       cls.type_call, -- Добавляем поле type_call
                       CASE cls.type_call -- Добавляем CASE для типа звонка
                           WHEN 0 THEN 'Ошиблись номером'
                           WHEN 1 THEN 'Англичанин'
                           WHEN 2 THEN 'Агентство'
                           WHEN 3 THEN 'Сервисный звонок'
                           WHEN 4 THEN 'Покупка билетов'
                           WHEN 5 THEN 'Заказ тура'
                           WHEN 6 THEN 'Не по теме'
                           WHEN 7 THEN 'Сорвался звонок'
                           ELSE 'Неизвестный тип'
                       END AS call_type_text,
                       pp.id AS processing_id -- Добавляем ID из privat_processing для проверки
                FROM calls cls
                LEFT JOIN cards cd ON cls.card_id = cd.id
                LEFT JOIN telephone t ON cd.telephone_id = t.id
                LEFT JOIN operators op ON cls.operator_id = op.id
                LEFT JOIN privat_processing pp ON cls.privat_processing_id = pp.id -- <--- Добавляем JOIN
                WHERE DATE(cls.datetime) = CURDATE()
                ORDER BY cls.datetime DESC
                """
                cursor.execute(query)
                raw_calls = cursor.fetchall()

                # Форматируем данные для шаблона
                moscow_calls = []
                for call in raw_calls:
                    # Определяем has_client_card на основе card_id И наличия записи в privat_processing И pp_id > 0
                    has_client_card = bool(
                        call.get('card_id') and int(call['card_id']) > 0 and \
                        call.get('privat_processing_id') and int(call['privat_processing_id']) > 0 and \
                        call.get('processing_id') is not None
                    )

                    # Определяем, является ли номер неизвестным
                    phone_number = call.get("ani", "Неизвестно")
                    is_unknown = not phone_number or phone_number == "Неизвестно"

                    # Форматируем время
                    timestamp = call.get("timestamp")
                    if isinstance(timestamp, datetime.datetime):
                        formatted_time = timestamp.strftime("%d.%m.%Y, %H:%M:%S")
                    else:
                        formatted_time = str(timestamp) if timestamp else "Н/Д"

                    # Добавляем форматированные данные, включая результат
                    moscow_calls.append({
                        'phone_number': phone_number,
                        'operator_name': call.get("agent_id", "Не указан"),
                        'call_time': formatted_time,
                        'has_client_card': has_client_card,
                        'is_unknown': is_unknown,
                        'id': call.get("id"),
                        'pp_id': str(call.get("privat_processing_id")).split(':')[0] if call.get("privat_processing_id") else None,
                        'result': call.get("result"), # Добавляем числовой результат
                        'call_result_text': call.get("call_result_text"), # Добавляем текстовый результат
                        'card_id': call.get("card_id"), # <<< Добавляем недостающий card_id
                        'call_type_text': call.get("call_type_text") # <<< Добавляем тип звонка
                    })

                logger.info(f"Получено {len(moscow_calls)} записей о звонках за текущие сутки")
        finally:
            connection.close()
    else:
        connection_error = "Не удалось установить соединение с базой данных"
        logger.error(connection_error)

    # Получаем количество звонков
    calls_count = len(moscow_calls)

    # Рендерим шаблон, передавая количество звонков
    return render_template(
        'contact_center_moscow.html',
        calls=moscow_calls,
        calls_count=calls_count, # Передаем количество
        connection_error=connection_error
    )


@calls.route("/api/moscow-calls")
def get_moscow_calls():
    # --- НАЧАЛО ИЗМЕНЕНИЯ ---
    # Получаем логгер и устанавливаем уровень DEBUG прямо здесь
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---
    try:
        # Получаем дату из параметров запроса
        selected_date_str = request.args.get('date')
        if selected_date_str:
            # Пытаемся преобразовать строку в дату
            try:
                selected_date = datetime.datetime.strptime(selected_date_str, '%Y-%m-%d').date()
                date_filter = selected_date
                date_filter_sql = "%s" # Используем плейсхолдер для даты
            except ValueError:
                # Если формат даты неверный, используем текущую дату
                logger.warning(f"Неверный формат даты: {selected_date_str}. Используется текущая дата.")
                date_filter = datetime.date.today()
                date_filter_sql = "CURDATE()" # Используем CURDATE() для текущей даты
        else:
            # Если дата не передана, используем текущую дату
            date_filter = datetime.date.today()
            date_filter_sql = "CURDATE()"
            selected_date = date_filter # Устанавливаем selected_date для логгера

        logger.info(f"Запрос звонков для даты: {selected_date}")


        connection = get_db_connection()
        if not connection:
            logger.error("Не удалось подключиться к базе данных")
            return jsonify({"success": False, "error": "Ошибка подключения к базе данных", "calls": []}), 500

        try:
            with connection.cursor() as cursor:
                 # Используем date_filter_sql в запросе
                query = f"""
                SELECT
                    cls.id,
                    t.number AS phone_number,
                    op.name AS operator_name,
                    cls.datetime AS timestamp,
                    cls.card_id,
                    cls.privat_processing_id AS pp_id,
                    cls.result, -- Добавляем поле result
                    CASE cls.result -- Добавляем CASE для текстового описания
                        WHEN 0 THEN 'Сорвался'
                        WHEN 1 THEN 'Обработано'
                        WHEN 2 THEN 'Клиент положил трубку'
                        WHEN 3 THEN 'Не работает интернет'
                        WHEN 4 THEN 'Сорвался-обрыв'
                        WHEN 5 THEN 'Сорвался-плохая слышимость'
                        WHEN 6 THEN 'Сорвался-тишина'
                        ELSE 'Неизвестный результат'
                    END AS call_result_text,
                    cls.type_call, -- Добавляем поле type_call
                    CASE cls.type_call -- Добавляем CASE для типа звонка
                        WHEN 0 THEN 'Ошиблись номером'
                        WHEN 1 THEN 'Англичанин'
                        WHEN 2 THEN 'Агентство'
                        WHEN 3 THEN 'Сервисный звонок'
                        WHEN 4 THEN 'Покупка билетов'
                        WHEN 5 THEN 'Заказ тура'
                        WHEN 6 THEN 'Не по теме'
                        WHEN 7 THEN 'Сорвался звонок'
                        ELSE 'Неизвестный тип'
                    END AS call_type_text,
                    pp.id AS processing_id -- Добавляем ID из privat_processing для проверки
                FROM calls cls
                LEFT JOIN cards cd ON cls.card_id = cd.id
                LEFT JOIN telephone t ON cd.telephone_id = t.id
                LEFT JOIN operators op ON cls.operator_id = op.id
                LEFT JOIN privat_processing pp ON cls.privat_processing_id = pp.id -- <--- Добавляем JOIN
                WHERE DATE(cls.datetime) = {date_filter_sql}
                ORDER BY cls.datetime DESC
                """
                # Передаем дату как параметр, если используется плейсхолдер
                if date_filter_sql == "%s":
                    cursor.execute(query, (date_filter,))
                else:
                     cursor.execute(query) # Выполняем без параметра для CURDATE()

                calls = cursor.fetchall()

                # Форматируем данные (остальная часть функции без изменений)
                formatted_calls = []
                for call in calls:
                    # Определяем has_client_card на основе card_id И наличия записи в privat_processing И pp_id > 0
                    has_client_card = bool(
                        call.get('card_id') and int(call['card_id']) > 0 and \
                        call.get('pp_id') and int(call['pp_id']) > 0 and \
                        call.get('processing_id') is not None
                    )

                    # Логирование для отладки типа звонка
                    logger.debug(f"Processing call ID {call.get('id')}: card_id={call.get('card_id')}, pp_id={call.get('pp_id')}, processing_id={call.get('processing_id')}, has_client_card={has_client_card}")

                    formatted_call = {
                        'id': call['id'],
                        'phone_number': call['phone_number'],
                        'operator': call['operator_name'],
                        'time': call['timestamp'].strftime("%d.%m.%Y, %H:%M:%S") if call['timestamp'] else '',
                        'card_id': call['card_id'],
                        'pp_id': call['pp_id'],
                        'has_client_card': has_client_card,
                        'result': call['result'], # Возвращаем числовой результат
                        'call_result_text': call['call_result_text'], # Возвращаем текстовый результат
                        'call_type_text': call['call_type_text'] # <<< Добавляем тип звонка
                    }
                    formatted_calls.append(formatted_call)

                # Обновляем кэш только для текущей даты
                # if not selected_date_str:
                #     update_calls_cache(formatted_calls)

                logger.info(f"Получено {len(formatted_calls)} записей о звонках для API за {selected_date}")
                return jsonify({"success": True, "calls": formatted_calls})

        finally:
            connection.close()

    except Exception as e:
        logger.error(f"Ошибка при получении звонков: {str(e)}")
        return jsonify({"success": False, "error": str(e), "calls": []}), 500


@calls.route("/api/call-agency-data/<int:pp_id>")
def get_call_agency_data(pp_id):
    try:
        logger.info(f"Начало обработки запроса для pp_id: {pp_id}")

        connection = get_db_connection()
        if not connection:
            logger.error("Не удалось установить соединение с базой данных")
            return jsonify({
                "success": False,
                "error": "Не удалось подключиться к базе данных",
                "agency_data": []
            }), 500

        try:
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                # Исправленный запрос с правильным JOIN для операторов
                agency_query = """
                SELECT
                    pp.id,
                    ag.id AS agency_db_id, /* Добавили ID самого агентства */
                    ag.name AS agency_name_ru,
                    ag.english_name AS agency_name_en,
                    ag.adres AS agency_address,
                    ag.comment AS agency_comment,
                    ag.tel_1_id, ag.tel_2_id, ag.tel_3_id, ag.tel_4_id, ag.tel_5_id, ag.tel_6_id, ag.tel_7_id,
                    ag.city_id, /* Оставляем для совместимости, но используем cty.name */
                    cty.name AS city_name,
                    ag.metro_id, /* Оставляем для совместимости, но используем ag_metro.name */
                    ag_metro.name AS agency_metro_name, /* Метро самого агентства */
                    ag.district_id, /* Оставляем для совместимости, но используем d.name */
                    d.name AS district_name,
                    ag.area_id, /* Для JOIN с areas */
                    ar.name AS area_name, /* Название зоны/района из areas */
                    ag.region AS agency_region_id, /* ID региона из agentstvo, для JOIN с regions */
                    rg.name AS region_name_from_db, /* Название региона из regions */
                    ag.time_zone,
                    ag.time_rezhim_id,
                    ag.english,
                    ag.tickets,
                    ag.station_not_set,
                    ag.switch_msk_agency,
                    ag.bank_card,
                    ag.stambul,
                    ag.austria,
                    cr.result,
                    CASE cr.result
                        WHEN -1 THEN 'ошибка'
                        WHEN 0 THEN 'дозвон'
                        WHEN 1 THEN 'занято'
                        WHEN 2 THEN 'не подходят'
                        WHEN 3 THEN 'отказались от звонка'
                        WHEN 4 THEN 'бросили трубку'
                        WHEN 5 THEN 'тишина на линии'
                        ELSE 'неизвестно'
                    END AS call_result_text,
                    cnt.name AS client_country,
                    m_client.name AS client_metro, /* Метро клиента из pp.metro_id */
                    mn.name AS manager_name,
                    cr.datetime,
                    n.name AS client_name,
                    o.name AS operator_name
                FROM privat_processing pp
                LEFT JOIN calls_result cr ON FIND_IN_SET(cr.id, REPLACE(pp.calls_results_ids, '|', ','))
                LEFT JOIN telephone t2 ON cr.telephone_id = t2.id
                LEFT JOIN agentstvo ag ON (
                    t2.id = ag.tel_1_id OR
                    t2.id = ag.tel_2_id OR
                    t2.id = ag.tel_3_id OR
                    t2.id = ag.tel_4_id OR
                    t2.id = ag.tel_5_id OR
                    t2.id = ag.tel_6_id OR
                    t2.id = ag.tel_7_id
                )
                LEFT JOIN country cnt ON pp.country_id = cnt.id
                LEFT JOIN city cty ON ag.city_id = cty.id
                LEFT JOIN metro ag_metro ON ag.metro_id = ag_metro.id /* Метро агентства */
                LEFT JOIN metro m_client ON pp.metro_id = m_client.id /* Метро клиента */
                LEFT JOIN names mn ON pp.manager_name_id = mn.id
                LEFT JOIN names n ON pp.client_name_id = n.id
                LEFT JOIN calls cls ON pp.id = cls.privat_processing_id
                LEFT JOIN operators o ON cls.operator_id = o.id
                LEFT JOIN district d ON ag.district_id = d.id
                LEFT JOIN areas ar ON ag.area_id = ar.id /* JOIN для area_name */
                LEFT JOIN regions rg ON ag.region = rg.id /* JOIN для region_name */
                WHERE pp.id = %s
                AND (ag.hidden = 0 OR ag.hidden IS NULL)
                AND (ag.id NOT IN (280, 318) OR ag.id IS NULL)
                AND (d.hidden = 0 OR d.hidden IS NULL)
                ORDER BY cr.datetime DESC
                LIMIT 1
                """

                logger.info(f"Выполнение запроса для pp_id: {pp_id}")
                cursor.execute(agency_query, (pp_id,))
                agency_data_list = cursor.fetchall() # Изменено имя на agency_data_list

                # <<< НАЧАЛО ИЗМЕНЕНИЯ: Получение номеров телефонов >>>
                # phone_numbers = [] # Старая переменная
                if agency_data_list: # Используем новое имя
                    agency_record = agency_data_list[0]
                    agency_record['telephones_detailed'] = [] # Инициализируем новый ключ

                    phone_ids_to_fetch = []
                    for i in range(1, 8):
                        tel_id_key = f'tel_{i}_id'
                        if agency_record.get(tel_id_key) and agency_record[tel_id_key] > 0:
                            phone_ids_to_fetch.append(agency_record[tel_id_key])

                    if phone_ids_to_fetch:
                        placeholders = ', '.join(['%s'] * len(phone_ids_to_fetch))
                        phone_query_detailed = f"""
                        SELECT id, number, comment FROM telephone WHERE id IN ({placeholders})
                        """
                        try:
                            cursor.execute(phone_query_detailed, phone_ids_to_fetch)
                            phones_detailed_data = cursor.fetchall()
                            agency_record['telephones_detailed'] = phones_detailed_data
                            logger.info(f"Найдены детальные телефоны для агентства {agency_record.get('agency_name_ru')}: {len(phones_detailed_data)} шт.")
                        except Exception as phone_e:
                            logger.error(f"Ошибка при получении детальных номеров телефонов: {str(phone_e)}")
                    # Удаляем старые tel_x_id поля, если они больше не нужны напрямую в JS
                    # for i in range(1, 8):
                    #     agency_record.pop(f'tel_{i}_id', None)

                # Преобразуем datetime объекты в строки
                for record in agency_data_list: # Используем новое имя
                    if record.get('datetime'):
                        try:
                            record['datetime'] = record['datetime'].strftime('%d.%m.%Y %H:%M:%S')
                        except Exception as e:
                            logger.error(f"Ошибка форматирования даты: {str(e)}")
                            record['datetime'] = str(record['datetime'])

                logger.info(f"Получено записей: {len(agency_data_list)}") # Используем новое имя
                if agency_data_list: # Используем новое имя
                    logger.info(f"Первая запись: {agency_data_list[0]}")

                return jsonify({
                    "success": True,
                    "agency_data": agency_data_list # Возвращаем список, как и раньше
                })

        except Exception as e:
            logger.error(f"Ошибка при выполнении запроса: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                "success": False,
                "error": str(e),
                "agency_data": []
            }), 500
        finally:
            connection.close()

    except Exception as e:
        logger.error(f"Общая ошибка: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": str(e),
            "agency_data": []
        }), 500


@calls.route("/api/client-card/call/<int:call_id>")
def get_client_card_by_call(call_id):
    """Возвращает данные карточки клиента для конкретного ID звонка."""
    try:
        logger.info(f"Запрос карточки клиента для call_id={call_id}")
        connection = get_db_connection()
        if connection:
            try:
                with connection.cursor(pymysql.cursors.DictCursor) as cursor: # Используем DictCursor для удобства
                    # Запрос изменен для поиска по call_id
                    query = """
                    SELECT
                        pp.id AS processing_id, -- Убедимся, что получаем pp.id
                        n_client.name AS client_name,
                        city.name AS client_city,
                        n_manager.name AS manager_name,
                        m.name AS metro_name,
                        c.name AS country_name,
                        ads.ads_name AS ad_name,
                        t.number AS phone  -- Добавляем номер телефона
                    FROM calls cls
                    JOIN privat_processing pp ON cls.privat_processing_id = pp.id
                    LEFT JOIN names n_client ON pp.client_name_id = n_client.id
                    LEFT JOIN city ON pp.client_city_id = city.id
                    LEFT JOIN names n_manager ON pp.manager_name_id = n_manager.id
                    LEFT JOIN metro m ON pp.metro_id = m.id
                    LEFT JOIN country c ON pp.country_id = c.id
                    LEFT JOIN ads ON pp.ads_id = ads.id
                    LEFT JOIN cards cd ON cls.card_id = cd.id
                    LEFT JOIN telephone t ON cd.telephone_id = t.id
                    WHERE cls.id = %s -- Ищем по ID звонка
                    LIMIT 1 -- На всякий случай, хотя ID должен быть уникален
                    """
                    cursor.execute(query, (call_id,))
                    client = cursor.fetchone()

                    # Добавим логирование для отладки
                    logger.info(
                        f"Запрос карточки для call_id={call_id}, результат: {client}"
                    )

                    if client and client.get('processing_id') is not None: # Доп. проверка на случай, если pp.id был NULL
                        # Успешно найдены данные для этого звонка
                        return jsonify({"success": True, "client_data": client})
                    else:
                        # Данные не найдены для этого конкретного звонка
                        logger.warning(f"Информация о клиенте для call_id={call_id} не найдена или нет связи с privat_processing.")
                        return jsonify({"success": False, "error": "Информация о клиенте не найдена"})
            finally:
                connection.close()
        else:
            logger.error("Не удалось установить соединение с базой данных")
            return jsonify({"error": "Ошибка подключения к базе данных"})
    except Exception as e:
        logger.error(f"Ошибка при получении данных о клиенте: {str(e)}")
        return jsonify({"error": str(e)}), 500


@calls.route("/api/call_stats")
def get_call_stats():
    try:
        connection = get_db_connection()
        if connection:
            try:
                with connection.cursor() as cursor:
                    # Запрос для подсчета общего количества звонков за сутки
                    count_query = """
                    SELECT COUNT(*) as total_calls
                    FROM calls
                    WHERE DATE(datetime) = CURDATE()
                    """
                    cursor.execute(count_query)
                    total_calls_result = cursor.fetchone()
                    total_calls = (
                        total_calls_result["total_calls"] if total_calls_result else 0
                    )

                    # Проверяем структуру таблицы calls для определения названия колонки с временем завершения звонка
                    structure_query = """
                    SHOW COLUMNS FROM calls
                    WHERE Field LIKE '%end%' OR Field LIKE '%finish%' OR Field LIKE '%duration%'
                    """
                    cursor.execute(structure_query)
                    columns = cursor.fetchall()

                    avg_time = "3:15"  # Значение по умолчанию

                    # Если нашли нужную колонку, используем её
                    if columns:
                        end_column = columns[0]["Field"]
                        logger.info(
                            f"Найдена колонка для времени окончания звонка: {end_column}"
                        )

                        avg_time_query = f"""
                        SELECT AVG(TIMESTAMPDIFF(SECOND, datetime, {end_column})) as avg_seconds
                        FROM calls
                        WHERE DATE(datetime) = CURDATE()
                        AND {end_column} IS NOT NULL
                        """
                        try:
                            cursor.execute(avg_time_query)
                            avg_time_result = cursor.fetchone()

                            if avg_time_result and avg_time_result["avg_seconds"]:
                                avg_seconds = avg_time_result["avg_seconds"]
                                avg_minutes = int(avg_seconds // 60)
                                avg_seconds_remainder = int(avg_seconds % 60)
                                avg_time = f"{avg_minutes}:{avg_seconds_remainder:02d}"
                        except Exception as e:
                            logger.error(
                                f"Ошибка при расчете среднего времени: {str(e)}"
                            )

                    logger.info(
                        f"Статистика звонков: всего {total_calls}, среднее время {avg_time}"
                    )

                    return jsonify({"total_calls": total_calls, "avg_time": avg_time})
            finally:
                connection.close()
        else:
            logger.error("Не удалось установить соединение с базой данных")
            return jsonify({"total_calls": 42, "avg_time": "3:15"})
    except Exception as e:
        logger.error(f"Ошибка при получении статистики звонков: {str(e)}")
        return jsonify({"total_calls": 42, "avg_time": "3:15"})


@calls.route("/finesse/test-connection", methods=["GET"])
def test_finesse_connection():
    finesse_url = "http://uccx1.teztour.com:8082/finesse/api/SystemInfo"
    auth = ("test", "test")

    try:
        response = requests.get(finesse_url, auth=auth, timeout=10)

        # Возвращаем ответ в формате XML
        return Response(
            response.text, content_type="application/xml", status=response.status_code
        )
    except requests.Timeout:
        return jsonify({"error": "Request to Finesse timed out"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@calls.route("/finesse/proxy/agents", methods=["GET"])
def get_agents_status():
    # Проверяем авторизацию пользователя
    token = request.headers.get("X-Session-Token")

    if not token or token not in active_sessions:
        return jsonify({"error": "Требуется авторизация"}), 401

    # Получаем данные сессии
    session_data = active_sessions[token]

    # Проверяем время жизни сессии
    if time.time() - session_data["timestamp"] > 8 * 60 * 60:
        # Сессия истекла
        del active_sessions[token]
        return jsonify({"error": "Сессия истекла"}), 401

    # Используем учетные данные из сессии
    username, password = session_data["credentials"]

    finesse_url = "http://uccx1.teztour.com:8082/finesse/api/Users"

    auth = (username, password)  # Используем учетные данные из сессии

    try:
        response = requests.get(finesse_url, auth=auth, timeout=10)

        print(f"Запрос к Finesse API, статус: {response.status_code}")

        if response.status_code != 200:
            error_message = f"Finesse API вернул код {response.status_code}"
            print(error_message)
            if response.status_code == 401:
                error_message = "Ошибка авторизации в API Finesse. Требуются учетные данные с правами на просмотр операторов."
            return jsonify({"error": error_message}), response.status_code

        # Добавим отладочную информацию
        print(f"Ответ от Finesse API: {response.text[:200]}...")

        # Преобразуем XML в JSON для удобства обработки
        xml_content = response.text
        try:
            data_dict = xmltodict.parse(xml_content)
            # Возвращаем данные в формате JSON
            return jsonify(data_dict)
        except Exception as e:
            print(f"Ошибка при парсинге XML: {str(e)}")
            return jsonify({"error": f"Ошибка парсинга XML: {str(e)}"}), 500

    except requests.Timeout:
        return jsonify({"error": "Превышено время ожидания запроса к Finesse API"}), 504
    except Exception as e:
        print(f"Общая ошибка: {str(e)}")
        return jsonify({"error": str(e)}), 500


@calls.route("/finesse/proxy/calls", methods=["GET"])
def get_finesse_calls():
    """Получение активных звонков из Finesse API"""
    # Проверяем токен в заголовке
    token = request.headers.get("X-Session-Token")

    if not token or token not in active_sessions:
        return jsonify({"error": "Требуется авторизация"}), 401

    # Получаем данные сессии
    session_data = active_sessions[token]
    username, password = session_data["credentials"]

    try:
        # Изменяем URL API для получения звонков агента
        # Здесь используем имя пользователя для получения диалогов конкретного агента
        finesse_url = (
            f"http://uccx1.teztour.com:8082/finesse/api/User/{username}/Dialogs"
        )

        print(f"Отправка запроса к API: {finesse_url}")

        response = requests.get(finesse_url, auth=(username, password), timeout=10)

        print(f"Получен ответ с кодом: {response.status_code}")

        if response.status_code == 200:
            # Обрабатываем XML ответ
            data = xmltodict.parse(response.text)

            # Логирование данных для отладки
            print(f"Получены данные о звонках: {data}")

            return jsonify(data)
        elif response.status_code == 404:
            # Пробуем альтернативный URL для всех диалогов
            alt_url = "http://uccx1.teztour.com:8082/finesse/api/Team/1/Dialogs"
            print(f"Попытка запроса к альтернативному API: {alt_url}")

            alt_response = requests.get(alt_url, auth=(username, password), timeout=10)

            if alt_response.status_code == 200:
                data = xmltodict.parse(alt_response.text)
                print(f"Получены данные из альтернативного API: {data}")
                return jsonify(data)
            else:
                return (
                    jsonify(
                        {
                            "error": f"API вернул ошибку: {response.status_code} и альтернативный API вернул {alt_response.status_code}",
                            "message": "Не удалось получить данные о звонках",
                        }
                    ),
                    500,
                )
        else:
            return (
                jsonify(
                    {
                        "error": f"API вернул ошибку: {response.status_code}",
                        "message": "Не удалось получить данные о звонках",
                    }
                ),
                response.status_code,
            )

    except Exception as e:
        print(f"Ошибка при получении звонков: {str(e)}")
        traceback.print_exc()  # Вывод полного стека ошибки
        return jsonify({"error": str(e)}), 500


@calls.route("/finesse-auth-test")
def finesse_auth_test():
    return render_template("finesse_auth_test.html")


@calls.route("/finesse/login", methods=["POST"])
def finesse_login():
    if not request.is_json:
        return jsonify({"success": False, "error": "Неверный формат запроса"}), 400

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return (
            jsonify(
                {"success": False, "error": "Имя пользователя и пароль обязательны"}
            ),
            400,
        )

    # Проверка учетных данных
    finesse_url = f"http://uccx1.teztour.com:8082/finesse/api/User/{username}"
    try:
        response = requests.get(finesse_url, auth=(username, password), timeout=10)
        if response.status_code == 200:
            # Успешная авторизация
            # session_token = str(uuid.uuid4()) # <<< УДАЛЯЕМ генерацию токена

            # Получаем реальные данные пользователя из ответа API
            try:
                data = xmltodict.parse(response.text)
                user_data = data.get('User', {})

                user = {
                    "username": username,
                    "displayName": f"{user_data.get('firstName', '')} {user_data.get('lastName', '')}".strip(),
                    "extension": user_data.get('extension', ''),
                    "role": user_data.get('roles', {}).get('role', 'Agent'),
                }
            except Exception as e:
                logger.error(f"Ошибка при парсинге данных пользователя: {str(e)}")
                user = {
                    "username": username,
                    "displayName": "Пользователь",
                    "extension": "",
                    "role": "Agent",
                }

            # Сохраняем данные сессии Flask
            flask_session["finesse_authenticated"] = True
            flask_session["finesse_user"] = user
            flask_session["finesse_credentials"] = (username, password) # <<< СОХРАНЯЕМ учетные данные

            # <<< НАЧАЛО ИЗМЕНЕНИЯ: Логируем сессию ПОСЛЕ записи >>>
            logger.info(f"[finesse_login] Session content after setting keys: {dict(flask_session)}")
            # <<< КОНЕЦ ИЗМЕНЕНИЯ >>>

            # Сохраняем токен в памяти сервера # <<< УДАЛЯЕМ блок active_sessions
            # active_sessions[session_token] = {
            #     "user": user,
            #     "timestamp": time.time(),
            #     "credentials": (username, password),
            # }

            return jsonify({"success": True, "user": user}) # <<< УДАЛЯЕМ token из ответа
        else:
            return jsonify({"success": False, "error": "Ошибка авторизации"}), 401
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@calls.route("/finesse/session", methods=["GET"])
def finesse_session():
    """Проверка авторизации пользователя в Finesse и создание сессии"""
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Basic "):
        return jsonify({"authenticated": False, "error": "Отсутствует Basic авторизация"}), 401

    try:
        # Извлекаем учетные данные из заголовка
        auth_data = auth_header.replace("Basic ", "")
        auth_bytes = base64.b64decode(auth_data)
        auth_str = auth_bytes.decode("utf-8")
        username, password = auth_str.split(":", 1)

        # Создаем уникальный токен сессии
        session_token = str(uuid.uuid4())

        # Проверяем соединение с Finesse API
        finesse_url = "http://uccx1.teztour.com:8082/finesse/api/User/" + username
        response = requests.get(
            finesse_url,
            auth=(username, password),
            timeout=10
        )

        if response.status_code != 200:
            return jsonify({
                "authenticated": False,
                "error": f"Ошибка авторизации в Finesse (код {response.status_code})"
            }), 401

        # Парсим XML-ответ
        user_data = xmltodict.parse(response.text)

        # Извлекаем нужные данные пользователя
        user_info = user_data.get("User", {})
        user = {
            "loginId": user_info.get("loginId"),
            "firstName": user_info.get("firstName"),
            "lastName": user_info.get("lastName"),
            "extension": user_info.get("extension"),
            "state": user_info.get("state"),
            "stateChangeTime": user_info.get("stateChangeTime"),
            "team": user_info.get("team")
        }

        # Сохраняем данные сессии
        active_sessions[session_token] = {
            "timestamp": time.time(),
            "credentials": (username, password),
            "user": user
        }

        # <<< НАЧАЛО ИЗМЕНЕНИЯ: Сохраняем состояние Finesse в сессию Flask >>>
        flask_session["finesse_authenticated"] = True
        flask_session["finesse_user"] = user
        flask_session["finesse_credentials"] = (username, password)
        logger.info(f"[finesse_session] Finesse authenticated state set in flask_session for user {username}")
        # <<< КОНЕЦ ИЗМЕНЕНИЯ >>>

        # Возвращаем успешный ответ с токеном и данными пользователя
        return jsonify({
            "authenticated": True,
            # "token": session_token, # Токен больше не нужен
            "user": user
        })

    except Exception as e:
        logger.error(f"Ошибка при авторизации в Finesse: {str(e)}")
        return jsonify({"authenticated": False, "error": str(e)}), 500


@calls.route("/finesse/agent/state", methods=["GET", "POST"])
def finesse_agent_state():
    """Получение или изменение статуса агента"""
    # <<< НАЧАЛО ИЗМЕНЕНИЯ: Логируем содержимое сессии >>>
    logger.debug(f"[finesse_agent_state] Current flask_session content: {dict(flask_session)}")
    # <<< КОНЕЦ ИЗМЕНЕНИЯ >>>

    # <<< НАЧАЛО ИЗМЕНЕНИЯ: Проверяем сессию Flask и извлекаем учетные данные >>>
    if not flask_session.get("finesse_authenticated"):
         logger.warning(f"[finesse_agent_state] Пользователь не аутентифицирован в Finesse.")
         return jsonify({"success": False, "error": "Требуется авторизация Finesse"}), 401

    credentials = flask_session.get("finesse_credentials")
    if not credentials:
         # Используем безопасное извлечение имени пользователя для лога
         user_info_from_session = flask_session.get('finesse_user', {})
         username_for_log = user_info_from_session.get('loginId', '[unknown]')
         logger.error(f"[finesse_agent_state] Учетные данные Finesse не найдены в сессии для пользователя {username_for_log}")
         return jsonify({"success": False, "error": "Ошибка сессии: Учетные данные Finesse отсутствуют"}), 500
    username, password = credentials
    # <<< КОНЕЦ ИЗМЕНЕНИЯ >>>

    logger.info(f"[finesse_agent_state] Используются учетные данные для пользователя: {username}")

    # Для метода GET возвращаем текущий статус
    if request.method == "GET":
        try:
            # Запрос к API Finesse для получения текущего статуса
            finesse_url = f"http://uccx1.teztour.com:8082/finesse/api/User/{username}"
            logger.info(f"[finesse_agent_state GET] Запрос к Finesse URL: {finesse_url}")
            response = requests.get(
                finesse_url,
                auth=(username, password),
                timeout=10
            )
            logger.info(f"[finesse_agent_state GET] Ответ от Finesse: Статус {response.status_code}")

            if response.status_code != 200:
                return jsonify({
                    "success": False,
                    "error": f"Ошибка получения статуса (код {response.status_code})"
                }), response.status_code

            # Парсим XML-ответ
            user_data = xmltodict.parse(response.text)
            user_info = user_data.get("User", {})

            # <<< НАЧАЛО ИЗМЕНЕНИЯ: Обновляем flask_session >>>
            current_finesse_user = flask_session.get("finesse_user")
            if current_finesse_user:
                 current_finesse_user["state"] = user_info.get("state")
                 current_finesse_user["stateChangeTime"] = user_info.get("stateChangeTime")
                 # Помечаем сессию как измененную, чтобы Flask-Session ее сохранил
                 flask_session.modified = True
            else:
                 logger.warning("[finesse_agent_state GET] finesse_user не найден в сессии для обновления.")
            # <<< КОНЕЦ ИЗМЕНЕНИЯ >>>

            return jsonify({
                "success": True,
                "state": user_info.get("state"),
                "stateChangeTime": user_info.get("stateChangeTime")
            })

        except Exception as e:
            logger.error(f"Ошибка при получении статуса агента: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500

    # Для метода POST изменяем статус
    elif request.method == "POST":
        try:
            # Получаем новый статус из запроса
            data = request.get_json()
            new_state = data.get("state")

            if not new_state:
                return jsonify({"success": False, "error": "Не указан новый статус"}), 400

            # Подготавливаем XML для запроса изменения статуса
            xml_data = f"""<?xml version="1.0" encoding="UTF-8"?>
                <User>
                    <state>{new_state}</state>
                </User>
            """

            # Запрос к API Finesse для изменения статуса
            finesse_url = f"http://uccx1.teztour.com:8082/finesse/api/User/{username}"
            response = requests.put(
                finesse_url,
                auth=(username, password),
                data=xml_data,
                headers={"Content-Type": "application/xml"},
                timeout=10
            )

            if response.status_code in [200, 202]:
                # <<< НАЧАЛО ИЗМЕНЕНИЯ: Обновляем flask_session >>>
                current_finesse_user = flask_session.get("finesse_user")
                if current_finesse_user:
                    current_finesse_user["state"] = new_state
                    current_finesse_user["stateChangeTime"] = datetime.datetime.now().isoformat()
                    # Помечаем сессию как измененную
                    flask_session.modified = True
                else:
                    logger.warning("[finesse_agent_state POST] finesse_user не найден в сессии для обновления.")
                # <<< КОНЕЦ ИЗМЕНЕНИЯ >>>

                return jsonify({
                    "success": True,
                    "message": f"Статус изменен на {new_state}"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": f"API вернул ошибку: {response.status_code}"
                }), response.status_code

        except Exception as e:
            logger.error(f"Ошибка при изменении статуса агента: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500


@calls.route("/finesse/agents/status", methods=["GET"])
def finesse_agents_status():
    """Получение статусов всех операторов"""
    # <<< НАЧАЛО ИЗМЕНЕНИЯ: Логируем содержимое сессии >>>
    logger.debug(f"[finesse_agents_status] Current flask_session content: {dict(flask_session)}")
    # <<< КОНЕЦ ИЗМЕНЕНИЯ >>>

    # <<< НАЧАЛО ИЗМЕНЕНИЯ: Проверяем сессию Flask >>>
    if not flask_session.get("finesse_authenticated"):
         logger.warning(f"[finesse_agents_status] Пользователь не аутентифицирован в Finesse.")
         return jsonify({"success": False, "error": "Требуется авторизация Finesse"}), 401

    credentials = flask_session.get("finesse_credentials")
    if not credentials:
         logger.error(f"[finesse_agents_status] Учетные данные Finesse не найдены в сессии для пользователя {flask_session.get('finesse_user', {}).get('username')}")
         return jsonify({"success": False, "error": "Ошибка сессии: Учетные данные Finesse отсутствуют"}), 500
    username, password = credentials
    # <<< КОНЕЦ ИЗМЕНЕНИЯ >>>

    # Получаем данные сессии # <<< УДАЛЯЕМ блок >>>
    # session_data = active_sessions[token]
    # username, password = session_data["credentials"]
    logger.info(f"[finesse_agents_status] Используются учетные данные для пользователя: {username}") # Лог пользователя
    # <<< НАЧАЛО ИЗМЕНЕНИЯ: Добавляем логирование пароля и URL >>>
    # logger.info(f"[finesse_agents_status] Проверка учетных данных - Username: '{username}', Password: '{password}'")

    try:
        # Запрос к API Finesse для получения списка всех операторов
        finesse_url = "http://uccx1.teztour.com:8082/finesse/api/Users"
        # <<< НАЧАЛО ИЗМЕНЕНИЯ: Логируем URL и статус ответа >>>
        logger.info(f"[finesse_agents_status] Запрос к Finesse URL: {finesse_url}") # Лог URL
        auth = (username, password)
        response = requests.get(
            finesse_url,
            auth=auth,
            timeout=15
        )
        logger.info(f"[finesse_agents_status] Ответ от Finesse: Статус {response.status_code}") # Лог ответа Finesse
        # <<< КОНЕЦ ИЗМЕНЕНИЯ >>>

        if response.status_code != 200:
            # <<< НАЧАЛО ИЗМЕНЕНИЯ: Логируем тело ошибки, если есть >>>
            error_body = response.text[:500] # Ограничим длину на всякий случай
            logger.error(f"[finesse_agents_status] Ошибка от Finesse API ({response.status_code}): {error_body}")
            # <<< КОНЕЦ ИЗМЕНЕНИЯ >>>
            return jsonify({
                "success": False,
                "error": f"Ошибка получения списка операторов (код {response.status_code})"
            }), response.status_code

        # Парсим XML-ответ
        users_data = xmltodict.parse(response.text)
        users = users_data.get("Users", {}).get("User", [])

        # Если вернулся только один пользователь, преобразуем его в список
        if not isinstance(users, list):
            users = [users]

        # Форматируем данные пользователей
        formatted_users = []
        for user in users:
            # Пропускаем системных пользователей или супервизоров без extension
            if not user.get("extension"):
                continue

            formatted_users.append({
                "loginId": user.get("loginId"),
                "firstName": user.get("firstName"),
                "lastName": user.get("lastName"),
                "displayName": f"{user.get('firstName', '')} {user.get('lastName', '')}".strip(),
                "extension": user.get("extension"),
                "status": user.get("state"),
                "team": user.get("teamName"),
                "lastStateChange": user.get("stateChangeTime")
            })

        # Сортируем пользователей по имени
        formatted_users.sort(key=lambda x: x["displayName"])

        return jsonify(formatted_users)

    except Exception as e:
        logger.error(f"Ошибка при получении статусов операторов: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@calls.route("/finesse/logout", methods=["POST"])
def finesse_logout():
    """Выход пользователя и очистка сессии"""
    # token = request.headers.get("X-Session-Token") # <<< УДАЛЯЕМ работу с токеном >>>

    # <<< НАЧАЛО ИЗМЕНЕНИЯ: Очищаем сессию Flask >>>
    flask_session.pop("finesse_authenticated", None)
    flask_session.pop("finesse_user", None)
    flask_session.pop("finesse_credentials", None)
    logger.info("Сессия Finesse очищена в flask_session.")
    # <<< КОНЕЦ ИЗМЕНЕНИЯ >>>

    # Если токен найден в активных сессиях, удаляем его # <<< УДАЛЯЕМ блок active_sessions >>>
    # if token in active_sessions:
    #     del active_sessions[token]
    #     return jsonify({"success": True, "message": "Выход выполнен успешно"})

    # Если токен не найден, возвращаем сообщение об успехе (пользователь уже вышел)
    return jsonify({"success": True, "message": "Выход выполнен успешно"})


@calls.route("/finesse/health-check", methods=["GET"])
def finesse_health_check():
    """Проверка доступности API Finesse"""
    try:
        # Проверяем доступность API Finesse
        finesse_url = "http://uccx1.teztour.com:8082/finesse/api/SystemInfo"
        response = requests.get(finesse_url, timeout=5)

        if response.status_code == 200:
            return jsonify({"status": "ok", "message": "API Finesse доступно"})
        else:
            return jsonify({"status": "error", "message": f"API Finesse недоступно, код: {response.status_code}"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Ошибка при проверке API: {str(e)}"})


@calls.route("/finesse/check-token", methods=["POST"])
def check_token_validity():
    """Проверка валидности токена без перезагрузки страницы"""
    if not request.is_json:
        return jsonify({"valid": False, "error": "Неверный формат запроса"}), 400

    data = request.get_json()
    token = data.get("token")

    if not token:
        return jsonify({"valid": False, "error": "Токен не предоставлен"}), 400

    # Проверяем токен в хранилище активных сессий
    if token in active_sessions:
        session_data = active_sessions[token]

        # Проверяем время жизни сессии
        if time.time() - session_data["timestamp"] > 8 * 60 * 60:
            # Сессия истекла
            del active_sessions[token]
            return jsonify({"valid": False, "error": "Сессия истекла"})

        # Обновляем время активности
        session_data["timestamp"] = time.time()

        # Возвращаем данные пользователя
        return jsonify({
            "valid": True,
            "user": session_data.get("user", {})
        })

    return jsonify({"valid": False, "error": "Недействительный токен"})


def setup_session_cleaner():
    """Настройка автоматической очистки устаревших сессий"""
    def clean_old_sessions():
        now = time.time()
        expired_tokens = []

        # <<< ИЗМЕНЕНИЕ: УДАЛЯЕМ логику очистки active_sessions >>>
        # for token, session_data in active_sessions.items():
        #     # Если сессия старше 8 часов, помечаем ее как устаревшую
        #     if now - session_data.get("timestamp", 0) > 8 * 60 * 60:
        #         expired_tokens.append(token)
        #
        # # Удаляем устаревшие сессии
        # for token in expired_tokens:
        #     del active_sessions[token]

        # Просто логируем, что планировщик жив (если нужно)
        logger.debug("Планировщик очистки сессий активен (логика active_sessions удалена).")

        # Планируем следующую очистку через час
        threading.Timer(3600, clean_old_sessions).start()

    # Запускаем первую очистку
    threading.Timer(3600, clean_old_sessions).start()


# Новая функция для тестирования соединений
@calls.route('/test-oracle-connections')
def test_oracle_connections():
    results = {}
    try:
        with SessionOracleCRM() as session:
            results['crm_test'] = str(session.execute(text("SELECT 1 FROM DUAL")).fetchone())
            tables_result = session.execute(text("SELECT table_name FROM user_tables")).fetchall()
            results['crm_tables'] = [t[0] for t in tables_result] if tables_result else []
    except Exception as e:
        results['crm_error'] = str(e)

    try:
        with SessionSalesSchema() as session:
            results['sales_test'] = str(session.execute(text("SELECT 1 FROM DUAL")).fetchone())
            tables_result = session.execute(text("SELECT table_name FROM user_tables")).fetchall()
            results['sales_tables'] = [t[0] for t in tables_result] if tables_result else []

            # Проверка существования и структуры таблицы T_CALL_INFO
            try:
                column_result = session.execute(text("""
                    SELECT column_name FROM all_tab_columns
                    WHERE table_name = 'T_CALL_INFO'
                    """)).fetchall()
                results['call_info_columns'] = [c[0] for c in column_result] if column_result else []

                # Проверка наличия данных
                count_result = session.execute(text("SELECT COUNT(*) FROM T_CALL_INFO")).fetchone()
                results['call_info_count'] = count_result[0] if count_result else 0
            except Exception as e:
                results['call_info_error'] = str(e)
    except Exception as e:
        results['sales_error'] = str(e)

    return jsonify(results)


@calls.route("/contact-center/vilnius/tel/", methods=["GET"])
def contact_center_vilnius_tel():
    # Получаем номер телефона из запроса
    ani = request.args.get("ani", "")
    current_ani = flask_session.get("current_ani", "")
    type_request = request.args.get("type", "")

    # Принудительно сбрасываем флаги обновления при каждом запросе newcall
    if type_request == "newcall":
        # Сбрасываем флаги обновления
        if "name_updated" in flask_session:
            flask_session.pop("name_updated")
            logger.info("Сброшен флаг name_updated")
        if "manager_updated" in flask_session:
            flask_session.pop("manager_updated")
            logger.info("Сброшен флаг manager_updated")
        if ani != current_ani:
            if "pk_record" in flask_session:
                flask_session.pop("pk_record")
                logger.info(f"Сброшен pk_record для нового номера: {ani}")
            flask_session["current_ani"] = ani
            logger.info(f"Установлен новый номер в сессии: {ani}")

    # Получаем тип запроса - может быть newcall или endcall
    request_type = request.args.get("type", "")

    # Если это завершение звонка, обрабатываем соответствующим образом
    if request_type == "endcall":
        # Логика для завершения звонка
        logger.info(f"Обработка завершения звонка для номера {ani}")
        # Возвращаем шаблон завершения звонка
        return render_template("endcall.html", ani=ani)

    # Для новых звонков (type=newcall) или если тип не указан
    # Удаляем все пробелы и символы '+' из номера
    clean_ani_input = ani.replace(" ", "").lstrip('+') # Используем новое имя для входного чистого ani

    logger.info(f"Поиск агентства по очищенному телефону: {clean_ani_input}")

    # <<< НАЧАЛО ИЗМЕНЕНИЯ: Проверка на пустой номер >>>
    if not clean_ani_input:
        logger.warning("Номер телефона не указан или пуст.")
        return render_template("agency_not_found.html", ani=ani)
    # <<< КОНЕЦ ИЗМЕНЕНИЯ >>>

    try:
        # Получаем данные агентства
        with SessionOracleCRM() as session_crm:
            # Поиск агентства по телефону с улучшенным поиском
            sql = text("""
            SELECT AGENCY_ID, AGENCY_PHONE
            FROM T_AGENCY_PHONE
            WHERE REPLACE(AGENCY_PHONE, ' ', '') LIKE :phone
            """)

            # Для большей надежности ищем только по цифрам номера
            clean_ani_digits = ''.join(c for c in clean_ani_input if c.isdigit()) # Используем чистое имя clean_ani_digits

            # <<< НАЧАЛО ИЗМЕНЕНИЯ: Проверка на пустые цифры >>>
            if not clean_ani_digits:
                logger.warning(f"Не удалось извлечь цифры из номера: '{clean_ani_input}'. Поиск агентства невозможен.")
                return render_template("agency_not_found.html", ani=ani)
            # <<< КОНЕЦ ИЗМЕНЕНИЯ >>>

            logger.info(f"Поиск по чистым цифрам номера: {clean_ani_digits}")
            agency = session_crm.execute(sql, {'phone': f'%{clean_ani_digits}%'}).fetchone()

            if not agency:
                logger.warning(f"Агентство с телефоном {ani} ({clean_ani_digits}) не найдено")
                return render_template("agency_not_found.html", ani=ani)

            # Здесь определяем agency_id
            agency_id = agency[0]
            logger.info(f"Найдено агентство с ID: {agency_id}")

        # Получаем историю звонков через прямой запрос
        call_history = []
        last_call = None

        try:
            with SessionSalesSchema() as session_sales:
                # Запрос к истории звонков с правильным форматированием даты
                call_history_sql = text(
                    """
                SELECT
                    CALL_INFO_ID,
                    TIME_BEGIN,
                    TIME_END,
                    PHONE_NUMBER,
                    CURRATOR,
                    REGION,
                    AGENCY_MANAGER,
                    AGENCY_NAME
                FROM T_CALL_INFO
                WHERE AGENCY_ID = :agency_id
                ORDER BY TIME_BEGIN DESC
                """
                )

                # Выполняем запрос
                call_history_result = session_sales.execute(
                    call_history_sql, {'agency_id': str(agency_id)}
                ).fetchall()

                # Преобразуем результаты в список словарей
                if call_history_result:
                    call_history = []
                    for row in call_history_result:
                        # Создаем словарь вручную
                        call_dict = {}
                        for column_name in row._fields:
                            call_dict[column_name] = getattr(row, column_name)
                        call_history.append(call_dict)

                    # Первый результат - последний звонок
                    if call_history:
                        last_call = call_history[0]

                logger.info(f"Получено {len(call_history)} записей истории звонков")
        except Exception as e:
            logger.error(f"Error getting call history: {str(e)}")
            traceback.print_exc()
            # Продолжаем выполнение даже если история звонков недоступна

        # Перед рендерингом шаблона добавим отладочный вывод:
        logger.info(f"Last call data: {last_call if last_call else 'None'}")
        if call_history:
            logger.info(f"First call history record keys: {list(call_history[0].keys())}")

        try:
            # Получаем данные агентства из XML-шлюза
            # Аутентификация в XML API
            auth_url = XML_AUTH_URL
            response = requests.get(auth_url, timeout=10)
            sess_id = etree.fromstring(response.content).findtext("sessionId")

            # Запрос данных агентства
            agency_url = f"http://xml.teztour.com/xmlgate/agency/view?agencyId={agency_id}&aid={sess_id}"
            logger.info(f"Запрос данных агентства через XML API: {agency_url}")
            response_agency = requests.get(agency_url, timeout=10)
            root = etree.fromstring(response_agency.content)

            # Извлекаем данные агентства из XML
            agency_data = {}

            # Базовые данные агентства
            agency_data['agency_name'] = root.findtext(".//name", f"Имя агентства не получено (ID: {agency_id})")
            agency_data['company_name_en'] = root.findtext(".//nameEng", "")
            agency_data['agency_city'] = root.findtext(".//city", "")
            agency_data['agency_percent'] = root.findtext(".//percent", "")
            agency_data['agency_front_office'] = root.findtext(".//frontOffice", "")
            agency_data['agency_contract'] = root.findtext(".//contract", "")
            agency_data['agency_quantity_tourists'] = root.findtext(".//sentTourists", "0")
            agency_data['agency_boss'] = root.findtext(".//boss", "")
            agency_data['agency_curator_name'] = root.findtext(".//curator/fullName", "")
            agency_data['agency_blacklist'] = "Yes" if root.findtext(".//blackList") == "true" else "No"

            # Получаем сотрудников агентства
            managers = root.findall(".//managers/manager")
            agency_data['agency_employee'] = " / ".join([m.text for m in managers if m.text is not None])

            # Ищем контактную информацию, связанную с номером телефона
            clean_ani = ani.replace("+", "").replace(" ", "")
            contact_found = False
            for contact in root.findall(".//contacts/contact"):
                contact_value = contact.findtext("value", "")
                if contact_value and clean_ani in contact_value.replace("+", "").replace(" ", ""):
                    agency_data['agency_contact_person'] = contact.findtext("person", "")
                    agency_data['agency_contact_description'] = contact.findtext("description", "")
                    contact_found = True
                    logger.info(f"Найдена контактная информация для номера {ani}")
                    break

            if not contact_found:
                agency_data['agency_contact_person'] = ""
                agency_data['agency_contact_description'] = ""
                logger.warning(f"Контактная информация для номера {ani} не найдена")

            logger.info(f"Получены данные агентства из XML: {agency_data['agency_name']}")

            # Добавить после успешного получения данных агентства из XML
            # Примерно после строки: logger.info(f"Получены данные агентства из XML: {agency_data['agency_name']}")

            # Записываем данные об агентстве в базу данных call_info
            try:
                # Получаем ID записи звонка из сессии или создаем новую запись
                pk_record = flask_session.get("pk_record")
                if not pk_record:
                    # Создаем новую запись звонка
                    with session_scope() as db_session:
                        pk_record = record_stat_to_db(db_session,
                                                     curator=request.args.get("curator_id", ""),
                                                     ag_id=agency_id,
                                                     tel=ani)
                        flask_session["pk_record"] = pk_record
                        logger.info(f"Создана новая запись о звонке с ID: {pk_record}")

                # Обновляем имя агентства в записи звонка
                if pk_record and agency_data.get('agency_name') and agency_id != '0' and 'name_updated' not in flask_session:
                    write_agency_name(pk_record, agency_data['agency_name'], engine_sales_schema)
                    flask_session['name_updated'] = True
                    logger.info(f"Обновлено имя агентства для звонка {pk_record}: {agency_data['agency_name']}")

                # Обновляем менеджера агентства в записи звонка
                if pk_record and agency_data.get('agency_contact_person') and 'manager_updated' not in flask_session:
                    write_agency_manager(pk_record, agency_data['agency_contact_person'], engine_sales_schema)
                    flask_session['manager_updated'] = True
                    logger.info(f"Обновлен менеджер агентства для звонка {pk_record}: {agency_data['agency_contact_person']}")
            except Exception as e:
                logger.error(f"Ошибка при записи данных агентства в T_CALL_INFO: {str(e)}")
                traceback.print_exc()
        except Exception as e:
            logger.error(f"Ошибка при получении данных агентства: {str(e)}")
            traceback.print_exc()
            agency_data = {
                'agency_name': f'Ошибка при получении данных (ID: {agency_id})',
                'company_name_en': '',
                'agency_city': '',
                'agency_percent': '',
                'agency_front_office': '',
                'agency_contract': '',
                'agency_quantity_tourists': '0',
                'agency_boss': '',
                'agency_curator_name': '',
                'agency_blacklist': 'No',
                'agency_contact_person': '',
                'agency_contact_description': '',
                'agency_employee': ''
            }
    except Exception as e:
        logger.error(f"Ошибка при получении данных агентства: {str(e)}")
        traceback.print_exc()
        agency_data = {
            'agency_name': f'Ошибка при получении данных (ID: {agency_id})',
            'company_name_en': '',
            'agency_city': '',
            'agency_employee': ''
        }

    # Если это новый звонок и указан curator_id
    if request_type == "newcall" and request.args.get("curator_id"):
        # Рендерим шаблон для карточки звонящего агента
        return render_template(
            "agency_data.html",
            agency=agency_data,
            agency_id=agency_id,
            call_history=call_history,
            last_call=last_call,
            call=last_call,
            calls=call_history,
            phone_number=f"+{ani}",
            agency_name=agency_data.get('agency_name', f'Имя агентства не получено (ID: {agency_id})'),
            curator=request.args.get("curator_id", ""),
            ani=ani,
            curator_id=request.args.get("curator_id")
        )

    # В других случаях - обычный шаблон contact_center
    return render_template(
        "contact_center.html",
        agency_id=agency_id,
        call_history=call_history,
        last_call=last_call
    )


def get_last_calls_safe(agency_id: str, limit: int = 6) -> List[Dict[str, Any]]:
    """Безопасная версия функции get_last_calls, использующая прямые SQL запросы"""
    try:
        with SessionSalesSchema() as session:
            query = text("""
            SELECT
                CALL_INFO_ID, TIME_BEGIN, TIME_END, PHONE_NUMBER,
                CURRATOR, THEME, REGION, AGENCY_MANAGER, AGENCY_NAME,
                CASE
                    WHEN TIME_END IS NOT NULL THEN
                        CASE
                            WHEN (TIME_END - TIME_BEGIN) * 86400 < 60 THEN
                                TO_CHAR(TRUNC((TIME_END - TIME_BEGIN) * 86400)) || ' seconds'
                            ELSE
                                TO_CHAR(TRUNC((TIME_END - TIME_BEGIN) * 86400 / 60)) || ' minutes ' ||
                                TO_CHAR(MOD(TRUNC((TIME_END - TIME_BEGIN) * 86400), 60)) || ' seconds'
                        END
                    ELSE 'In progress'
                END as CALL_DURATION
            FROM T_CALL_INFO
            WHERE AGENCY_ID = :agency_id
            ORDER BY CALL_INFO_ID DESC
            FETCH FIRST :limit ROWS ONLY
            """)
            result = session.execute(query, {"agency_id": agency_id, "limit": limit}).fetchall()
            return [dict(row) for row in result]
    except Exception as e:
        logger.error(f"Ошибка при получении истории звонков: {str(e)}")
        traceback.print_exc()
        return []


@calls.route("/finesse/check-connection", methods=["HEAD", "GET"])
def finesse_check_connection():
    """Простой эндпоинт для проверки соединения с Finesse API"""
    try:
        # Можно добавить реальную проверку соединения с Finesse
        # Пока просто возвращаем успешный статус
        if request.method == "HEAD":
            return "", 200
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"Ошибка проверки соединения: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@calls.route("/api/calls")
def get_calls():
    """Алиас для get_moscow_calls для совместимости с JS"""
    return get_moscow_calls()

# Глобальная переменная для кэширования
_calls_cache = None
_cache_timestamp = None

def get_cached_calls():
    """Возвращает кэшированные данные о звонках, если они актуальны"""
    global _calls_cache, _cache_timestamp

    if not _calls_cache or not _cache_timestamp:
        return None

    # Проверяем, не устарел ли кэш (30 секунд)
    if (datetime.datetime.now() - _cache_timestamp).total_seconds() > 30:
        return None

    return _calls_cache

def update_calls_cache(calls):
    """Обновляет кэш звонков"""
    global _calls_cache, _cache_timestamp
    _calls_cache = calls
    _cache_timestamp = datetime.datetime.now()


@calls.route("/api/moscow-operator-stats")
def get_moscow_operator_stats():
    """Возвращает статистику звонков по операторам за указанную дату."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    try:
        # Получаем дату из параметров запроса, по умолчанию - сегодня
        selected_date_str = request.args.get('date')
        if selected_date_str:
            try:
                selected_date = datetime.datetime.strptime(selected_date_str, '%Y-%m-%d').date()
                date_filter_sql = "%s"
                query_params = (selected_date,)
            except ValueError:
                logger.warning(f"Неверный формат даты для статистики: {selected_date_str}. Используется текущая дата.")
                date_filter_sql = "CURDATE()"
                query_params = ()
        else:
            selected_date = datetime.date.today()
            date_filter_sql = "CURDATE()"
            query_params = ()

        logger.info(f"Запрос статистики операторов для даты: {selected_date}")

        connection = get_db_connection()
        if not connection:
            logger.error("Не удалось подключиться к базе данных для статистики операторов")
            return jsonify({"success": False, "error": "Ошибка подключения к базе данных", "stats": []}), 500

        try:
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                query = f"""
                SELECT
                    op.name AS operator_name,
                    COUNT(cls.id) AS call_count
                FROM calls cls
                JOIN operators op ON cls.operator_id = op.id
                WHERE DATE(cls.datetime) = {date_filter_sql}
                GROUP BY cls.operator_id, op.name
                ORDER BY op.name; -- Сортируем по имени оператора
                """

                cursor.execute(query, query_params)
                stats = cursor.fetchall()

                logger.info(f"Получено {len(stats)} записей статистики операторов за {selected_date}")
                return jsonify({"success": True, "stats": stats})

        except Exception as e:
            logger.error(f"Ошибка при выполнении запроса статистики операторов: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"success": False, "error": str(e), "stats": []}), 500
        finally:
            if connection:
                connection.close()

    except Exception as e:
        logger.error(f"Общая ошибка в get_moscow_operator_stats: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e), "stats": []}), 500


@calls.route("/api/moscow-calls-monthly-stats")
def get_moscow_calls_monthly_stats():
    """Возвращает ежемесячную статистику звонков (год, месяц, количество) для графика."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.info("Запрос ежемесячной статистики звонков")

    try:
        connection = get_db_connection()
        if not connection:
            logger.error("Не удалось подключиться к базе данных для ежемесячной статистики")
            return jsonify({"success": False, "error": "Ошибка подключения к базе данных", "stats": []}), 500

        try:
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                query = """
                SELECT
                    YEAR(datetime) AS year,
                    MONTH(datetime) AS month,
                    COUNT(*) AS count
                FROM calls
                GROUP BY YEAR(datetime), MONTH(datetime)
                ORDER BY year, month;
                """
                cursor.execute(query)
                stats = cursor.fetchall()

                logger.info(f"Получено {len(stats)} записей ежемесячной статистики")
                return jsonify({"success": True, "stats": stats})

        except Exception as e:
            logger.error(f"Ошибка при выполнении запроса ежемесячной статистики: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"success": False, "error": str(e), "stats": []}), 500
        finally:
            if connection:
                connection.close()

    except Exception as e:
        logger.error(f"Общая ошибка в get_moscow_calls_monthly_stats: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e), "stats": []}), 500


@calls.route("/api/agencies")
def get_agencies():
    logger = logging.getLogger(__name__)
    search_term = request.args.get('search', '').strip()
    agencies_list = []
    connection_error = None

    connection = get_db_connection()
    if not connection:
        connection_error = "Не удалось установить соединение с базой данных для получения списка агентств"
        logger.error(connection_error)
        return jsonify({"success": False, "error": connection_error, "agencies": []}), 500

    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            base_query = """
                SELECT
                    ag.id AS ID_TR,
                    ag.name AS NAME_RU,
                    ag.english_name AS NAME_EN,
                    ag.adres AS ADDRESS,
                    c.name AS CITY_NAME,
                    m.name AS METRO_STATION_NAME,
                    d.name AS DISTRICT_NAME,
                    (SELECT t.number FROM telephone t WHERE t.id = ag.tel_1_id) AS telephone_1_number,
                    (SELECT t.number FROM telephone t WHERE t.id = ag.tel_2_id) AS telephone_2_number,
                    (SELECT t.number FROM telephone t WHERE t.id = ag.tel_3_id) AS telephone_3_number,
                    (SELECT t.number FROM telephone t WHERE t.id = ag.tel_4_id) AS telephone_4_number,
                    (SELECT t.number FROM telephone t WHERE t.id = ag.tel_5_id) AS telephone_5_number,
                    (SELECT t.number FROM telephone t WHERE t.id = ag.tel_6_id) AS telephone_6_number,
                    (SELECT t.number FROM telephone t WHERE t.id = ag.tel_7_id) AS telephone_7_number
                FROM agentstvo ag
                LEFT JOIN city c ON ag.city_id = c.id
                LEFT JOIN metro m ON ag.metro_id = m.id
                LEFT JOIN district d ON ag.district_id = d.id
                WHERE (ag.hidden = 0 OR ag.hidden IS NULL)
            """
            params = []
            if search_term:
                search_like = f"%{search_term}%"
                base_query += """ AND (
                    ag.name LIKE %s OR
                    ag.english_name LIKE %s OR
                    ag.adres LIKE %s OR
                    c.name LIKE %s OR
                    m.name LIKE %s OR
                    d.name LIKE %s OR
                    EXISTS (SELECT 1 FROM telephone t WHERE t.id = ag.tel_1_id AND t.number LIKE %s) OR
                    EXISTS (SELECT 1 FROM telephone t WHERE t.id = ag.tel_2_id AND t.number LIKE %s) OR
                    EXISTS (SELECT 1 FROM telephone t WHERE t.id = ag.tel_3_id AND t.number LIKE %s) OR
                    EXISTS (SELECT 1 FROM telephone t WHERE t.id = ag.tel_4_id AND t.number LIKE %s) OR
                    EXISTS (SELECT 1 FROM telephone t WHERE t.id = ag.tel_5_id AND t.number LIKE %s) OR
                    EXISTS (SELECT 1 FROM telephone t WHERE t.id = ag.tel_6_id AND t.number LIKE %s) OR
                    EXISTS (SELECT 1 FROM telephone t WHERE t.id = ag.tel_7_id AND t.number LIKE %s)
                ) """
                params.extend([search_like] * 13) # Было 6, стало 6 + 7 = 13
                base_query += " ORDER BY ag.name LIMIT 200" # Ограничиваем вывод, если есть поисковый запрос
            else:
                base_query += " ORDER BY ag.name" # Без LIMIT, если поискового запроса нет

            logger.debug(f"Executing agencies query: {cursor.mogrify(base_query, params) if params else base_query}")
            cursor.execute(base_query, params)
            agencies_raw = cursor.fetchall()
            logger.info(f"Найдено {len(agencies_raw)} агентств по запросу: '{search_term}'")

            agencies_list = []
            for agency_data in agencies_raw:
                all_phones_parts = []
                for i in range(1, 8):
                    phone_key = f"telephone_{i}_number"
                    if agency_data.get(phone_key):
                        all_phones_parts.append(agency_data[phone_key])
                agency_data['ALL_TELEPHONES_CONCAT'] = " ".join(filter(None, all_phones_parts))
                agencies_list.append(agency_data)

    except pymysql.MySQLError as e:
        logger.error(f"MySQL ошибка при получении списка агентств: {e}")
        return jsonify({"success": False, "error": f"Ошибка базы данных: {e}", "agencies": []}), 500
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при получении списка агентств: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": f"Внутренняя ошибка сервера: {e}", "agencies": []}), 500
    finally:
        if connection:
            connection.close()

    return jsonify({"success": True, "agencies": agencies_list})


@calls.route("/api/agency-details/<int:agency_id>")
def get_agency_details(agency_id):
    logger = logging.getLogger(__name__)
    agency_details = None
    connection_error = None

    connection = get_db_connection()
    if not connection:
        connection_error = f"Не удалось установить соединение с БД для получения деталей агентства ID: {agency_id}"
        logger.error(connection_error)
        return jsonify({"success": False, "error": connection_error}), 500

    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = """
                SELECT
                    ag.*,
                    c.name AS city_name,
                    m.name AS metro_name,
                    d.name AS district_name,
                    ar.name AS area_name,
                    rg.name AS region_name_from_db
                FROM agentstvo ag
                LEFT JOIN city c ON ag.city_id = c.id
                LEFT JOIN metro m ON ag.metro_id = m.id
                LEFT JOIN district d ON ag.district_id = d.id
                LEFT JOIN areas ar ON ag.area_id = ar.id
                LEFT JOIN regions rg ON ag.region = rg.id
                WHERE ag.id = %s AND (ag.hidden = 0 OR ag.hidden IS NULL)
            """
            logger.debug(f"Executing agency details query: {cursor.mogrify(query, (agency_id,))}")
            cursor.execute(query, (agency_id,))
            agency_details = cursor.fetchone()

            if agency_details:
                logger.info(f"Найдены детали для агентства ID: {agency_id}")
                # Получение всех телефонных номеров
                phone_fields = ['tel_1_id', 'tel_2_id', 'tel_3_id', 'tel_4_id', 'tel_5_id', 'tel_6_id', 'tel_7_id']
                phone_ids = [agency_details[pf] for pf in phone_fields if agency_details.get(pf) and agency_details[pf] > 0]

                agency_details['telephones'] = []
                if phone_ids:
                    phone_placeholders = ', '.join(['%s'] * len(phone_ids))
                    # Изменяем запрос, чтобы получать time_rezhim_id и comment из telephone
                    phone_query = f"""SELECT id, number, comment, time_rezhim_id
                                       FROM telephone
                                       WHERE id IN ({phone_placeholders})"""

                    logger.debug(f"Executing telephones query: {cursor.mogrify(phone_query, phone_ids)}")
                    cursor.execute(phone_query, phone_ids)
                    phones_data = cursor.fetchall()

                    # Для каждого телефона получаем его режим работы, если он есть
                    for phone in phones_data:
                        phone['work_schedule'] = None # Инициализируем поле для режима работы
                        time_rezhim_id_for_phone = phone.get('time_rezhim_id')
                        if time_rezhim_id_for_phone and time_rezhim_id_for_phone > 0:
                            schedule_query = "SELECT * FROM time_rezhim WHERE id = %s"
                            cursor.execute(schedule_query, (time_rezhim_id_for_phone,))
                            schedule_data = cursor.fetchone()
                            if schedule_data:
                                # Форматируем данные о режиме работы для удобства
                                formatted_schedule = {}
                                days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                                for day in days:
                                    from_time = schedule_data.get(f'{day}_from')
                                    to_time = schedule_data.get(f'{day}_to')
                                    if from_time and to_time:
                                        # Преобразуем timedelta в строку HH:MM
                                        formatted_schedule[day] = f"{str(from_time).split(':')[0]:0>2}:{str(from_time).split(':')[1]:0>2} - {str(to_time).split(':')[0]:0>2}:{str(to_time).split(':')[1]:0>2}"
                                    else:
                                        formatted_schedule[day] = "Выходной"
                                phone['work_schedule'] = formatted_schedule

                    agency_details['telephones'] = phones_data # Теперь это список телефонов с их режимами работы
                    logger.info(f"Для агентства ID {agency_id} найдено {len(phones_data)} телефонов с информацией о режиме работы.")
            else:
                logger.warning(f"Агентство с ID: {agency_id} не найдено или скрыто.")
                return jsonify({"success": False, "error": "Агентство не найдено"}), 404

    except pymysql.MySQLError as e:
        logger.error(f"MySQL ошибка при получении деталей агентства ID {agency_id}: {e}")
        return jsonify({"success": False, "error": f"Ошибка базы данных: {e}"}), 500
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при получении деталей агентства ID {agency_id}: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": f"Внутренняя ошибка сервера: {e}"}), 500
    finally:
        if connection:
            connection.close()

    return jsonify({"success": True, "agency_details": agency_details})
