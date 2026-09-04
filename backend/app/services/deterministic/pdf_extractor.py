"""
PDF text extraction service.
Deterministic — no AI, no external calls.
"""
import io
import pdfplumber


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract all text from a PDF file given its raw bytes."""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        pages = []
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n".join(pages)
