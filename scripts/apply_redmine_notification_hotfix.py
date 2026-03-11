#!/usr/bin/env python3
"""
Apply the requester-notification hotfix for Redmine queues.

This script:
1. Loads environment variables from the project env files.
2. Connects to the Redmine MySQL database.
3. Backs up the current procedure definition.
4. Ensures supporting indexes exist for requester queue lookups.
5. Recreates redmine.pr_update_status_for_its with deterministic email lookup
   and local variables instead of session variables.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, Tuple

import pymysql
import pymysql.cursors


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKUP_DIR = PROJECT_ROOT / "logs" / "sql_backups"
DIRECT_REDMINE_HOST = "helpdesk.teztour.com"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from env_loader import load_environment

INDEX_STATEMENTS = (
    (
        "u_its_update_status",
        "idx_u_its_update_status_author_rowdate",
        "ALTER TABLE redmine.u_its_update_status "
        "ADD INDEX idx_u_its_update_status_author_rowdate (Author, RowDateCreated)",
    ),
    (
        "u_its_add_notes",
        "idx_u_its_add_notes_author_rowdate",
        "ALTER TABLE redmine.u_its_add_notes "
        "ADD INDEX idx_u_its_add_notes_author_rowdate (Author, RowDateCreated)",
    ),
)

PROCEDURE_SQL = """
CREATE DEFINER=`easyredmine`@`%` PROCEDURE `pr_update_status_for_its`(
    IN $old_id INT,
    IN $old_status_id INT,
    IN $new_status_id INT
)
BEGIN
    DECLARE issue_author_id INT DEFAULT NULL;
    DECLARE easy_email_to_value VARCHAR(255) DEFAULT NULL;
    DECLARE redmine_author_email VARCHAR(255) DEFAULT NULL;
    DECLARE subject_value VARCHAR(500) DEFAULT NULL;
    DECLARE description_value LONGTEXT DEFAULT NULL;
    DECLARE issue_updated_on DATETIME DEFAULT NULL;
    DECLARE old_status_name VARCHAR(255) DEFAULT NULL;
    DECLARE new_status_name VARCHAR(255) DEFAULT NULL;
    DECLARE queue_event_time VARCHAR(255) DEFAULT NULL;

    IF ($old_status_id <> $new_status_id) THEN
        SELECT
            i.author_id,
            NULLIF(TRIM(IFNULL(i.easy_email_to, '')), ''),
            i.subject,
            i.description,
            i.updated_on
        INTO
            issue_author_id,
            easy_email_to_value,
            subject_value,
            description_value,
            issue_updated_on
        FROM redmine.issues i
        WHERE i.id = $old_id
        LIMIT 1;

        IF easy_email_to_value IS NOT NULL THEN
            SET easy_email_to_value = LOWER(easy_email_to_value);
        END IF;

        SELECT
            NULLIF(TRIM(IFNULL(ea.address, '')), '')
        INTO redmine_author_email
        FROM redmine.email_addresses ea
        WHERE ea.user_id = issue_author_id
          AND NULLIF(TRIM(IFNULL(ea.address, '')), '') IS NOT NULL
        ORDER BY ea.is_default DESC, ea.id ASC
        LIMIT 1;

        IF redmine_author_email IS NOT NULL THEN
            SET redmine_author_email = LOWER(redmine_author_email);
        END IF;

        SELECT us.name
        INTO old_status_name
        FROM redmine.u_statuses us
        WHERE us.id = $old_status_id
        LIMIT 1;

        SELECT us.name
        INTO new_status_name
        FROM redmine.u_statuses us
        WHERE us.id = $new_status_id
        LIMIT 1;

        SET queue_event_time = COALESCE(
            CAST(issue_updated_on AS CHAR),
            DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s')
        );

        IF easy_email_to_value IS NOT NULL AND INSTR(easy_email_to_value, '@') > 0 THEN
            INSERT INTO redmine.u_its_update_status
            SET IssueID = $old_id,
                OldSubj = subject_value,
                Body = description_value,
                OldStatus = old_status_name,
                NewStatus = new_status_name,
                DateCreated = queue_event_time,
                Author = easy_email_to_value;
        END IF;

        IF redmine_author_email IS NOT NULL
           AND INSTR(redmine_author_email, '@') > 0
           AND (
               easy_email_to_value IS NULL
               OR redmine_author_email <> easy_email_to_value
           ) THEN
            INSERT INTO redmine.u_its_update_status
            SET IssueID = $old_id,
                OldSubj = subject_value,
                Body = description_value,
                OldStatus = old_status_name,
                NewStatus = new_status_name,
                DateCreated = queue_event_time,
                Author = redmine_author_email;
        END IF;
    END IF;
END
"""


def _connection_candidates() -> Iterable[Tuple[str, int]]:
    configured_host = os.getenv("MYSQL_HOST", "127.0.0.1")
    configured_port = int(os.getenv("MYSQL_PORT", "3306"))

    yield configured_host, configured_port

    if configured_host in {"127.0.0.1", "localhost"}:
        yield DIRECT_REDMINE_HOST, 3306


def _connect() -> pymysql.connections.Connection:
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    database = os.getenv("MYSQL_DATABASE")

    last_error = None
    for host, port in _connection_candidates():
        try:
            print(f"[connect] Trying {host}:{port}/{database}")
            return pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=6,
                autocommit=False,
            )
        except Exception as exc:  # pragma: no cover - diagnostic path
            last_error = exc
            print(f"[connect] Failed: {exc}")

    raise RuntimeError(f"Unable to connect to Redmine DB: {last_error}")


def _backup_current_procedure(cursor: pymysql.cursors.DictCursor) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"redmine_notification_hotfix_{timestamp}.sql"

    cursor.execute("SHOW CREATE PROCEDURE redmine.pr_update_status_for_its")
    row = cursor.fetchone()
    create_sql = row["Create Procedure"] if row else "-- procedure not found"

    backup_path.write_text(
        "-- Backup before requester notification hotfix\n"
        f"-- Created at: {datetime.now().isoformat()}\n\n"
        "DROP PROCEDURE IF EXISTS redmine.pr_update_status_for_its;\n"
        f"{create_sql};\n",
        encoding="utf-8",
    )
    return backup_path


def _ensure_index(
    cursor: pymysql.cursors.DictCursor,
    table_name: str,
    index_name: str,
    ddl: str,
) -> None:
    cursor.execute(
        f"SHOW INDEX FROM redmine.{table_name} WHERE Key_name = %s",
        (index_name,),
    )
    if cursor.fetchone():
        print(f"[index] Exists: {table_name}.{index_name}")
        return

    print(f"[index] Creating: {table_name}.{index_name}")
    cursor.execute(ddl)


def apply_hotfix() -> None:
    load_environment(PROJECT_ROOT)

    with _connect() as connection:
        with connection.cursor() as cursor:
            backup_path = _backup_current_procedure(cursor)
            print(f"[backup] {backup_path}")

            for table_name, index_name, ddl in INDEX_STATEMENTS:
                _ensure_index(cursor, table_name, index_name, ddl)

            print("[procedure] Recreating redmine.pr_update_status_for_its")
            cursor.execute("DROP PROCEDURE IF EXISTS redmine.pr_update_status_for_its")
            cursor.execute(PROCEDURE_SQL)

        connection.commit()
        print("[done] Redmine notification hotfix applied successfully.")


if __name__ == "__main__":
    apply_hotfix()
