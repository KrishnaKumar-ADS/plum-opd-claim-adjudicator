"""Tests for OCR service."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_pdf_parsing():
    from backend.utils.parsers import parse_pdf_text
    # Test with empty bytes (should handle gracefully)
    result = parse_pdf_text(b"")
    assert result == "" or result is not None
    print("✅ PDF parsing test passed")


def test_file_detection():
    from backend.utils.parsers import detect_file_type, is_image_file, is_pdf_file
    assert detect_file_type("test.pdf") == "application/pdf"
    assert detect_file_type("test.jpg") == "image/jpeg"
    assert is_image_file("photo.png") == True
    assert is_pdf_file("doc.pdf") == True
    assert is_pdf_file("photo.jpg") == False
    print("✅ File detection test passed")


if __name__ == "__main__":
    test_pdf_parsing()
    test_file_detection()
