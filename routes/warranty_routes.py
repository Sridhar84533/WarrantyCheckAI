from flask import Blueprint, request, jsonify
from services.warranty_service import calculate_warranty

warranty_bp = Blueprint("warranty", __name__)


@warranty_bp.route("/api/check-warranty", methods=["POST"])
@warranty_bp.route("/check-warranty", methods=["POST"])  # Alias for backward compatibility
def check_warranty():
    try:
        data = request.get_json(silent=True)
        if not data:
            # Handle possible form data or empty payload
            data = request.form.to_dict() if request.form else {}

        if not data:
            return jsonify({
                "success": False,
                "error": "Please provide product and warranty details in JSON format."
            }), 400

        result = calculate_warranty(
            product_name=data.get("product_name", ""),
            brand=data.get("brand", ""),
            model_number=data.get("model_number", ""),
            serial_number=data.get("serial_number", ""),
            purchase_date=data.get("purchase_date", ""),
            warranty_years=data.get("warranty_years", "")
        )

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Warranty calculation failed.",
            "details": str(e)
        }), 500