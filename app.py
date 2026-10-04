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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
    static_url_path="/static"
)

app.secret_key = FLASK_SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_SIZE
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure uploads folder exists safely
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
except OSError:
    pass

# Register feature blueprints
app.register_blueprint(chat_bp)
app.register_blueprint(warranty_bp)
app.register_blueprint(document_bp)


@app.route("/", methods=["GET", "POST"])
@app.route("/api/index", methods=["GET", "POST"])
@app.route("/api/index.py", methods=["GET", "POST"])
@app.route("/api", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        data = request.get_json(silent=True) or (request.form.to_dict() if request.form else {})
        if "document" in request.files:
            from routes.document_routes import upload_document
            return upload_document()
        if "purchase_date" in data or "warranty_years" in data or "product_name" in data:
            from routes.warranty_routes import check_warranty
            return check_warranty()
        if "message" in data:
            from routes.chat_routes import chat
            return chat()
        return jsonify({
            "success": False,
            "error": "No matching handler found for request payload."
        }), 400

    return render_template("index.html")


@app.route("/static/<path:filename>")
def serve_custom_static(filename):
    search_dirs = [
        os.path.join(BASE_DIR, "static"),
        os.path.join(BASE_DIR, "public", "static"),
        os.path.join(os.path.dirname(BASE_DIR), "static"),
        os.path.join(os.path.dirname(BASE_DIR), "public", "static"),
    ]
    for d in search_dirs:
        full_path = os.path.join(d, filename)
        if os.path.isfile(full_path):
            response = send_from_directory(os.path.abspath(d), filename)
            if filename.endswith(".css"):
                response.headers["Content-Type"] = "text/css; charset=utf-8"
            elif filename.endswith(".js"):
                response.headers["Content-Type"] = "application/javascript; charset=utf-8"
            response.headers["Cache-Control"] = "public, max-age=86400"
            return response
    return ("Static asset not found", 404, {"Content-Type": "text/plain"})


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
    if request.path.startswith("/static/"):
        return ("Static asset not found", 404, {"Content-Type": "text/plain"})

    clean_path = request.path.rstrip("/")
    if clean_path in ["", "/api", "/api/index", "/api/index.py"]:
        return render_template("index.html")

    # If the user requested an actual API endpoint that does not exist, return JSON
    if (request.path.startswith("/api/") and not request.path.startswith("/api/index")) or \
       request.path in ["/check-warranty", "/chat", "/upload-document"]:
        return jsonify({
            "success": False,
            "error": f"API endpoint not found: {request.path}"
        }), 404

    # Otherwise render home page
    return render_template("index.html")


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