"""Gemini 2.5 Flash OCR processing via OpenRouter."""

import base64
from backend.ai.gemini_client import get_ai_client
from backend.utils.parsers import parse_pdf_text, is_image_file, is_pdf_file
from backend.utils.logger import get_logger

logger = get_logger("ocr_service")

OCR_SYSTEM_PROMPT = """You are an expert OCR system specialized in reading medical documents including prescriptions, bills, diagnostic reports, and pharmacy receipts. Extract ALL text from the document accurately, preserving the structure and formatting. Pay special attention to:
- Doctor names and registration numbers
- Patient details (name, age, sex)
- Dates
- Diagnosis and medical conditions
- Medicine names, dosages, and quantities
- Amounts and totals
- Hospital/clinic names
- Signatures and stamps (note their presence)"""


def process_document(file_bytes: bytes, filename: str) -> dict:
    """Process a medical document and extract text using OCR."""
    result = {"filename": filename, "text": "", "method": "", "success": False}

    try:
        if is_pdf_file(filename):
            text = parse_pdf_text(file_bytes)
            if text and len(text.strip()) > 50:
                result["text"] = text
                result["method"] = "pdf_text_extraction"
                result["success"] = True
                logger.info(f"PDF text extraction successful for {filename}")
                return result
            # If PDF text extraction yields little text, try vision OCR
            logger.info(f"PDF text extraction yielded minimal text, falling back to vision OCR")

        if is_image_file(filename) or is_pdf_file(filename):
            text = _vision_ocr(file_bytes, filename)
            if text:
                result["text"] = text
                result["method"] = "vision_ocr"
                result["success"] = True
                logger.info(f"Vision OCR successful for {filename}")
                return result

        logger.warning(f"No OCR method succeeded for {filename}")
        return result

    except Exception as e:
        logger.error(f"OCR processing failed for {filename}: {e}")
        result["error"] = str(e)
        return result


def _vision_ocr(file_bytes: bytes, filename: str) -> str:
    """Use OpenRouter vision model for OCR."""
    client = get_ai_client()
    encoded = base64.b64encode(file_bytes).decode("utf-8")

    ext = filename.lower().split(".")[-1]
    media_types = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp", "pdf": "application/pdf"}
    media_type = media_types.get(ext, "image/jpeg")

    prompt = """Extract ALL text from this medical document. Preserve the structure.
Include: doctor details, patient info, dates, diagnosis, medicines, amounts, totals.
If handwritten, do your best to read it accurately.
Return the extracted text only, no commentary."""

    return client.generate_with_vision(
        prompt=prompt, image_base64=encoded, media_type=media_type,
        system_prompt=OCR_SYSTEM_PROMPT, temperature=0.05
    )


def process_multiple_documents(files: list[tuple[bytes, str]]) -> list[dict]:
    """Process multiple documents in parallel and return all results."""
    if not files:
        return []
    
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=len(files)) as executor:
        futures = [executor.submit(process_document, file_bytes, filename) for file_bytes, filename in files]
        results = [future.result() for future in futures]
    return results
