from flask import Blueprint, request, jsonify
from services.foundry_service import chat_with_agent

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/api/chat", methods=["POST"])
@chat_bp.route("/chat", methods=["POST"])  # Alias for backward compatibility
def chat():
    try:
        data = request.get_json(silent=True)
        if not data:
            data = request.form.to_dict() if request.form else {}

        message = str(data.get("message", "")).strip()

        if not message:
            return jsonify({
                "success": False,
                "error": "Please enter a message."
            }), 400

        reply = chat_with_agent(message)

        return jsonify({
            "success": True,
            "reply": reply,
            "response": reply
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to get response from AI agent: {str(e)}"
        }), 500