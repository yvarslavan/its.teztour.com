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

        # Читаем настройки из конфига
        try:
            from config import get
            self.sender_email = get('ender_email', 'sender_email') or "help@tez-tour.com"
            self.sender_password = get('ender_email', 'sender_password') or "$GjvjoM%"
        except:
            # Fallback значения
            self.sender_email = "help@tez-tour.com"
            self.sender_password = "$GjvjoM%"

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
            <div style="background-color: #ecd8bf; padding: 20px; margin-bottom: 20px;">
                <table width="100%" border="0" cellspacing="0" cellpadding="0" style="border-collapse: collapse;">
                    <tr align="top">
                        <td width="280" align="left">
                            <a href="http://www.tez-tour.com" target="_blank">
                                <img src="https://s.tez-tour.com/article/7025866/TEZ_TOUR_logo_horizontal_cmyk_7505.png"
                                     alt="TEZ TOUR" title="TEZ TOUR" border="0" style="max-width: 200px; height: auto;">
                            </a>
                        </td>
                        <td align="right" width="400">
                            <div style="font-family: Tahoma, Verdana, Arial, sans-serif; font-size: 14px; color: #252525; padding: 0; line-height: 18px;">
                                <b>Служба технической поддержки TEZ TOUR</b><br>
                                <a href="tel:+7(495) 775-10-09">+7(495) 775-10-09</a>,
                                <a href="tel:+7(495) 660-10-09">+7(495) 660-10-09</a>, вн.1000<br>
                                Email: <a href="mailto:help@tez-tour.com" target="_blank">help@tez-tour.com</a>
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
            result = self.send_email(recipient, task_subject, task_message, cc, attachments, reply_to)
            current_app.logger.info(f"📧 [TASK] Email для задачи {task_id} отправлен: {result}")
            return result
        except Exception as e:
            current_app.logger.error(f"❌ [TASK] Ошибка при отправке email для задачи {task_id}: {e}")
            return False


# Создаем глобальный экземпляр
email_sender = EmailSender()
