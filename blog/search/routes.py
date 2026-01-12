from flask import Blueprint, request, jsonify
from flask_login import login_required
from blog.services.search_service import search_service

search_bp = Blueprint('search', __name__)

@search_bp.route("/search")
@login_required
def search():
    """AJAX поиск по сайту (инструкции и страницы)"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    results = search_service.search(query)
    return jsonify(results)

