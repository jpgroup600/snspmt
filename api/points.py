from flask import Blueprint
from backend_flask import get_user_points, purchase_points, kcp_register_transaction, kcp_payment_form, kcp_payment_return, kcp_payment_approve, deduct_points, get_purchase_history
bp = Blueprint('points', __name__)

ROUTES = [
    ('/api/points', 'get_user_points', {'methods': ['GET']}),
    ('/api/points/purchase', 'purchase_points', {'methods': ['POST']}),
    ('/api/points/purchase-kcp/register', 'kcp_register_transaction', {'methods': ['POST']}),
    ('/api/points/purchase-kcp/payment-form', 'kcp_payment_form', {'methods': ['POST']}),
    ('/api/points/purchase-kcp/return', 'kcp_payment_return', {'methods': ['POST']}),
    ('/api/points/purchase-kcp/approve', 'kcp_payment_approve', {'methods': ['POST']}),
    ('/api/points/deduct', 'deduct_points', {'methods': ['POST']}),
    ('/api/points/purchase-history', 'get_purchase_history', {'methods': ['GET']}),
]


def register_routes(source_module):
    for rule, func_name, options in ROUTES:
        view_func = getattr(source_module, func_name)
        bp.add_url_rule(rule, view_func=view_func, **dict(options))


__all__ = ['bp', 'register_routes']
