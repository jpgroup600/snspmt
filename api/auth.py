from flask import Blueprint
from backend_flask import register, sync_user, get_user, kakao_token, auth_login, kakao_login, google_callback, google_login    

bp = Blueprint('auth', __name__)

ROUTES = [
    ('/api/register', 'register', {'methods': ['POST']}),
    ('/api/users/sync', 'sync_user', {'methods': ['POST']}),
    ('/api/users/<path:user_id>', 'get_user', {'methods': ['GET']}),
    ('/api/auth/kakao-token', 'kakao_token', {'methods': ['POST']}),
    ('/api/auth/login', 'auth_login', {'methods': ['POST']}),
    ('/api/auth/kakao-login', 'kakao_login', {'methods': ['POST']}),
    ('/api/auth/google-callback', 'google_callback', {'methods': ['GET']}),
    ('/api/auth/google-login', 'google_login', {'methods': ['POST']}),
]


def register_routes(source_module):
    for rule, func_name, options in ROUTES:
        view_func = getattr(source_module, func_name)
        bp.add_url_rule(rule, view_func=view_func, **dict(options))


__all__ = ['bp', 'register_routes']
