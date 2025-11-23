from flask import Blueprint
from backend_flask import admin_import_smm_services, smm_panel_test, smm_panel_proxy, get_smm_services, get_admin_categories, create_admin_category, get_admin_category, update_admin_category, delete_admin_product, get_admin_products, create_admin_product, get_admin_product, update_admin_product, delete_admin_product, get_admin_product_variants, create_admin_product_variant, get_admin_product_variant, update_admin_product_variant, delete_admin_product_variant, get_admin_packages, create_admin_package, get_admin_package, update_admin_package, delete_admin_package
bp = Blueprint('catalog', __name__)

ROUTES = [
    ('/api/admin/catalog/import-smm', 'admin_import_smm_services', {'methods': ['POST', 'OPTIONS']}),
    ('/api/smm-panel/test', 'smm_panel_test', {'methods': ['GET']}),
    ('/api/smm-panel', 'smm_panel_proxy', {'methods': ['POST']}),
    ('/api/smm-panel/services', 'get_smm_services', {'methods': ['GET']}),
    ('/api/admin/categories', 'get_admin_categories', {'methods': ['GET']}),
    ('/api/admin/categories', 'create_admin_category', {'methods': ['POST']}),
    ('/api/admin/categories/<int:category_id>', 'get_admin_category', {'methods': ['GET']}),
    ('/api/admin/categories/<int:category_id>', 'update_admin_category', {'methods': ['PUT']}),
    ('/api/admin/categories/<int:category_id>', 'delete_admin_category', {'methods': ['DELETE']}),
    ('/api/admin/products', 'get_admin_products', {'methods': ['GET']}),
    ('/api/admin/products', 'create_admin_product', {'methods': ['POST']}),
    ('/api/admin/products/<int:product_id>', 'get_admin_product', {'methods': ['GET']}),
    ('/api/admin/products/<int:product_id>', 'update_admin_product', {'methods': ['PUT']}),
    ('/api/admin/products/<int:product_id>', 'delete_admin_product', {'methods': ['DELETE']}),
    ('/api/categories', 'get_categories', {'methods': ['GET']}),
    ('/api/products', 'get_products', {'methods': ['GET']}),
    ('/api/product-variants', 'get_product_variants', {'methods': ['GET']}),
    ('/api/packages', 'get_packages', {'methods': ['GET']}),
    ('/api/admin/product-variants', 'get_admin_product_variants', {'methods': ['GET']}),
    ('/api/admin/product-variants', 'create_admin_product_variant', {'methods': ['POST']}),
    ('/api/admin/product-variants/<int:variant_id>', 'get_admin_product_variant', {'methods': ['GET']}),
    ('/api/admin/product-variants/<int:variant_id>', 'update_admin_product_variant', {'methods': ['PUT']}),
    ('/api/admin/product-variants/<int:variant_id>', 'delete_admin_product_variant', {'methods': ['DELETE']}),
    ('/api/admin/packages', 'get_admin_packages', {'methods': ['GET']}),
    ('/api/admin/packages', 'create_admin_package', {'methods': ['POST']}),
    ('/api/admin/packages/<int:package_id>', 'get_admin_package', {'methods': ['GET']}),
    ('/api/admin/packages/<int:package_id>', 'update_admin_package', {'methods': ['PUT']}),
    ('/api/admin/packages/<int:package_id>', 'delete_admin_package', {'methods': ['DELETE']}),
]


def register_routes(source_module):
    for rule, func_name, options in ROUTES:
        view_func = getattr(source_module, func_name)
        bp.add_url_rule(rule, view_func=view_func, **dict(options))


__all__ = ['bp', 'register_routes']
