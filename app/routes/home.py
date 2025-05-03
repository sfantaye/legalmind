# app/routes/home.py
import logging
import secrets
import shutil
from pathlib import Path
from fastapi import APIRouter, Request, Form, UploadFile, File, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import aiofiles

from app.utils.pdf_parser import extract_text

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Simple in-memory storage for document context (replace with DB/Cache in production)
document_store: dict[str, str] = {}
UPLOAD_DIR = Path("temp_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serves the homepage."""
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/upload", response_class=HTMLResponse)
async def upload_form(request: Request):
    """Serves the file upload page."""
    return templates.TemplateResponse("upload.html", {"request": request})

@router.post("/upload")
async def handle_upload(
    request: Request,
    file: UploadFile = File(...)
):
    """Handles file upload, extracts text, and redirects to chat."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    # Generate a unique session ID for this document/chat session
    session_id = secrets.token_hex(16)
    logger.info(f"Handling upload for file: {file.filename}, session: {session_id}")

    # Save file temporarily (optional, could process in memory)
    temp_file_path = UPLOAD_DIR / f"{session_id}_{file.filename}"
    file_content = b""
    try:
        async with aiofiles.open(temp_file_path, 'wb') as out_file:
            content = await file.read() # Read content
            file_content = content
            await out_file.write(content)
        logger.info(f"File saved temporarily to {temp_file_path}")

        # Extract text based on file type
        extracted_content = await extract_text(file.filename, file_content)

        if not extracted_content:
            logger.warning(f"Could not extract text from {file.filename} or unsupported type.")
            # Optionally delete temp file if text extraction failed
            temp_file_path.unlink(missing_ok=True)
            # Redirect back to upload with error? Or proceed without context?
            # Let's proceed but store empty context.
            document_store[session_id] = "" # Store empty context
            # Maybe raise an HTTP exception instead?
            # raise HTTPException(status_code=400, detail="Could not extract text from file or unsupported file type.")

        else:
            logger.info(f"Extracted {len(extracted_content)} characters from {file.filename}.")
            # Store extracted text associated with the session ID
            document_store[session_id] = extracted_content
            # Clean up the temporary file after processing
            # temp_file_path.unlink(missing_ok=True) # Keep file for potential debugging? Or delete.

    except Exception as e:
        logger.error(f"Error processing upload for {file.filename}: {e}", exc_info=True)
        temp_file_path.unlink(missing_ok=True) # Ensure cleanup on error
        raise HTTPException(status_code=500, detail=f"Failed to process file: {e}")
    finally:
        await file.close()


    # Redirect to the chat page, passing the session_id
    # We'll retrieve the context in the chat route using this ID
    redirect_url = request.url_for("chat_page", session_id=session_id)
    logger.info(f"Redirecting to chat page: {redirect_url}")
    return RedirectResponse(url=redirect_url, status_code=303) # Use 303 See Other for POST->GET redirect
