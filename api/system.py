from flask import Blueprint
from backend_flask import uploaded_file, sitemap, rss, robots, test_database_connection, test_users_table, health_check, get_config, deployment_status, check_referral_connection, serve_admin, serve_index, get_active_notices, serve_spa_routes, serve_spa
bp = Blueprint('system', __name__)

ROUTES = [
    ('/static/uploads/<filename>', 'uploaded_file', {}),
    ('/sitemap.xml', 'sitemap', {}),
    ('/rss.xml', 'rss', {}),
    ('/robots.txt', 'robots', {}),
    ('/api/test/db', 'test_database_connection', {'methods': ['GET']}),
    ('/api/test/users', 'test_users_table', {'methods': ['GET']}),
    ('/health', 'health_check', {'methods': ['GET']}),
    ('/api/health', 'health_check', {'methods': ['GET'], 'endpoint': 'health_check_2'}),
    ('/api/config', 'get_config', {'methods': ['GET']}),
    ('/api/deployment-status', 'deployment_status', {'methods': ['GET']}),
    ('/api/debug/referral-connection/<user_id>', 'check_referral_connection', {'methods': ['GET']}),
    ('/admin', 'serve_admin', {}),
    ('/', 'serve_index', {'methods': ['GET', 'POST']}),
    ('/api/notices/active', 'get_active_notices', {'methods': ['GET']}),
    ('/home', 'serve_spa_routes', {'methods': ['GET']}),
    ('/points', 'serve_spa_routes', {'methods': ['GET'], 'endpoint': 'serve_spa_routes_2'}),
    ('/orders', 'serve_spa_routes', {'methods': ['GET'], 'endpoint': 'serve_spa_routes_3'}),
    ('/admin', 'serve_spa_routes', {'methods': ['GET'], 'endpoint': 'serve_spa_routes_4'}),
    ('/referral', 'serve_spa_routes', {'methods': ['GET'], 'endpoint': 'serve_spa_routes_5'}),
    ('/blog', 'serve_spa_routes', {'methods': ['GET'], 'endpoint': 'serve_spa_routes_6'}),
    ('/blog/<path:blog_path>', 'serve_spa_routes', {'methods': ['GET'], 'endpoint': 'serve_spa_routes_7'}),
    ('/kakao-callback', 'serve_spa_routes', {'methods': ['GET'], 'endpoint': 'serve_spa_routes_8'}),
    ('/<path:path>', 'serve_spa', {'methods': ['GET']}),
]


def register_routes(source_module):
    for rule, func_name, options in ROUTES:
        view_func = getattr(source_module, func_name)
        bp.add_url_rule(rule, view_func=view_func, **dict(options))


__all__ = ['bp', 'register_routes']
