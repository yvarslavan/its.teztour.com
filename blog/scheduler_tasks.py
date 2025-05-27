import logging
# Убираем current_app из глобальных импортов, если он больше не нужен напрямую
# from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

# Оставляем только те импорты, которые нужны на уровне модуля
from blog.models import User
from redmine import check_notifications
# db можно импортировать здесь, если он нужен глобально в модуле,
# но create_app будем импортировать внутри функции
from blog import db

logger = logging.getLogger(__name__)

def scheduled_check_all_user_notifications():
    """
    Плановая задача для проверки уведомлений для всех активных пользователей.
    """
    # Импортируем create_app здесь, чтобы избежать циклического импорта
    from blog import create_app

    # Для работы с базой данных и конфигурацией приложения нужен контекст приложения Flask
    app_instance = create_app()

    with app_instance.app_context():
        logger.info("SCHEDULER: Начало плановой проверки уведомлений для всех пользователей.")
        try:
            active_users = User.query.filter_by(online=True).all()
        except SQLAlchemyError as e:
            logger.error(f"SCHEDULER: Ошибка SQLAlchemy при получении активных пользователей: {e}", exc_info=True)
            active_users = [] # Предотвращаем дальнейшее выполнение, если пользователи не получены

        if not active_users:
            logger.info("SCHEDULER: Активные пользователи не найдены. Проверка уведомлений не требуется.")
            return

        logger.info(f"SCHEDULER: Найдено {len(active_users)} активных пользователей для проверки.")

        for user in active_users:
            logger.info(f"SCHEDULER: Проверка уведомлений для пользователя ID: {user.id}, Email: {user.email}")
            try:
                # Вызываем оригинальную функцию check_notifications из redmine.py
                # Эта функция ожидает email и id пользователя.
                # Она также сама обрабатывает внутренние ошибки и логирование.
                processed_count = check_notifications(user.email, user.id)
                if processed_count is False: # check_notifications может вернуть False при ошибке
                     logger.warning(f"SCHEDULER: Функция check_notifications вернула False для пользователя ID: {user.id}. Возможна ошибка внутри функции.")
                elif processed_count is not None:
                    logger.info(f"SCHEDULER: Обработано {processed_count} уведомлений для пользователя ID: {user.id}.")
                else: # Если вернулся None, это тоже может быть индикатором проблемы
                    logger.info(f"SCHEDULER: Функция check_notifications вернула None для пользователя ID: {user.id}.")

            except Exception as e:
                # Логируем ошибку, но продолжаем для других пользователей
                logger.error(f"SCHEDULER: Исключение при проверке уведомлений для пользователя ID: {user.id}. Ошибка: {e}", exc_info=True)

        logger.info("SCHEDULER: Завершение плановой проверки уведомлений для всех пользователей.")
