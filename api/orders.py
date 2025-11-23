from flask import Blueprint
from backend_flask import reprocess_package_orders, create_scheduled_order, create_order, start_package_processing, get_package_progress, get_orders, get_scheduled_orders, check_order_status, update_order_status, cron_process_scheduled_orders, cron_process_split_deliveries

bp = Blueprint('orders', __name__)

ROUTES = [
    ('/api/admin/reprocess-package-orders', 'reprocess_package_orders', {'methods': ['POST']}),
    ('/api/scheduled-orders', 'create_scheduled_order', {'methods': ['POST']}),
    ('/api/orders', 'create_order', {'methods': ['POST']}),
    ('/api/orders/start-package-processing', 'start_package_processing', {'methods': ['POST']}),
    ('/api/orders/<int:order_id>/package-progress', 'get_package_progress', {'methods': ['GET']}),
    ('/api/orders', 'get_orders', {'methods': ['GET']}),
    ('/api/admin/scheduled-orders', 'get_scheduled_orders', {'methods': ['GET']}),
    ('/api/orders/check-status', 'check_order_status', {'methods': ['POST']}),
    ('/api/orders/<order_id>/status', 'update_order_status', {'methods': ['PUT']}),
    ('/api/cron/process-scheduled-orders', 'cron_process_scheduled_orders', {'methods': ['POST']}),
    ('/api/cron/process-split-deliveries', 'cron_process_split_deliveries', {'methods': ['POST']}),
]


def register_routes(source_module):
    for rule, func_name, options in ROUTES:
        view_func = getattr(source_module, func_name)
        bp.add_url_rule(rule, view_func=view_func, **dict(options))


__all__ = ['bp', 'register_routes']
