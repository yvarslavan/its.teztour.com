import logging
import os
import uuid
import time # Добавляем импорт time
from flask import current_app # Добавляем импорт current_app
from sqlalchemy.exc import SQLAlchemyError

# Оставляем только те импорты, которые нужны на уровне модуля
from blog.models import User
# ИСПРАВЛЕНИЕ: Убираем импорт check_notifications отсюда, чтобы избежать циклического импорта
# from redmine import check_notifications
# db можно импортировать здесь, если он нужен глобально в модуле,
# но create_app будем импортировать внутри функции
from blog import db

# logger = logging.getLogger(__name__) # Удаляем или комментируем, будем использовать current_app.logger

def scheduled_check_all_user_notifications():
    """
    Плановая задача для проверки уведомлений для всех активных пользователей.
    """
    # Импортируем create_app здесь, чтобы избежать циклического импорта
    from blog import create_app

    # Для работы с базой данных и конфигурацией приложения нужен контекст приложения Flask
    app_instance = create_app()

    with app_instance.app_context():
        logger = current_app.logger # Используем логгер Flask приложения
        run_id = uuid.uuid4()
        pid = os.getpid()
        start_time = time.time()

        logger.info(f"SCHEDULER_RUN: PID={pid}, RunID={run_id}: НАЧАЛО плановой проверки уведомлений.")

        try:
            active_users = User.query.filter_by(online=True).all()
        except SQLAlchemyError as e:
            logger.error(f"SCHEDULER_RUN: PID={pid}, RunID={run_id}: Ошибка SQLAlchemy при получении активных пользователей: {e}", exc_info=True)
            active_users = [] # Предотвращаем дальнейшее выполнение, если пользователи не получены
            # Завершаем задачу, если не можем получить пользователей
            end_time = time.time()
            logger.info(f"SCHEDULER_RUN: PID={pid}, RunID={run_id}: ЗАВЕРШЕНИЕ плановой проверки (ошибка получения пользователей). Время выполнения: {end_time - start_time:.2f} сек.")
            return

        if not active_users:
            logger.info(f"SCHEDULER_RUN: PID={pid}, RunID={run_id}: Активные пользователи не найдены. Проверка уведомлений не требуется.")
            end_time = time.time()
            logger.info(f"SCHEDULER_RUN: PID={pid}, RunID={run_id}: ЗАВЕРШЕНИЕ плановой проверки (нет активных пользователей). Время выполнения: {end_time - start_time:.2f} сек.")
            return

        logger.info(f"SCHEDULER_RUN: PID={pid}, RunID={run_id}: Найдено {len(active_users)} активных пользователей для проверки.")

        total_processed_notifications_for_run = 0

        for user in active_users:
            logger.info(f"SCHEDULER_RUN: PID={pid}, RunID={run_id}: Начало проверки уведомлений для пользователя ID: {user.id}, Email: {user.email}")
            user_check_start_time = time.time()
            try:
                # ИСПРАВЛЕНИЕ: Используем новую улучшенную функцию check_notifications_improved
                from blog.notification_service import check_notifications_improved

                # Вызываем улучшенную функцию check_notifications_improved
                processed_count = check_notifications_improved(user_email=user.email, user_id=user.id)

                logger.info(f"SCHEDULER_RUN: PID={pid}, RunID={run_id}: Обработано {processed_count} уведомлений для пользователя ID: {user.id}.")

                if processed_count > 0:
                    total_processed_notifications_for_run += processed_count
                    logger.info(f"SCHEDULER_RUN: PID={pid}, RunID={run_id}: Успешно обработано {processed_count} уведомлений для пользователя ID: {user.id}.")

            except Exception as e:
                # Логируем ошибку, но продолжаем для других пользователей
                logger.error(f"SCHEDULER_RUN: PID={pid}, RunID={run_id}: Исключение при вызове check_notifications для пользователя ID: {user.id}. Ошибка: {e}", exc_info=True)
            finally:
                user_check_end_time = time.time()
                logger.info(f"SCHEDULER_RUN: PID={pid}, RunID={run_id}: Завершение проверки уведомлений для пользователя ID: {user.id}. Время: {user_check_end_time - user_check_start_time:.2f} сек.")

        end_time = time.time()
        logger.info(f"SCHEDULER_RUN: PID={pid}, RunID={run_id}: ЗАВЕРШЕНИЕ плановой проверки уведомлений. Всего обработано: {total_processed_notifications_for_run} уведомлений. Общее время выполнения: {end_time - start_time:.2f} сек.")
