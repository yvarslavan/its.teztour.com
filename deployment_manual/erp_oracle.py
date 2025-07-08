from configparser import ConfigParser
import os
import logging
from flask import flash
import oracledb

os.environ["NLS_LANG"] = "Russian.AL32UTF8"

config = ConfigParser()
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")

config.read(config_path)
db_host = config.get("oracle", "host")
db_port = config.get("oracle", "port")
db_service_name = config.get("oracle", "service_name")
db_user_name = config.get("oracle", "user_name")
db_password = config.get("oracle", "password")


def connect_oracle(
    oracle_host, oracle_port, oracle_service_name, oracle_user_name, oracle_password
):
    try:
        oracle_connection = oracledb.connect(
            user=oracle_user_name,
            password=oracle_password,
            host=oracle_host,
            port=oracle_port,
            service_name=oracle_service_name
        )
        return oracle_connection
    except oracledb.DatabaseError as e:
        logging.error("Ошибка выполнения открытия соединения: %s", str(e))
        return None


def close_oracle_connection(connection):
    if connection is not None:
        try:
            connection.close()
            print("Oracle connection closed successfully")
        except oracledb.DatabaseError as e:
            logging.error("Ошибка выполнения закрытия соединения: %s", str(e))
    else:
        logging.warning("Попытка закрыть несуществующее соединение")


def verify_credentials(connection, login_erp_user, password_erp_user):
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT CASE WHEN COUNT(*) > 0 THEN 1 ELSE 0 END AS result
                            FROM erp.v_user WHERE AUTH_PERIOD_TYPE <> 'Заблокированный сотрудник'
                            AND NAME = :login_erp_user AND PASSWORD = :password_erp_user""",
                {
                    "login_erp_user": str(login_erp_user),
                    "password_erp_user": str(password_erp_user)
                }
            )
            return bool(cursor.fetchone()[0] == 1)
    except oracledb.DatabaseError as e:
        logging.error("Ошибка выполнения запроса к базе данных TEZ ERP: %s", str(e))
        flash("Произошла ошибка при выполнении запроса к базе данных TEZ ERP.", "error")
        return False


def get_user_erp_data(connection, login_erp_user, password_erp_user):
    try:
        cursor = connection.cursor()
        cursor.execute(
            """SELECT
                        NVL(vu.PASSWORD,'') as password,
                        UPPER(NVL(vu.FULL_NAME, '')) as full_name,
                        NVL(vu.EMAIL, '') as email,
                        NVL(vu.OFFICE, '') as office,
                        NVL(vu.DEPARTMENT_NAME, '') as department_name,
                        NVL(vu.POST_NAME, '') as position,
                        NVL(vu.PHONE_EXT, '') as phone_ext,
                        NVL(vu.VPN, '') as vpn,
                        NVL(tu.vpn_end_date, '') as vpn_end_date
                FROM erp.v_user vu, erp.t_user tu
                WHERE vu.USER_ID=tu.USER_ID AND (vu.AUTH_PERIOD_TYPE IS NOT NULL
                      AND vu.AUTH_PERIOD_TYPE <> 'Заблокированный сотрудник')
                      AND vu.NAME = :erp_login  AND vu.PASSWORD = :erp_password""",
            {"erp_login": str(login_erp_user), "erp_password": str(password_erp_user)},
        )
        result = cursor.fetchone()
        if result:
            return result
    except oracledb.DatabaseError as e:
        logging.error("Ошибка выполнения запроса к базе данных TEZ ERP: %s", str(e))
        flash("Произошла ошибка при выполнении запроса к базе данных TEZ ERP.", "error")
    return None


def get_user_erp_password(connection, user_username):
    if connection is None:
        logging.error("Отсутствует соединение с базой данных TEZ ERP")
        return None
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT PASSWORD
                FROM erp.v_user
                WHERE AUTH_PERIOD_TYPE <> 'Заблокированный сотрудник'
                AND NAME = :login_erp_user
                """,
                {"login_erp_user": str(user_username)},
            )
            result = cursor.fetchone()
            return result[0] if result else None  # Возвращаем строку, а не кортеж
    except oracledb.DatabaseError as e:
        logging.error("Ошибка выполнения запроса к базе данных TEZ ERP: %s", str(e))
        flash("Произошла ошибка при выполнении запроса к базе данных TEZ ERP.", "error")
        return None  # Лучше возвращать None в случае ошибки
