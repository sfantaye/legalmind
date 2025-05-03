# app/routes/assistant.py
import logging
from fastapi import APIRouter, Request, Form, HTTPException, Path as FastApiPath
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.services.langgraph_flow import run_chat_flow, run_contract_flow
from app.routes.home import document_store # Import the in-memory store

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/assistant/{session_id}", response_class=HTMLResponse)
async def chat_page(request: Request, session_id: str = FastApiPath(...)):
    """Serves the chat interface page for a specific session."""
    # Check if the session exists (i.e., if a document was uploaded for it)
    doc_context = document_store.get(session_id)
    has_document = doc_context is not None # Check if key exists
    logger.info(f"Serving chat page for session {session_id}. Document context present: {has_document}")
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "session_id": session_id,
        "has_document": has_document,
        "initial_message": "Hello! How can I help you today? Ask a question about your uploaded document or general legal topics, or request a contract generation." if has_document else "Hello! How can I help you today? Ask general legal questions or request a contract generation."
    })

@router.post("/assistant/chat/{session_id}")
async def handle_chat(
    request: Request,
    session_id: str = FastApiPath(...),
    user_input: str = Form(...)
):
    """Handles incoming chat messages via LangGraph flow."""
    logger.info(f"Received chat input for session {session_id}: '{user_input[:50]}...'")
    doc_context = document_store.get(session_id) # Retrieve context if available

    if user_input.lower().startswith("generate contract:"):
         # Handle contract generation requests initiated via chat
         try:
             parts = user_input.split(":", 2)
             if len(parts) < 3:
                  return JSONResponse({"response": "To generate a contract, please use the format: 'generate contract: [type]: [details]' (e.g., 'generate contract: NDA: Parties are ACME Corp and Beta Inc, effective date 2024-01-01'). Supported types: NDA, Rental Agreement."})

             contract_type = parts[1].strip()
             details = parts[2].strip()
             logger.info(f"Contract generation request detected: Type='{contract_type}', Details='{details[:50]}...'")

             response = await run_contract_flow(contract_type, details, session_id)
             return JSONResponse({"response": response})

         except Exception as e:
             logger.error(f"Error during contract generation request parsing or execution: {e}", exc_info=True)
             return JSONResponse({"response": "Sorry, I couldn't process the contract generation request."})
    else:
        # Handle general chat or document Q&A
        try:
            response = await run_chat_flow(user_input, session_id, doc_context)
            logger.info(f"LangGraph chat response generated for session {session_id}")
            return JSONResponse({"response": response})
        except Exception as e:
            logger.error(f"Error running LangGraph chat flow: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error processing chat message.")

# Optional: Add a specific endpoint for contract generation if preferred over chat command
@router.post("/assistant/generate/{session_id}")
async def handle_generate_contract(
    request: Request,
    session_id: str = FastApiPath(...),
    contract_type: str = Form(...),
    details: str = Form(...)
):
    """Handles contract generation requests."""
    logger.info(f"Received contract generation request for session {session_id}: Type='{contract_type}', Details='{details[:50]}...'")
    try:
        response = await run_contract_flow(contract_type, details, session_id)
        logger.info(f"LangGraph contract response generated for session {session_id}")
        # Could return JSON or perhaps trigger a file download later
        return JSONResponse({"response": response, "contract_type": contract_type})
    except Exception as e:
        logger.error(f"Error running LangGraph contract flow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error generating contract.")
