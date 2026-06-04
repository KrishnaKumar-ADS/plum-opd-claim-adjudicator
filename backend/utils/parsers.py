"""Document parsing utilities."""

import io
import json
import base64
from pathlib import Path
from typing import Optional
from datetime import datetime
from backend.utils.logger import get_logger

logger = get_logger("parsers")


def parse_pdf_text(file_bytes: bytes) -> str:
    """Extract text content from a PDF file."""
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(io.BytesIO(file_bytes))
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text.strip())

        full_text = "\n\n".join(text_parts)
        logger.info(f"Extracted {len(full_text)} chars from PDF ({len(reader.pages)} pages)")
        return full_text

    except Exception as e:
        logger.error(f"PDF parsing failed: {e}")
        return ""


def image_to_base64(file_bytes: bytes, media_type: str = "image/jpeg") -> str:
    """Convert image bytes to base64 data URI."""
    encoded = base64.b64encode(file_bytes).decode("utf-8")
    return f"data:{media_type}/{media_type.split('/')[-1]};base64,{encoded}"


def detect_file_type(filename: str) -> str:
    """Detect document type from filename extension."""
    ext = Path(filename).suffix.lower()
    type_map = {
        ".pdf": "application/pdf",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
    }
    return type_map.get(ext, "application/octet-stream")


def is_image_file(filename: str) -> bool:
    """Check if file is an image type."""
    return detect_file_type(filename).startswith("image/")


def is_pdf_file(filename: str) -> bool:
    """Check if file is a PDF."""
    return detect_file_type(filename) == "application/pdf"


def parse_amount(amount_str: str) -> Optional[float]:
    """Parse monetary amount from string, handling ₹ symbol and commas."""
    if isinstance(amount_str, (int, float)):
        return float(amount_str)

    try:
        cleaned = str(amount_str).replace("₹", "").replace(",", "").replace(" ", "").strip()
        return float(cleaned)
    except (ValueError, TypeError):
        logger.warning(f"Cannot parse amount: {amount_str}")
        return None


def parse_date_flexible(date_str: str) -> Optional[str]:
    """Parse date from various formats and return ISO format."""
    if not date_str:
        return None

    formats = [
        "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y",
        "%Y/%m/%d", "%d %b %Y", "%d %B %Y",
        "%B %d, %Y", "%b %d, %Y",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(str(date_str).strip(), fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    logger.warning(f"Cannot parse date: {date_str}")
    return None


def load_json_file(filepath: str | Path) -> dict:
    """Load and parse a JSON file."""
    path = Path(filepath)
    if not path.exists():
        logger.error(f"JSON file not found: {filepath}")
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {filepath}: {e}")
        return {}


def load_text_file(filepath: str | Path) -> str:
    """Load text content from a file."""
    path = Path(filepath)
    if not path.exists():
        logger.error(f"Text file not found: {filepath}")
        return ""

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks for RAG ingestion."""
    if not text:
        return []

    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap

    logger.info(f"Split text into {len(chunks)} chunks (size={chunk_size}, overlap={overlap})")
    return chunks
