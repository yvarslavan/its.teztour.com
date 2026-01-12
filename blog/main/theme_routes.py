"""
@file: theme_routes.py
@description: Flask routes for theme management
@dependencies: Flask, theme_helper
@created: 2025-01-06
"""

from flask import Blueprint, jsonify, request
from blog.utils.theme_helper import ThemeHelper, with_theme_cookie

theme_bp = Blueprint('theme', __name__, url_prefix='/api/theme')


@theme_bp.route('/sync', methods=['POST'])
@with_theme_cookie
def sync_theme():
    """
    Sync theme from localStorage to server cookie
    
    Request JSON:
        {
            "theme": "light" | "dark"
        }
    
    Returns:
        JSON response with success status
    """
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400
    
    theme = request.json.get('theme')
    
    if theme not in ['light', 'dark']:
        return jsonify({'error': 'Invalid theme value'}), 400
    
    return jsonify({
        'success': True,
        'theme': theme,
        'message': 'Theme synced successfully'
    })


@theme_bp.route('/current', methods=['GET'])
def get_current_theme():
    """
    Get current theme from cookie
    
    Returns:
        JSON response with current theme
    """
    theme = ThemeHelper.get_theme_from_cookie() or 'light'
    
    return jsonify({
        'theme': theme
    })
