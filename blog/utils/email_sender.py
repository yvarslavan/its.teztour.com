import smtplib
import ssl
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from flask import current_app
import os
from datetime import datetime


class EmailSender:
    """Класс для отправки email сообщений"""

    def __init__(self):
        self.smtp_server = "mail.tez-tour.com"  # SMTP сервер TEZ TOUR
        self.smtp_port = 587  # Порт для TLS (более надежный)

        # Читаем настройки из переменных окружения
        try:
            import os
            self.sender_email = os.getenv('SENDER_EMAIL') or "help@tez-tour.com"
            self.sender_password = os.getenv('SENDER_PASSWORD') or ""
        except:
            # Fallback значения
            self.sender_email = "help@tez-tour.com"
            self.sender_password = ""

    def send_email(self, recipient, subject, message, cc=None, attachments=None, reply_to=None):
        """
        Отправка email сообщения

        Args:
            recipient (str): Email получателя
            subject (str): Тема письма
            message (str): Текст сообщения
            cc (str): Email для копии (CC)
            attachments (list): Список путей к файлам для вложения
            reply_to (str): Email для ответа

        Returns:
            bool: True если отправка успешна, False в противном случае
        """
        try:
            # ВРЕМЕННО: Для тестирования просто логируем отправку
            current_app.logger.info(f"📧 [TEST] Email будет отправлен:")
            current_app.logger.info(f"   От: {self.sender_email}")
            current_app.logger.info(f"   Кому: {recipient}")
            current_app.logger.info(f"   Тема: {subject}")
            current_app.logger.info(f"   CC: {cc}")
            current_app.logger.info(f"   Сообщение: {message[:100]}...")

            # Создаем объект сообщения (как в рабочем скрипте)
            msg = MIMEMultipart('mixed')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = recipient

            if cc:
                msg['Cc'] = cc

            if reply_to:
                msg['Reply-To'] = reply_to

            # Добавляем текст сообщения (как в рабочем скрипте)
            part = MIMEText(message, 'html', "utf-8")
            msg.attach(part)

            # Добавляем вложения
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())

                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {os.path.basename(file_path)}'
                        )
                        msg.attach(part)

            # Создаем список получателей
            recipients = [recipient]
            if cc:
                recipients.extend([email.strip() for email in cc.split(',')])

                        # Подключение к SMTP серверу (исправленная версия)
            current_app.logger.info(f"🔗 [SMTP] Подключаемся к {self.smtp_server}:{self.smtp_port}")

                        # Создаем SSL контекст с более совместимыми настройками
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            try:
                # Попытка 1: TLS на порту 587
                current_app.logger.info(f"🔗 [SMTP] Попытка 1: TLS на порту {self.smtp_port}")
                s = smtplib.SMTP(self.smtp_server, self.smtp_port)
                s.ehlo()
                s.starttls(context=context)
                s.ehlo()
                s.login(self.sender_email, self.sender_password)
            except Exception as e1:
                current_app.logger.warning(f"⚠️ [SMTP] Ошибка TLS на порту {self.smtp_port}: {e1}")

                # Попытка 2: Без TLS на порту 25
                try:
                    current_app.logger.info(f"🔗 [SMTP] Попытка 2: Без TLS на порту 25")
                    s = smtplib.SMTP("mail.tez-tour.com", 25)
                    s.ehlo()
                    s.login(self.sender_email, self.sender_password)
                except Exception as e2:
                    current_app.logger.error(f"❌ [SMTP] Ошибка подключения: {e2}")
                    raise Exception(f"Не удалось подключиться к SMTP серверу: {e2}")

            current_app.logger.info(f"📧 [SMTP] Отправляем email на {recipients}")
            s.sendmail(self.sender_email, recipients, msg.as_string())
            s.quit()

            current_app.logger.info(f"✅ [SMTP] Email успешно отправлен: {recipient}, тема: {subject}")
            time.sleep(1)  # делаем небольшую паузу как в рабочем скрипте
            return True

        except Exception as e:
            current_app.logger.error(f"Ошибка при отправке email: {e}")
            return False

    def send_task_email(self, task_id, recipient, subject, message, cc=None, attachments=None, reply_to=None):
        """
        Отправка email связанного с задачей

        Args:
            task_id (int): ID задачи
            recipient (str): Email получателя
            subject (str): Тема письма
            message (str): Текст сообщения
            cc (str): Email для копии (CC)
            attachments (list): Список путей к файлам для вложения
            reply_to (str): Email для ответа

        Returns:
            bool: True если отправка успешна, False в противном случае
        """
        # Добавляем информацию о задаче в тему
        task_subject = f"Задача #{task_id} - {subject}"

        # Добавляем подпись с информацией о задаче
        task_message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <!-- Стильный заголовок с логотипом -->
            <div style="background-color: #1a365d; padding: 20px; margin-bottom: 20px;">
                <table width="100%" border="0" cellspacing="0" cellpadding="0" style="border-collapse: collapse;">
                    <tr align="top">
                        <td width="280" align="left">
                            <a href="http://www.tez-tour.com" target="_blank">
                                <img src="https://r.tez-tour.com/armmanager/images/teztour_logo.png"
                                     alt="TEZ TOUR" title="TEZ TOUR" border="0" style="max-width: 200px; height: auto;">
                            </a>
                        </td>
                        <td align="right" width="400">
                            <div style="font-family: Tahoma, Verdana, Arial, sans-serif; font-size: 14px; color: #ffffff; padding: 0; line-height: 18px;">
                                <b>Служба технической поддержки TEZ TOUR</b><br>
                                Email: <a href="mailto:help@tez-tour.com" target="_blank" style="color: #ffffff; text-decoration: underline;">help@tez-tour.com</a>
                            </div>
                        </td>
                    </tr>
                </table>
            </div>

            <!-- Информация о задаче -->
            <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin-bottom: 20px;">
                <h3 style="margin: 0; color: #007bff;">Информация о задаче</h3>
                <p style="margin: 5px 0;"><strong>ID задачи:</strong> #{task_id}</p>
                <p style="margin: 5px 0;"><strong>Отправлено:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
            </div>

            <div style="line-height: 1.6;">
                {message}
            </div>

            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666;">
                <p>Это сообщение отправлено из системы TEZ Navigator</p>
                <p>Для просмотра задачи перейдите по ссылке: <a href="https://helpdesk.teztour.com/issues/{task_id}">Задача #{task_id}</a></p>
            </div>
        </div>
        """

        try:
            # Отправляем email
            result = self.send_email(recipient, task_subject, task_message, cc, attachments, reply_to)
            current_app.logger.info(f"📧 [TASK] Email для задачи {task_id} отправлен: {result}")

            # ИСПРАВЛЕНИЕ: Если email отправлен успешно, добавляем комментарий в Redmine
            if result:
                try:
                    self._add_email_comment_to_redmine(task_id, recipient, subject, message, cc, attachments)
                except Exception as comment_error:
                    current_app.logger.error(f"⚠️ [TASK] Email отправлен, но не удалось добавить комментарий в Redmine для задачи {task_id}: {comment_error}")
                    # Email отправлен, поэтому возвращаем True даже если комментарий не добавлен

            return result
        except Exception as e:
            current_app.logger.error(f"❌ [TASK] Ошибка при отправке email для задачи {task_id}: {e}")
            return False

    def _add_email_comment_to_redmine(self, task_id, recipient, subject, message, cc=None, attachments=None):
        """
        Добавляет комментарий в Redmine о том, что был отправлен email

        Args:
            task_id (int): ID задачи
            recipient (str): Email получателя
            subject (str): Тема письма
            message (str): Текст сообщения
            cc (str): Email для копии (CC)
            attachments (list): Список путей к файлам для вложения
        """
        from flask_login import current_user
        from blog.tasks.utils import create_redmine_connector, get_user_redmine_password

        try:
            current_app.logger.info(f"📝 [TASK] Добавление комментария в Redmine о отправке email для задачи {task_id}")

            # Получаем пароль пользователя из ERP
            actual_password = get_user_redmine_password(current_user.username)
            if not actual_password:
                current_app.logger.error(f"❌ [TASK] Не удалось получить пароль пользователя {current_user.username} для добавления комментария")
                return False

            # Создаем коннектор Redmine
            redmine_connector = create_redmine_connector(
                is_redmine_user=current_user.is_redmine_user,
                user_login=current_user.username,
                password=actual_password
            )

            if not redmine_connector:
                current_app.logger.error(f"❌ [TASK] Не удалось создать Redmine коннектор для добавления комментария")
                return False

            # Формируем текст комментария
            comment_lines = [f"Получатель: {recipient}"]

            if cc:
                comment_lines.append(f"Копия: {cc}")

            if attachments:
                comment_lines.append(f"Приложения: {len(attachments)} файл(ов)")

            # Добавляем само сообщение
            comment_lines.extend(["", message])

            comment_text = "\n".join(comment_lines)

            # Определяем user_id для добавления комментария
            if current_user.is_redmine_user and hasattr(current_user, 'id_redmine_user') and current_user.id_redmine_user:
                user_id = current_user.id_redmine_user
                current_app.logger.info(f"📝 [TASK] Используем Redmine user_id: {user_id} для пользователя {current_user.username}")
            else:
                # Для анонимных пользователей используем системный ID
                import os
                try:
                    user_id = int(os.getenv('REDMINE_ANONYMOUS_USER_ID', '13'))
                except:
                    user_id = 13  # Значение по умолчанию
                current_app.logger.info(f"📝 [TASK] Используем анонимный user_id: {user_id}")

            # Добавляем комментарий в задачу
            success, message = redmine_connector.add_comment(
                issue_id=task_id,
                notes=comment_text,
                user_id=user_id
            )

            if success:
                current_app.logger.info(f"✅ [TASK] Комментарий об отправке email успешно добавлен в задачу {task_id}")
                return True
            else:
                current_app.logger.error(f"❌ [TASK] Ошибка при добавлении комментария в задачу {task_id}: {message}")
                return False

        except Exception as e:
            current_app.logger.error(f"💥 [TASK] Критическая ошибка при добавлении комментария в задачу {task_id}: {e}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            return False


# Создаем глобальный экземпляр
email_sender = EmailSender()
