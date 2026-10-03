import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

from config.config import UPLOAD_FOLDER
from services.document_service import (
    allowed_file,
    is_image_file,
    extract_document_text
)
from services.foundry_service import analyze_warranty_document

document_bp = Blueprint("documents", __name__)


@document_bp.route("/api/upload-document", methods=["POST"])
@document_bp.route("/upload-document", methods=["POST"])  # Alias for backward compatibility
def upload_document():
    try:
        if "document" not in request.files:
            return jsonify({
                "success": False,
                "error": "Please select a document to upload."
            }), 400

        file = request.files["document"]

        if not file or not file.filename:
            return jsonify({
                "success": False,
                "error": "No file was selected."
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                "success": False,
                "error": "Unsupported file format. Please upload a PDF, DOCX, JPG, JPEG, or PNG document."
            }), 400

        filename = secure_filename(file.filename)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # Check if file is an image
        if is_image_file(filename):
            return jsonify({
                "success": True,
                "filename": filename,
                "is_image": True,
                "extracted_text": "[Image file received. OCR/Vision text extraction is reserved for future integration.]",
                "analysis": {
                    "product_name": "",
                    "brand": "",
                    "model_number": "",
                    "serial_number": "",
                    "purchase_date": "",
                    "warranty_years": "",
                    "invoice_number": "",
                    "missing_information": [
                        "Image OCR/Vision processing is reserved for future integration. Please enter warranty details manually."
                    ],
                    "document_summary": f"Image file '{filename}' uploaded successfully. OCR/Vision extraction will be supported in an upcoming update."
                }
            }), 200

        # For PDF and DOCX, extract text
        extracted_text = extract_document_text(filepath)

        if not extracted_text:
            return jsonify({
                "success": False,
                "error": "No readable text could be extracted from this document. Please ensure it contains selectable digital text."
            }), 400

        # Perform AI analysis using the Microsoft Foundry agent
        analysis = analyze_warranty_document(extracted_text)

        return jsonify({
            "success": True,
            "filename": filename,
            "is_image": False,
            "extracted_text": extracted_text,
            "analysis": analysis
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Document processing failed: {str(e)}"
        }), 500