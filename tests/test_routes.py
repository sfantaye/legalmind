# tests/test_routes.py
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import io

# Adjust import path based on your project structure
# If running pytest from root, this should work:
from app.main import app
# Mock the document store for isolated testing
from app.routes import home, assistant

@pytest.fixture(scope="module")
def client():
    """Create a TestClient instance for the FastAPI app."""
    return TestClient(app)

@pytest.fixture(autouse=True)
def reset_document_store():
    """Clear the in-memory document store before each test."""
    home.document_store.clear()
    assistant.document_store.clear() # Ensure assistant uses the same store reference
    yield # Run the test
    home.document_store.clear()
    assistant.document_store.clear()


def test_read_root(client: TestClient):
    """Test the homepage endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "<h1>Welcome to LegalMind!</h1>" in response.text # Check for specific content

def test_upload_form(client: TestClient):
    """Test the upload form GET endpoint."""
    response = client.get("/upload")
    assert response.status_code == 200
    assert '<form action="/upload"' in response.text

def test_handle_upload_pdf_success(client: TestClient, monkeypatch):
    """Test successful PDF upload and text extraction."""
    # Mock the extract_text function to avoid actual parsing
    async def mock_extract_text(filename: str, content: bytes):
         assert filename == "test.pdf"
         assert content == b"fake pdf content"
         return "Extracted text from PDF."

    monkeypatch.setattr("app.routes.home.extract_text", mock_extract_text)

    file_content = b"fake pdf content"
    files = {'file': ('test.pdf', io.BytesIO(file_content), 'application/pdf')}

    # Expect a redirect (307 is default for TestClient, FastAPI uses 303 in code)
    # Allow redirects to follow it to the chat page.
    response = client.post("/upload", files=files, allow_redirects=False) # Test the redirect itself first

    assert response.status_code == 303 # Check for 303 See Other
    assert response.headers["location"].startswith("/assistant/")

    # Check if context was stored (need the session_id from location)
    session_id = response.headers["location"].split("/")[-1]
    assert session_id in home.document_store
    assert home.document_store[session_id] == "Extracted text from PDF."

def test_handle_upload_unsupported(client: TestClient, monkeypatch):
     """Test upload of an unsupported file type."""
     async def mock_extract_text_empty(filename: str, content: bytes):
          assert filename == "test.txt"
          return "" # Simulate unsupported type returning empty string

     monkeypatch.setattr("app.routes.home.extract_text", mock_extract_text_empty)

     files = {'file': ('test.txt', io.BytesIO(b"some text"), 'text/plain')}
     response = client.post("/upload", files=files, allow_redirects=False)

     assert response.status_code == 303 # Should still redirect
     session_id = response.headers["location"].split("/")[-1]
     assert session_id in home.document_store
     assert home.document_store[session_id] == "" # Context should be empty

def test_chat_page(client: TestClient):
    """Test accessing the chat page directly (without upload context)."""
    # Fake a session ID
    session_id = "fake_session_no_doc"
    response = client.get(f"/assistant/{session_id}")
    assert response.status_code == 200
    assert f"Session ID: {session_id}" in response.text
    assert "No document uploaded for this session" in response.text

def test_chat_page_with_context(client: TestClient):
    """Test accessing chat page when context should exist."""
    session_id = "fake_session_with_doc"
    home.document_store[session_id] = "Some document text." # Manually add context

    response = client.get(f"/assistant/{session_id}")
    assert response.status_code == 200
    assert f"Session ID: {session_id}" in response.text
    assert "Document context is loaded" in response.text

# Test chat POST endpoint (requires mocking LangGraph) - More complex
@pytest.mark.asyncio
async def test_handle_chat_post(client: TestClient, monkeypatch):
    """Test POSTing a message to the chat endpoint."""
    session_id = "test_chat_session"
    home.document_store[session_id] = "Document context for chat." # Add context

    # Mock the langgraph flow function
    async def mock_run_chat_flow(user_input, sid, doc_context):
        assert user_input == "Hello AI!"
        assert sid == session_id
        assert doc_context == "Document context for chat."
        return "AI says hello back!"

    monkeypatch.setattr("app.routes.assistant.run_chat_flow", mock_run_chat_flow)

    response = client.post(
        f"/assistant/chat/{session_id}",
        data={"user_input": "Hello AI!"} # Send as form data
    )

    assert response.status_code == 200
    assert response.json() == {"response": "AI says hello back!"}

@pytest.mark.asyncio
async def test_handle_chat_generate_contract(client: TestClient, monkeypatch):
    """Test triggering contract generation via chat."""
    session_id = "test_contract_session"

    async def mock_run_contract_flow(contract_type, details, sid):
         assert contract_type == "NDA"
         assert details == "Parties are X and Y."
         assert sid == session_id
         return "Generated NDA text..."

    monkeypatch.setattr("app.routes.assistant.run_contract_flow", mock_run_contract_flow)

    response = client.post(
        f"/assistant/chat/{session_id}",
        data={"user_input": "generate contract: NDA: Parties are X and Y."}
    )

    assert response.status_code == 200
    assert response.json() == {"response": "Generated NDA text..."}


def test_health_check(client: TestClient):
     """Test the health check endpoint."""
     response = client.get("/health")
     assert response.status_code == 200
     assert response.json() == {"status": "ok"}
