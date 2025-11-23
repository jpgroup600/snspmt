from flask import Blueprint
from backend_flask import admin_get_coupons, admin_create_coupon, admin_update_coupon, admin_delete_coupon, get_admin_stats, get_admin_purchases, update_purchase_status, get_admin_users, update_admin_user, delete_admin_user, get_payout_requests, approve_payout_request, reject_payout_request, get_admin_transactions, get_withdrawal_requests, process_withdrawal, get_notices, create_notice, update_notice, delete_notice, migrate_database, upload_admin_image

bp = Blueprint('admin', __name__)

ROUTES = [
    ('/api/admin/coupons', 'admin_get_coupons', {'methods': ['GET']}),
    ('/api/admin/coupons', 'admin_create_coupon', {'methods': ['POST', 'OPTIONS']}),
    ('/api/admin/coupons/<int:coupon_id>', 'admin_update_coupon', {'methods': ['PUT']}),
    ('/api/admin/coupons/<int:coupon_id>', 'admin_delete_coupon', {'methods': ['DELETE']}),
    ('/api/admin/stats', 'get_admin_stats', {'methods': ['GET']}),
    ('/api/admin/purchases', 'get_admin_purchases', {'methods': ['GET']}),
    ('/api/admin/purchases/<int:purchase_id>', 'update_purchase_status', {'methods': ['PUT']}),
    ('/api/admin/users', 'get_admin_users', {'methods': ['GET']}),
    ('/api/admin/users/<int:user_id>', 'update_admin_user', {'methods': ['PUT']}),
    ('/api/admin/users/<int:user_id>', 'delete_admin_user', {'methods': ['DELETE']}),
    ('/api/admin/payout-requests', 'get_payout_requests', {'methods': ['GET']}),
    ('/api/admin/payout-requests/<int:request_id>/approve', 'approve_payout_request', {'methods': ['PUT']}),
    ('/api/admin/payout-requests/<int:request_id>/reject', 'reject_payout_request', {'methods': ['PUT']}),
    ('/api/admin/transactions', 'get_admin_transactions', {'methods': ['GET']}),
    ('/api/admin/withdrawal-requests', 'get_withdrawal_requests', {'methods': ['GET']}),
    ('/api/admin/process-withdrawal', 'process_withdrawal', {'methods': ['POST']}),
    ('/api/admin/notices', 'get_notices', {'methods': ['GET']}),
    ('/api/admin/notices', 'create_notice', {'methods': ['POST']}),
    ('/api/admin/notices/<int:notice_id>', 'update_notice', {'methods': ['PUT']}),
    ('/api/admin/notices/<int:notice_id>', 'delete_notice', {'methods': ['DELETE']}),
    ('/api/admin/migrate-database', 'migrate_database', {'methods': ['POST', 'GET']}),
    ('/api/admin/upload-image', 'upload_admin_image', {'methods': ['POST']}),
]




def register_routes(source_module):
    for rule, func_name, options in ROUTES:
        view_func = getattr(source_module, func_name)
        bp.add_url_rule(rule, view_func=view_func, **dict(options))


__all__ = ['bp', 'register_routes']
