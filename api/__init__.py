from . import system as system_module
from . import auth as auth_module
from . import orders as orders_module
from . import points as points_module
from . import referral as referral_module
from . import catalog as catalog_module
from . import admin as admin_module
from . import blog as blog_module

modules = [
    system_module,
    auth_module,
    orders_module,
    points_module,
    referral_module,
    catalog_module,
    admin_module,
    blog_module,
]


def register_blueprints(app, source_module):
    for module in modules:
        module.register_routes(source_module)
        app.register_blueprint(module.bp)