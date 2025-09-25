#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@file: htmx_helpers.py
@description: Utility функции для работы с HTMX запросами и ответами
@dependencies: flask-htmx, flask
@created: 2025-01-31
"""

from flask import request, jsonify, render_template
from flask_htmx import HTMX


class HTMXManager:
    """Основной класс для управления HTMX интеграцией"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Инициализация с Flask приложением"""
        self.app = app
        
        # Добавляем context processor для HTMX
        @app.context_processor
        def htmx_context():
            return {
                'is_htmx_request': self.is_htmx_request(),
                'htmx_target': self.get_htmx_target(),
                'htmx_trigger': self.get_htmx_trigger(),
                'htmx_current_url': self.get_htmx_current_url()
            }
    
    @staticmethod
    def is_htmx_request():
        """Проверяет, является ли запрос HTMX запросом"""
        return request.headers.get('HX-Request') == 'true'
    
    @staticmethod
    def get_htmx_target():
        """Возвращает target элемент HTMX запроса"""
        return request.headers.get('HX-Target')
    
    @staticmethod
    def get_htmx_trigger():
        """Возвращает элемент, который инициировал HTMX запрос"""
        return request.headers.get('HX-Trigger')
    
    @staticmethod
    def get_htmx_current_url():
        """Возвращает текущий URL страницы при HTMX запросе"""
        return request.headers.get('HX-Current-URL')
    
    @staticmethod
    def get_htmx_prompt():
        """Возвращает значение prompt при HTMX запросе"""
        return request.headers.get('HX-Prompt')
    
    def render_partial(self, template_name, **context):
        """
        Рендерит частичный шаблон для HTMX запросов или полный для обычных
        
        Args:
            template_name (str): Имя шаблона
            **context: Контекст для шаблона
            
        Returns:
            str: Отрендеренный HTML
        """
        if self.is_htmx_request():
            # Для HTMX запросов возвращаем только частичный контент
            partial_template = f"partials/{template_name}"
            try:
                return render_template(partial_template, **context)
            except:
                # Если частичный шаблон не найден, возвращаем основной
                return render_template(template_name, **context)
        else:
            # Для обычных запросов возвращаем полную страницу
            return render_template(template_name, **context)
    
    def handle_error(self, error, error_template='errors/htmx_error.html'):
        """
        Обрабатывает ошибки для HTMX запросов
        
        Args:
            error (Exception): Исключение
            error_template (str): Шаблон для отображения ошибки
            
        Returns:
            Response: Flask response объект
        """
        if self.is_htmx_request():
            # Для HTMX запросов возвращаем частичный HTML с ошибкой
            error_html = render_template(error_template, error=str(error))
            return error_html, 500, {'HX-Retarget': '#error-container'}
        else:
            # Для обычных запросов возвращаем JSON или полную страницу ошибки
            return jsonify({'error': str(error)}), 500


def htmx_required(f):
    """
    Декоратор для маршрутов, которые должны обрабатывать только HTMX запросы
    
    Usage:
        @app.route('/api/data')
        @htmx_required
        def get_data():
            return render_template('data.html')
    """
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not HTMXManager.is_htmx_request():
            return jsonify({'error': 'This endpoint requires HTMX request'}), 400
        return f(*args, **kwargs)
    return decorated_function


def htmx_redirect(url, target=None):
    """
    Выполняет редирект для HTMX запросов
    
    Args:
        url (str): URL для редиректа
        target (str, optional): Target элемент для обновления
        
    Returns:
        Response: Flask response с HTMX заголовками
    """
    from flask import make_response
    
    response = make_response('', 200)
    response.headers['HX-Redirect'] = url
    
    if target:
        response.headers['HX-Retarget'] = target
    
    return response


def htmx_refresh():
    """
    Обновляет текущую страницу для HTMX запросов
    
    Returns:
        Response: Flask response с заголовком обновления
    """
    from flask import make_response
    
    response = make_response('', 200)
    response.headers['HX-Refresh'] = 'true'
    return response


def htmx_trigger_event(event_name, detail=None):
    """
    Триггерит JavaScript событие на клиенте
    
    Args:
        event_name (str): Имя события
        detail (dict, optional): Дополнительные данные события
        
    Returns:
        dict: Заголовки для добавления к response
    """
    import json
    
    headers = {'HX-Trigger': event_name}
    
    if detail:
        headers['HX-Trigger'] = json.dumps({event_name: detail})
    
    return headers


def get_htmx_attrs(**attrs):
    """
    Генерирует HTMX атрибуты для использования в шаблонах
    
    Args:
        **attrs: HTMX атрибуты (get, post, target, swap, etc.)
        
    Returns:
        dict: Словарь атрибутов для использования в шаблонах
        
    Example:
        attrs = get_htmx_attrs(
            get='/api/data',
            target='#content',
            swap='innerHTML',
            trigger='click'
        )
        # Результат: {'hx-get': '/api/data', 'hx-target': '#content', ...}
    """
    htmx_attrs = {}
    
    for key, value in attrs.items():
        # Преобразуем snake_case в kebab-case для HTMX атрибутов
        htmx_key = f"hx-{key.replace('_', '-')}"
        htmx_attrs[htmx_key] = value
    
    return htmx_attrs


# Глобальный экземпляр для использования в приложении
htmx_manager = HTMXManager()