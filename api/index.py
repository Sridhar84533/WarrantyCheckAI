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
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get("QUERY_STRING", "")
        params = parse_qs(query_string, keep_blank_values=True)

        target_path = None
        if "__path" in params:
            raw_path = params.pop("__path")[0]
            if raw_path:
                target_path = "/" + raw_path.lstrip("/")
            else:
                target_path = "/"
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
            environ["SCRIPT_NAME"] = ""

        return self.wsgi_app(environ, start_response)


app.wsgi_app = VercelPathFixer(app.wsgi_app)
