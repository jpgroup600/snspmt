from flask import Blueprint
from backend_flask import get_my_codes, use_referral_code, get_commissions, issue_referral_coupon, validate_referral_code, add_coupon_by_code, get_user_coupons, get_referral_commission_overview, pay_commission, get_payment_history, get_referral_stats, get_user_referrals, admin_register_referral, admin_get_referrals, admin_get_referral_codes, admin_get_commissions, delete_referral_code, activate_all_referral_codes, get_commission_points, get_commission_transactions, request_withdrawal, update_referral_commission_rate
bp = Blueprint('referral', __name__)

ROUTES = [
    ('/api/referral/my-codes', 'get_my_codes', {'methods': ['GET']}),
    ('/api/referral/use-code', 'use_referral_code', {'methods': ['POST']}),
    ('/api/referral/commissions', 'get_commissions', {'methods': ['GET']}),
    ('/api/referral/issue-coupon', 'issue_referral_coupon', {'methods': ['POST']}),
    ('/api/referral/validate-code', 'validate_referral_code', {'methods': ['GET']}),
    ('/api/user/coupons/add-by-code', 'add_coupon_by_code', {'methods': ['POST', 'OPTIONS']}),
    ('/api/user/coupons', 'get_user_coupons', {'methods': ['GET']}),
    ('/api/admin/referral/commission-overview', 'get_referral_commission_overview', {'methods': ['GET']}),
    ('/api/admin/referral/pay-commission', 'pay_commission', {'methods': ['POST']}),
    ('/api/admin/referral/payment-history', 'get_payment_history', {'methods': ['GET']}),
    ('/api/referral/stats', 'get_referral_stats', {'methods': ['GET']}),
    ('/api/referral/referrals', 'get_user_referrals', {'methods': ['GET']}),
    ('/api/admin/referral/register', 'admin_register_referral', {'methods': ['POST']}),
    ('/api/admin/referral/list', 'admin_get_referrals', {'methods': ['GET']}),
    ('/api/admin/referral/codes', 'admin_get_referral_codes', {'methods': ['GET']}),
    ('/api/admin/referral/commissions', 'admin_get_commissions', {'methods': ['GET']}),
    ('/api/admin/referral/codes/<code>', 'delete_referral_code', {'methods': ['DELETE']}),
    ('/api/admin/referral/activate-all', 'activate_all_referral_codes', {'methods': ['POST']}),
    ('/api/referral/commission-points', 'get_commission_points', {'methods': ['GET']}),
    ('/api/referral/commission-transactions', 'get_commission_transactions', {'methods': ['GET']}),
    ('/api/referral/withdrawal-request', 'request_withdrawal', {'methods': ['POST']}),
    ('/api/admin/referral/update-commission-rate', 'update_referral_commission_rate', {'methods': ['PUT']}),
]


def register_routes(source_module):
    for rule, func_name, options in ROUTES:
        view_func = getattr(source_module, func_name)
        bp.add_url_rule(rule, view_func=view_func, **dict(options))


__all__ = ['bp', 'register_routes']
