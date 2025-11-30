"""
Custom decorators for Receipt Tracker
"""

from functools import wraps
from flask import jsonify

def api_response(f):
    """Decorator to standardize API responses"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
            if isinstance(result, dict) and 'error' in result:
                return jsonify(result), 400
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return decorated_function

def requires_person_access(f):
    """Decorator to ensure person has access to resource"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request
        from auth import get_current_user
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Add person to kwargs
        kwargs['current_person'] = {"id": user['id'], "full_name": user['full_name']}
        return f(*args, **kwargs)
    return decorated_function