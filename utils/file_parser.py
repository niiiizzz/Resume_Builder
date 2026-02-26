"""
File parsing utilities for resume text extraction.
Supports PDF and image (OCR) inputs.
Business logic only — no Streamlit dependency.
"""

import io
import logging

logger = logging.getLogger(__name__)

# Maximum upload size in bytes (5 MB)
MAX_FILE_SIZE = 5 * 1024 * 1024


def validate_file_size(file_bytes: bytes) -> None:
    """Raise ValueError if file exceeds the 5 MB limit."""
    if len(file_bytes) > MAX_FILE_SIZE:
        size_mb = len(file_bytes) / (1024 * 1024)
        raise ValueError(
            f"File size ({size_mb:.1f} MB) exceeds the 5 MB limit. "
            "Please upload a smaller file."
        )


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text content from a PDF file.

    Args:
        file_bytes: Raw bytes of the PDF file.

    Returns:
        Extracted text as a single string.

    Raises:
        ValueError: If the PDF is corrupted or contains no extractable text.
    """
    validate_file_size(file_bytes)

    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(io.BytesIO(file_bytes))
        pages_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text.strip())

        full_text = "\n\n".join(pages_text).strip()
        if not full_text:
            raise ValueError(
                "Could not extract any text from this PDF. "
                "The file may be image-based — try uploading as an image instead."
            )
        return full_text

    except ValueError:
        raise
    except Exception as e:
        logger.error("PDF extraction failed: %s", e)
        raise ValueError(
            f"Failed to read the PDF file. It may be corrupted or password-protected. "
            f"Details: {e}"
        )


def extract_text_from_image(file_bytes: bytes) -> str:
    """
    Extract text from an image using OCR (Tesseract).

    Args:
        file_bytes: Raw bytes of an image file (PNG, JPG, JPEG).

    Returns:
        Extracted text as a string.

    Raises:
        ValueError: If OCR extraction fails or returns no text.
    """
    validate_file_size(file_bytes)

    try:
        from PIL import Image
        import pytesseract

        image = Image.open(io.BytesIO(file_bytes))
        text = pytesseract.image_to_string(image).strip()

        if not text:
            raise ValueError(
                "OCR could not extract any text from this image. "
                "Ensure the image contains readable text and is not blurry."
            )
        return text

    except ValueError:
        raise
    except Exception as e:
        logger.error("Image OCR extraction failed: %s", e)
        raise ValueError(
            f"Failed to extract text from the image. "
            f"Ensure Tesseract OCR is installed on your system. Details: {e}"
        )


def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extract text content from a DOCX file.

    Args:
        file_bytes: Raw bytes of the DOCX file.

    Returns:
        Extracted text as a single string.

    Raises:
        ValueError: If the DOCX is corrupted or contains no extractable text.
    """
    validate_file_size(file_bytes)

    try:
        from docx import Document

        doc = Document(io.BytesIO(file_bytes))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        full_text = "\n".join(paragraphs).strip()

        if not full_text:
            raise ValueError(
                "Could not extract any text from this DOCX file. "
                "The document may be empty or contain only images."
            )
        return full_text

    except ValueError:
        raise
    except Exception as e:
        logger.error("DOCX extraction failed: %s", e)
        raise ValueError(
            f"Failed to read the DOCX file. It may be corrupted. Details: {e}"
        )


def extract_text_from_txt(file_bytes: bytes) -> str:
    """
    Extract text from a plain text file.

    Args:
        file_bytes: Raw bytes of a .txt file.

    Returns:
        Decoded text as a string.

    Raises:
        ValueError: If decoding fails or text is empty.
    """
    validate_file_size(file_bytes)

    try:
        text = file_bytes.decode("utf-8", errors="replace").strip()
        if not text:
            raise ValueError("The uploaded text file is empty.")
        return text
    except ValueError:
        raise
    except Exception as e:
        logger.error("TXT extraction failed: %s", e)
        raise ValueError(f"Failed to read the text file. Details: {e}")
