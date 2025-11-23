from flask import Blueprint
from backend_flask import get_blog_posts, get_blog_post, get_blog_categories, get_blog_tags, create_blog_post, update_blog_post, delete_blog_post

bp = Blueprint('blog', __name__)

ROUTES = [
    ('/api/blog/posts', 'get_blog_posts', {'methods': ['GET']}),
    ('/api/blog/posts/<int:post_id>', 'get_blog_post', {'methods': ['GET']}),
    ('/api/blog/categories', 'get_blog_categories', {'methods': ['GET']}),
    ('/api/blog/tags', 'get_blog_tags', {'methods': ['GET']}),
    ('/api/blog/posts', 'create_blog_post', {'methods': ['POST']}),
    ('/api/blog/posts/<int:post_id>', 'update_blog_post', {'methods': ['PUT']}),
    ('/api/blog/posts/<int:post_id>', 'delete_blog_post', {'methods': ['DELETE']}),
]


def register_routes(source_module):
    for rule, func_name, options in ROUTES:
        view_func = getattr(source_module, func_name)
        bp.add_url_rule(rule, view_func=view_func, **dict(options))


__all__ = ['bp', 'register_routes']
