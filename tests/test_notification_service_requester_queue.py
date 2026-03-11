import os
import uuid
import unittest
from datetime import datetime
from unittest.mock import patch


for key, value in {
    "MYSQL_HOST": "127.0.0.1",
    "MYSQL_PORT": "3306",
    "MYSQL_DATABASE": "redmine",
    "MYSQL_USER": "easyredmine",
    "MYSQL_PASSWORD": "x",
    "MYSQL_QUALITY_HOST": "127.0.0.1",
    "MYSQL_QUALITY_PORT": "3306",
    "MYSQL_QUALITY_DATABASE": "redmine",
    "MYSQL_QUALITY_USER": "easyredmine",
    "MYSQL_QUALITY_PASSWORD": "x",
    "SECRET_KEY": "test-secret",
}.items():
    os.environ.setdefault(key, value)

import blog.notification_service as notification_service_module
from blog.notification_service import NotificationService


class FakeCursor:
    def __init__(self, results_sequence):
        self._results_sequence = list(results_sequence)
        self.executed = []
        self._current_rows = []
        self._current_row = None
        self.closed = False

    def execute(self, query, params=None):
        normalized_query = " ".join(query.split())
        self.executed.append((normalized_query, params))
        result = self._results_sequence.pop(0) if self._results_sequence else []

        if isinstance(result, dict):
            self._current_rows = [result]
            self._current_row = result
        else:
            self._current_rows = list(result)
            self._current_row = self._current_rows[0] if self._current_rows else None

    def fetchall(self):
        return list(self._current_rows)

    def fetchone(self):
        return self._current_row

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self, *args, **kwargs):
        return self._cursor


class EmptyQuery:
    def filter_by(self, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def all(self):
        return []


class FakeDateColumn:
    def desc(self):
        return self


class FakeNotificationsModel:
    query = EmptyQuery()
    date_created = FakeDateColumn()


class FakeNotificationsAddNotesModel:
    query = EmptyQuery()
    date_created = FakeDateColumn()


class NotificationServiceRequesterQueueTests(unittest.TestCase):
    def test_process_status_notifications_uses_author_queue(self):
        service = NotificationService()
        cursor = FakeCursor(
            [
                [
                    {
                        "ID": 501,
                        "IssueID": 270445,
                        "OldStatus": "Открыта",
                        "NewStatus": "В работе",
                        "OldSubj": "Ошибка входа",
                        "Body": "Описание",
                        "RowDateCreated": datetime(2026, 3, 11, 13, 4, 16),
                        "Author": "DMITRI@TEZTOUR.EE",
                    }
                ]
            ]
        )
        connection = FakeConnection(cursor)
        saved_notifications = []
        deleted_batches = []

        with patch.object(
            service.deduplicator, "is_duplicate", side_effect=lambda *_: False
        ), patch.object(
            service,
            "_save_status_notifications",
            side_effect=lambda notifications, request_id: saved_notifications.extend(
                notifications
            )
            or [notification.source_id for notification in notifications],
        ), patch.object(
            service,
            "_delete_processed_status_notifications",
            side_effect=lambda connection, ids_to_delete, request_id, recipient_email=None: deleted_batches.append(
                (ids_to_delete, recipient_email)
            ),
        ):
            processed_count = service._process_status_notifications(
                connection,
                " Dmitri@Teztour.EE ",
                24,
                uuid.uuid4(),
            )

        self.assertEqual(processed_count, 1)
        self.assertIn("WHERE Author = %s", cursor.executed[0][0])
        self.assertEqual(cursor.executed[0][1], ("dmitri@teztour.ee",))
        self.assertEqual(
            saved_notifications[0].data["recipient_email"], "dmitri@teztour.ee"
        )
        self.assertEqual(deleted_batches, [([501], "dmitri@teztour.ee")])

    def test_process_comment_notifications_uses_author_queue(self):
        service = NotificationService()
        cursor = FakeCursor(
            [
                [
                    {
                        "ID": 601,
                        "issue_id": 270445,
                        "Author": "DMITRI@TEZTOUR.EE",
                        "notes": "<p>Комментарий</p>",
                        "date_created": "2026-03-11 13:04:16",
                        "RowDateCreated": datetime(2026, 3, 11, 13, 4, 16),
                    }
                ],
                {"author_name": "Helpdesk Agent"},
            ]
        )
        connection = FakeConnection(cursor)
        saved_notifications = []
        deleted_batches = []

        with patch.object(
            service.deduplicator, "is_duplicate", side_effect=lambda *_: False
        ), patch.object(
            service,
            "_save_comment_notifications",
            side_effect=lambda notifications, request_id: saved_notifications.extend(
                notifications
            )
            or [notification.source_id for notification in notifications],
        ), patch.object(
            service,
            "_delete_processed_comment_notifications",
            side_effect=lambda connection, ids_to_delete, request_id, recipient_email=None: deleted_batches.append(
                (ids_to_delete, recipient_email)
            ),
        ):
            processed_count = service._process_comment_notifications(
                connection,
                " Dmitri@Teztour.EE ",
                24,
                uuid.uuid4(),
            )

        self.assertEqual(processed_count, 1)
        self.assertIn(
            "FROM u_its_add_notes WHERE Author = %s", cursor.executed[0][0]
        )
        self.assertEqual(cursor.executed[0][1], ("dmitri@teztour.ee",))
        self.assertEqual(
            saved_notifications[0].data["recipient_email"], "dmitri@teztour.ee"
        )
        self.assertEqual(deleted_batches, [([601], "dmitri@teztour.ee")])

    def test_get_user_notifications_syncs_requester_queue(self):
        service = NotificationService()
        call_order = []

        with patch.object(
            service,
            "_sync_requester_queue_notifications",
            side_effect=lambda user_id, user_email=None, request_id=None: call_order.append(
                ("sync", user_id)
            )
            or 0,
        ), patch.object(
            service,
            "_fetch_and_save_redmine_notifications",
            side_effect=lambda user_id: call_order.append(("redmine", user_id)),
        ), patch.object(
            notification_service_module,
            "REDMINE_NOTIFICATIONS",
            "off",
        ), patch.object(
            notification_service_module, "Notifications", FakeNotificationsModel
        ), patch.object(
            notification_service_module,
            "NotificationsAddNotes",
            FakeNotificationsAddNotesModel,
        ):
            result = service.get_user_notifications(24)

        self.assertEqual(call_order[0], ("sync", 24))
        self.assertEqual(result["total_count"], 0)

    def test_get_notifications_for_page_syncs_requester_queue(self):
        service = NotificationService()
        call_order = []

        with patch.object(
            service,
            "_sync_requester_queue_notifications",
            side_effect=lambda user_id, user_email=None, request_id=None: call_order.append(
                ("sync", user_id)
            )
            or 0,
        ), patch.object(
            service,
            "_fetch_and_save_redmine_notifications",
            side_effect=lambda user_id: call_order.append(("redmine", user_id)),
        ), patch.object(
            service,
            "get_local_redmine_notifications",
            side_effect=lambda user_id: [],
        ), patch.object(
            notification_service_module, "Notifications", FakeNotificationsModel
        ), patch.object(
            notification_service_module,
            "NotificationsAddNotes",
            FakeNotificationsAddNotesModel,
        ):
            result = service.get_notifications_for_page(24)

        self.assertEqual(call_order[0], ("sync", 24))
        self.assertEqual(result["total_count"], 0)


if __name__ == "__main__":
    unittest.main()
