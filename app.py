import os
from flask import (
    Flask,
    render_template,
    send_from_directory,
    jsonify,
    request
)

from config.config import (
    FLASK_SECRET_KEY,
    MAX_UPLOAD_SIZE,
    UPLOAD_FOLDER
)

from routes.chat_routes import chat_bp
from routes.warranty_routes import warranty_bp
from routes.document_routes import document_bp

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static"
)

app.secret_key = FLASK_SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_SIZE
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure uploads folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Register feature blueprints
app.register_blueprint(chat_bp)
app.register_blueprint(warranty_bp)
app.register_blueprint(document_bp)


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "application": "WarrantyCheck AI"
    })


@app.get("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# =========================================================
# GLOBAL ERROR HANDLERS (Always return JSON for API calls)
# =========================================================

@app.errorhandler(400)
def bad_request(e):
    return jsonify({
        "success": False,
        "error": "Bad request. Please verify the request parameters."
    }), 400


@app.errorhandler(404)
def not_found(e):
    # If the user requested an API endpoint that does not exist, return JSON
    if request.path.startswith("/api/") or request.path in ["/check-warranty", "/chat", "/upload-document"]:
        return jsonify({
            "success": False,
            "error": f"API endpoint not found: {request.path}"
        }), 404
    # Otherwise render home page or standard response
    return render_template("index.html"), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({
        "success": False,
        "error": f"Method {request.method} is not allowed for {request.path}."
    }), 405


@app.errorhandler(413)
def request_entity_too_large(e):
    return jsonify({
        "success": False,
        "error": "File size exceeds the 10 MB maximum limit."
    }), 413


@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({
        "success": False,
        "error": "An internal server error occurred. Please try again."
    }), 500


if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )