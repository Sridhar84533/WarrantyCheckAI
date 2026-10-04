import os
import sys
from urllib.parse import parse_qs, urlencode

# Ensure project root is in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app import app


class VercelPathFixer:
    """
    WSGI middleware to restore the original client request path on Vercel.
    Vercel CLI 62 rewrites route requests using the destination path (/api/index).
    By rewriting with `?__path=$1` in vercel.json, we extract the original path
    and set PATH_INFO accordingly so Flask routes correctly for all URLs,
    static files (CSS/JS), and API endpoints.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get("QUERY_STRING", "")
        params = parse_qs(query_string, keep_blank_values=True)

        target_path = None
        if "__path" in params:
            raw_path = params.pop("__path")[0]
            target_path = "/" + raw_path.lstrip("/")
            environ["QUERY_STRING"] = urlencode(params, doseq=True)
        else:
            # Fallback to headers if present
            matched = (
                environ.get("HTTP_X_ORIGINAL_URL")
                or environ.get("HTTP_X_FORWARDED_URI")
                or environ.get("HTTP_X_MATCHED_PATH")
            )
            if matched and matched != "/api/index":
                target_path = "/" + matched.split("?")[0].lstrip("/")

        if target_path:
            environ["PATH_INFO"] = target_path
        elif not environ.get("PATH_INFO") or environ.get("PATH_INFO") == "/api/index":
            environ["PATH_INFO"] = "/"

        return self.wsgi_app(environ, start_response)


app.wsgi_app = VercelPathFixer(app.wsgi_app)
