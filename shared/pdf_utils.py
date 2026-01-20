"""
PDF download and text extraction utilities.
"""

from pathlib import Path
import requests
from PyPDF2 import PdfReader


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def download_pdf(pdf_url, output_filename="agenda.pdf"):
    """
    Download PDF from URL.

    Args:
        pdf_url: URL of the PDF to download
        output_filename: Local filename to save PDF

    Returns:
        Path: Path to downloaded PDF or None if failed
    """
    print(f"Downloading PDF from {pdf_url}...")

    try:
        response = requests.get(pdf_url, headers=HEADERS, timeout=30)
        response.raise_for_status()

        pdf_path = Path(output_filename)
        pdf_path.write_bytes(response.content)
        print(f"PDF saved to {pdf_path}")
        return pdf_path

    except requests.RequestException as e:
        print(f"Error downloading PDF: {e}")
        return None


def extract_text_from_pdf(pdf_path):
    """
    Extract text content from PDF file.

    Args:
        pdf_path: Path to PDF file (str or Path object)

    Returns:
        str: Extracted text content or None if failed
    """
    print(f"Extracting text from {pdf_path}...")

    try:
        text_content = []
        reader = PdfReader(str(pdf_path))
        print(f"PDF has {len(reader.pages)} pages")

        for i, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            if text:
                text_content.append(f"--- Page {i} ---\n{text}")

        full_text = "\n\n".join(text_content)
        print(f"Extracted {len(full_text)} characters of text")
        return full_text

    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None
