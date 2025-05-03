
# /workspaces/legalmind/app/utils/pdf_parser.py

import fitz  # PyMuPDF
import io
import logging
import asyncio
from pathlib import Path
from typing import Optional # Use -> str | None for Python 3.10+ if preferred

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Helper Functions to run synchronous blocking code in threads ---

def _extract_pdf_text_sync(content: bytes) -> str:
    """Synchronously extracts text from PDF byte content."""
    text = ""
    try:
        # Open PDF document from byte stream
        with fitz.open(stream=content, filetype="pdf") as doc:
            if doc.needs_pass:
                 logger.warning("PDF is password protected. Cannot extract text.")
                 return "" # Cannot process password-protected PDFs this way

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text("text") # Extract text content
            logger.info(f"Successfully extracted {len(text)} characters from PDF.")
            return text
    except Exception as e:
        # Catch potential errors during PDF parsing (e.g., corrupted file)
        logger.error(f"Error extracting text from PDF stream: {e}", exc_info=True)
        return "" # Return empty string on error

def _extract_txt_text_sync(content: bytes) -> str:
    """Synchronously extracts text from plain text byte content."""
    try:
        # Decode assuming UTF-8, handle errors gracefully
        text = content.decode('utf-8', errors='replace')
        logger.info(f"Successfully decoded {len(text)} characters from TXT.")
        return text
    except Exception as e:
        logger.error(f"Error decoding/reading text file content: {e}", exc_info=True)
        return "" # Return empty string on error

# --- Main Async Function ---

async def extract_text(filename: str, content: bytes) -> Optional[str]:
    """
    Asynchronously extracts text content from supported file types.

    Uses PyMuPDF for PDFs (.pdf) and standard decoding for text files (.txt).
    Runs the synchronous extraction logic in a separate thread to avoid
    blocking the asyncio event loop.

    Args:
        filename: The original name of the file (used to determine type).
        content: The raw byte content of the file.

    Returns:
        The extracted text as a string if successful.
        Returns an empty string "" if the file is empty, password-protected (PDF),
        or an error occurred during extraction for a supported type.
        Returns None if the file type is not supported.
    """
    if not content:
        logger.warning(f"File '{filename}' is empty. No text to extract.")
        return "" # Return empty string for empty files

    file_ext = Path(filename).suffix.lower()
    logger.info(f"Attempting to extract text from file: {filename} (type: {file_ext})")

    extracted_text: Optional[str] = None

    try:
        if file_ext == ".pdf":
            # Run the synchronous PyMuPDF code in a thread pool
            extracted_text = await asyncio.to_thread(_extract_pdf_text_sync, content)
        elif file_ext == ".txt":
            # Run the synchronous decoding in a thread pool
            extracted_text = await asyncio.to_thread(_extract_txt_text_sync, content)
        else:
            logger.warning(f"Unsupported file type: '{file_ext}' for file '{filename}'")
            return None # Explicitly return None for unsupported types

    except Exception as e:
        # Catch unexpected errors during the async/threading process itself
        logger.error(f"Unexpected error during text extraction process for {filename}: {e}", exc_info=True)
        return "" # Return empty string on unexpected errors during async handling

    # Return the result (could be text, or "" if extraction failed/empty/password)
    # Note: The calling code checks `if not extracted_content`, which catches both None and ""
    return extracted_text