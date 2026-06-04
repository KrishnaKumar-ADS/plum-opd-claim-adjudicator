"""Structured information extraction from medical documents."""

from backend.ai.gemini_client import get_ai_client
from backend.utils.parsers import load_text_file
from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger("extraction_service")
settings = get_settings()


def _load_few_shot_examples() -> str:
    """Load and format few-shot examples for injection into extraction prompt."""
    try:
        import json
        examples_path = settings.prompts_dir + "/few_shot_examples.json"
        with open(examples_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        examples = data.get("extraction_examples", [])
        if not examples:
            return ""
        parts = ["EXAMPLES (follow these input→output patterns exactly):"]
        for i, ex in enumerate(examples[:2], 1):  # Use max 2 examples
            parts.append(f"\nEXAMPLE {i}:")
            parts.append(f"INPUT TEXT:\n{ex['input']}")
            parts.append(f"OUTPUT JSON:\n{json.dumps(ex['output'], indent=2)}")
        return "\n".join(parts)
    except Exception as e:
        logger.warning(f"Could not load few-shot examples: {e}")
        return ""


def extract_claim_data(ocr_text: str, document_type: str = "general") -> dict:
    """Extract structured claim data from OCR text using AI with few-shot prompting."""
    client = get_ai_client()

    # Load extraction prompt
    prompt_path = f"{settings.prompts_dir}/extraction_prompt.txt"
    system_prompt = load_text_file(prompt_path)
    if not system_prompt:
        system_prompt = DEFAULT_EXTRACTION_PROMPT

    # Inject few-shot examples for better structured extraction
    few_shot = _load_few_shot_examples()

    user_prompt = f"""{few_shot}

NOW EXTRACT FROM THIS DOCUMENT:
Document Type: {document_type}

OCR TEXT:
{ocr_text}

Extract ALL relevant information and respond with JSON only."""

    result = client.generate_json(user_prompt, system_prompt=system_prompt, provider="groq")

    if result:
        logger.info(f"Extraction successful: {list(result.keys())}")
    else:
        logger.warning("Extraction returned empty result")

    return result


def extract_from_structured_input(documents_data: dict) -> dict:
    """Extract and normalize data from already-structured input (e.g., test case JSON)."""
    extracted = {
        "doctor_name": "",
        "doctor_registration": "",
        "diagnosis": "",
        "treatments": [],
        "procedures": [],
        "medicines": [],
        "tests": [],
        "bill_breakdown": {},
        "total_amount": 0,
        "treatment_date": "",
        "patient_name": "",
    }

    # Extract from prescription
    prescription = documents_data.get("prescription", {})
    if prescription:
        extracted["doctor_name"] = prescription.get("doctor_name", "")
        extracted["doctor_registration"] = prescription.get("doctor_reg", "")
        extracted["diagnosis"] = prescription.get("diagnosis", "")
        extracted["medicines"] = prescription.get("medicines_prescribed", [])
        extracted["treatments"] = []
        if prescription.get("treatment"):
            extracted["treatments"].append(prescription["treatment"])
        if prescription.get("procedures"):
            extracted["procedures"] = prescription["procedures"]
        if prescription.get("tests_prescribed"):
            extracted["tests"] = prescription["tests_prescribed"]

    # Extract from bill
    bill = documents_data.get("bill", {})
    if bill:
        total = 0
        for key, value in bill.items():
            if isinstance(value, (int, float)):
                extracted["bill_breakdown"][key] = value
                total += value
            elif isinstance(value, list):
                # test_names, etc.
                pass
        extracted["total_amount"] = total

    return extracted


DEFAULT_EXTRACTION_PROMPT = """You are a medical document data extraction specialist. Extract structured information from the provided medical document text.

Extract these fields (use null if not found):
{
    "doctor_name": "Full name of the doctor",
    "doctor_registration": "Registration number (format: XX/XXXXX/XXXX)",
    "clinic_name": "Hospital or clinic name",
    "patient_name": "Patient's full name",
    "patient_age": "Patient age",
    "patient_gender": "Patient gender",
    "treatment_date": "Date of treatment (YYYY-MM-DD format)",
    "diagnosis": "Medical diagnosis",
    "treatments": ["List of treatments/procedures"],
    "procedures": ["List of specific procedures"],
    "medicines": ["List of prescribed medicines with dosage"],
    "tests": ["List of diagnostic tests"],
    "bill_breakdown": {"item": amount},
    "total_amount": 0,
    "payment_mode": "Cash/Card/UPI",
    "has_doctor_signature": true/false,
    "has_stamp": true/false,
    "document_quality": "good/fair/poor"
}

Be precise with amounts (numbers only, no ₹ symbol). Parse dates to YYYY-MM-DD format."""
