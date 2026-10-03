import json
import os
import re
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.ai.projects import AIProjectClient

from config.config import (
    FOUNDRY_PROJECT_ENDPOINT,
    FOUNDRY_AGENT_NAME,
    FOUNDRY_AGENT_VERSION,
)

if not FOUNDRY_PROJECT_ENDPOINT:
    raise RuntimeError("FOUNDRY_PROJECT_ENDPOINT is missing from .env")

# Use Service Principal (ClientSecretCredential) when env vars are set (e.g. Render),
# otherwise fall back to DefaultAzureCredential for local development (az login).
_tenant_id = os.environ.get("AZURE_TENANT_ID")
_client_id = os.environ.get("AZURE_CLIENT_ID")
_client_secret = os.environ.get("AZURE_CLIENT_SECRET")

if _tenant_id and _client_id and _client_secret:
    credential = ClientSecretCredential(
        tenant_id=_tenant_id,
        client_id=_client_id,
        client_secret=_client_secret,
    )
else:
    # Local development fallback (requires `az login`)
    credential = DefaultAzureCredential()

project_client = AIProjectClient(
    endpoint=FOUNDRY_PROJECT_ENDPOINT,
    credential=credential
)

openai_client = project_client.get_openai_client()

WARRANTY_ASSISTANT_SYSTEM_PROMPT = """You are WarrantyCheck AI, an intelligent warranty support assistant.

Your purpose is to help customers understand product warranty coverage and guide them through the warranty claim process.

You can help customers:
1. Check whether a product may still be within its warranty period.
2. Calculate warranty status using the purchase date and warranty duration.
3. Collect product information such as product name, model number, serial number, and service tag.
4. Understand problems reported by customers.
5. Review warranty or purchase documents when they are provided.
6. Guide customers through the next steps for a warranty claim.
7. Provide safe basic troubleshooting suggestions when appropriate.

When checking warranty status, ask for missing information such as:
- Product name
- Purchase date
- Warranty duration
- Serial number or service tag
- Current problem
- Invoice or proof of purchase

Do not claim that a warranty is definitely valid or invalid when required information is missing.
Clearly explain how the warranty-period calculation was made.
If the customer provides a document, use the information available in the document and identify missing information.
Do not invent warranty terms, purchase dates, serial numbers, or company policies.
For technical problems, provide safe basic troubleshooting steps and recommend contacting the manufacturer's official support when necessary.

Be professional, clear, concise, and helpful. Keep responses direct and structured to minimize wait times."""


def ask_agent(prompt: str, max_tokens: int = 600) -> str:
    """Send a prompt to the Microsoft Foundry WarrantyCheckAI agent and return output text."""
    response = openai_client.responses.create(
        input=prompt,
        max_output_tokens=max_tokens,
        extra_body={
            "agent_reference": {
                "name": FOUNDRY_AGENT_NAME,
                "version": FOUNDRY_AGENT_VERSION,
                "type": "agent_reference"
            }
        }
    )
    return response.output_text or ""


def chat_with_agent(message: str) -> str:
    """User conversation with WarrantyCheckAI agent with instructions and optimized response speed."""
    formatted_prompt = f"""[System Instructions]
{WARRANTY_ASSISTANT_SYSTEM_PROMPT}

[Customer Query]
{message}
"""
    return ask_agent(formatted_prompt, max_tokens=600)


def _extract_json_payload(raw_text: str) -> dict:
    """Safely extracts and parses the JSON structure from agent response."""
    text = raw_text.strip()

    # Remove Markdown fences if present
    if "```json" in text:
        match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            text = match.group(1).strip()
    elif "```" in text:
        match = re.search(r"```\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            text = match.group(1).strip()

    # Direct parse attempt
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    # Fallback regex search for outer JSON object
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1).strip())
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

    # Safe fallback if model output was not valid JSON
    return {
        "product_name": "",
        "brand": "",
        "model_number": "",
        "serial_number": "",
        "purchase_date": "",
        "warranty_years": "",
        "invoice_number": "",
        "missing_information": [
            "Could not parse structured JSON from document analysis."
        ],
        "document_summary": raw_text.strip()
    }


def analyze_warranty_document(document_text: str) -> dict:
    """Asks WarrantyCheckAI agent to extract warranty parameters into rigid JSON."""
    prompt = f"""You are analyzing a warranty or purchase document for WarrantyCheck AI.

Extract ONLY information that is explicitly present in the document.

Return ONLY valid JSON using exactly this structure:
{{
  "product_name": "",
  "brand": "",
  "model_number": "",
  "serial_number": "",
  "purchase_date": "",
  "warranty_years": "",
  "invoice_number": "",
  "missing_information": [],
  "document_summary": ""
}}

Rules:
- Never invent information.
- Only use information explicitly present in the document.
- Empty string if a field is not found.
- Use YYYY-MM-DD for purchase_date when confidently identifiable.
- warranty_years must be numeric when available (e.g. "1", "2", "3").
- missing_information must be an array of strings listing key missing items (e.g. ["serial_number", "purchase_date"]).
- document_summary must summarize only the document.
- Return valid JSON only. Do not add markdown backticks or commentary.

DOCUMENT:
{document_text}
"""
    result = ask_agent(prompt, max_tokens=500)
    data = _extract_json_payload(result)

    # Standardize types and missing fields
    return {
        "product_name": str(data.get("product_name") or "").strip(),
        "brand": str(data.get("brand") or "").strip(),
        "model_number": str(data.get("model_number") or "").strip(),
        "serial_number": str(data.get("serial_number") or "").strip(),
        "purchase_date": str(data.get("purchase_date") or "").strip(),
        "warranty_years": str(data.get("warranty_years") or "").strip(),
        "invoice_number": str(data.get("invoice_number") or "").strip(),
        "missing_information": data.get("missing_information") if isinstance(data.get("missing_information"), list) else [],
        "document_summary": str(data.get("document_summary") or "").strip()
    }