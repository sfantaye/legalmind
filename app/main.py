import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.routes import home, assistant
from app.services.groq_client import logger as groq_logger # Import logger for config check

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LegalMind AI Assistant")

# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(home.router, tags=["Homepage & Upload"])
app.include_router(assistant.router, prefix="/assistant", tags=["AI Assistant"]) # Add prefix here

@app.on_event("startup")
async def startup_event():
    logger.info("LegalMind application starting up...")
    if not groq_logger.handlers: # Check if groq_client logged its API key status
         pass # Already handled in groq_client import
    # Add any other startup logic here (e.g., DB connections)

@app.get("/health", tags=["System"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok"}

# Example: Root path redirect or simple message (optional if home router handles '/')
# @app.get("/", response_class=HTMLResponse, include_in_schema=False)
# async def root(request: Request):
#     # Redirect to the main page, handled by home.router now
#     return RedirectResponse(url="/")


if __name__ == "__main__":
    import uvicorn
    # This block is mainly for direct execution, `run.sh` or uvicorn command is preferred
    logger.info("Running LegalMind directly using uvicorn...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
