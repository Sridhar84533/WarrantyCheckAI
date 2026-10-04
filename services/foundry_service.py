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
_tenant_id = (os.environ.get("AZURE_TENANT_ID") or "").strip()
_client_id = (os.environ.get("AZURE_CLIENT_ID") or "").strip()
_client_secret = (os.environ.get("AZURE_CLIENT_SECRET") or "").strip()

if _tenant_id and _client_id and _client_secret:
    print(f"[AUTH] Using ClientSecretCredential | tenant_id='{_tenant_id}' len={len(_tenant_id)}")
    try:
        credential = ClientSecretCredential(
            tenant_id=_tenant_id,
            client_id=_client_id,
            client_secret=_client_secret,
        )
    except ValueError as e:
        raise ValueError(
            f"Azure credential error: {e}\n"
            f"  AZURE_TENANT_ID='{_tenant_id}' (len={len(_tenant_id)})\n"
            f"  AZURE_CLIENT_ID='{_client_id}' (len={len(_client_id)})\n"
            f"  AZURE_CLIENT_SECRET length={len(_client_secret)}"
        ) from e
else:
    print("[AUTH] Azure SP env vars not set — falling back to DefaultAzureCredential")
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
    try:
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
    except Exception as e:
        # Log full error details to Render logs
        err_body = getattr(e, "response", None)
        if err_body is not None:
            try:
                print(f"[AGENT ERROR] Status: {err_body.status_code}")
                print(f"[AGENT ERROR] Body: {err_body.text}")
            except Exception:
                pass
        print(f"[AGENT ERROR] Full exception: {repr(e)}")
        raise



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

    # Strip surrounding single-quotes that the agent sometimes wraps around JSON
    if text.startswith("'") and text.endswith("'"):
        text = text[1:-1].strip()

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

    # Fallback: find first { ... } block in text
    match = re.search(r"(\{[\s\S]*\})", text)
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
    prompt = (
        "Extract warranty and purchase details from the following document and return ONLY valid JSON "
        "with exactly these fields: "
        '{"product_name":"","brand":"","model_number":"","serial_number":"","purchase_date":"",'
        '"warranty_years":"","invoice_number":"","missing_information":[],"document_summary":""}. '
        "Rules: (1) Only use information explicitly in the document. (2) Empty string for missing fields. "
        "(3) purchase_date in YYYY-MM-DD format. (4) warranty_years as a numeric string like '1' or '2'. "
        "(5) missing_information is an array of field names that are absent. "
        "(6) Return RAW JSON only — no markdown fences, no backticks, no commentary. "
        f"DOCUMENT:\n{document_text}"
    )
    result = ask_agent(prompt, max_tokens=1000)
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