"""
@file: theme_helper.py
@description: Server-side theme management utilities for Flask
@dependencies: Flask
@created: 2025-01-06
"""

from flask import request, make_response
from functools import wraps


class ThemeHelper:
    """Helper class for managing theme preferences on the server side"""
    
    COOKIE_NAME = 'site_theme'
    COOKIE_MAX_AGE = 365 * 24 * 60 * 60  # 1 year
    
    @staticmethod
    def get_theme_from_cookie():
        """
        Get the current theme from cookie
        
        Returns:
            str: 'light', 'dark', or None if not set
        """
        return request.cookies.get(ThemeHelper.COOKIE_NAME)
    
    @staticmethod
    def set_theme_cookie(response, theme):
        """
        Set theme cookie on response
        
        Args:
            response: Flask response object
            theme (str): 'light' or 'dark'
            
        Returns:
            Flask response object with cookie set
        """
        if theme not in ['light', 'dark']:
            theme = 'light'
        
        response.set_cookie(
            ThemeHelper.COOKIE_NAME,
            theme,
            max_age=ThemeHelper.COOKIE_MAX_AGE,
            secure=request.is_secure,
            httponly=False,  # Allow JavaScript access
            samesite='Lax'
        )
        return response
    
    @staticmethod
    def inject_theme_context():
        """
        Context processor to inject theme into all templates
        
        Usage in Flask app:
            @app.context_processor
            def inject_theme():
                return ThemeHelper.inject_theme_context()
        """
        return {
            'current_theme': ThemeHelper.get_theme_from_cookie() or 'light'
        }


def with_theme_cookie(f):
    """
    Decorator to automatically sync localStorage theme with cookie
    
    Usage:
        @app.route('/api/set-theme', methods=['POST'])
        @with_theme_cookie
        def set_theme():
            # Theme will be automatically synced to cookie
            return jsonify({'success': True})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = make_response(f(*args, **kwargs))
        
        # Check if theme is in request (from localStorage sync)
        theme = request.json.get('theme') if request.is_json else None
        
        if theme:
            ThemeHelper.set_theme_cookie(response, theme)
        
        return response
    
    return decorated_function
