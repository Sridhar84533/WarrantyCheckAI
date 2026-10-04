import os
import sys

# Ensure project root is in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app import app


class VercelPathFixer:
    """
    WSGI middleware to restore the original client request path on Vercel.
    When Vercel rewrites requests from '/(.*)' to '/api/index',
    PATH_INFO is rewritten to '/api/index', while the original requested path
    is stored in HTTP_X_MATCHED_PATH.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        matched_path = (
            environ.get("HTTP_X_MATCHED_PATH")
            or environ.get("HTTP_X_FORWARDED_URI")
            or environ.get("HTTP_X_NOW_ROUTE_MATCHES")
        )
        if matched_path:
            # Strip any query parameters from path
            environ["PATH_INFO"] = matched_path.split("?")[0]
        elif environ.get("PATH_INFO") == "/api/index":
            environ["PATH_INFO"] = "/"

        return self.wsgi_app(environ, start_response)


app.wsgi_app = VercelPathFixer(app.wsgi_app)
