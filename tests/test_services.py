# tests/test_services.py
import pytest
import os
from unittest.mock import patch, AsyncMock

# Assuming tests are run from the root 'legalmind' directory
from app.utils.pdf_parser import extract_text_from_pdf, extract_text_from_docx, extract_text
from app.services import groq_client
# LangGraph testing is complex, focus on simpler units here

# Fixtures for sample file content
@pytest.fixture
def sample_pdf_bytes():
    # In a real test suite, you might load a small test PDF file
    # For simplicity, we'll mock the pypdf behavior
    return b"%PDF-1.4 fake pdf content"

@pytest.fixture
def sample_docx_bytes():
    # Similarly, mock python-docx behavior or use a tiny test file
    return b"PK\x03\x04..." # Fake DOCX header

# --- Test pdf_parser ---

@pytest.mark.asyncio
@patch('app.utils.pdf_parser.PdfReader')
async def test_extract_pdf_success(mock_pdf_reader, sample_pdf_bytes):
    """Test successful PDF text extraction using mocking."""
    # Configure the mock PdfReader
    mock_page = AsyncMock()
    mock_page.extract_text.return_value = "Page 1 text. "
    mock_reader_instance = AsyncMock()
    mock_reader_instance.pages = [mock_page, mock_page] # Simulate 2 pages
    mock_pdf_reader.return_value = mock_reader_instance

    text = await extract_text_from_pdf(sample_pdf_bytes)

    assert text == "Page 1 text. \nPage 1 text."
    mock_pdf_reader.assert_called_once() # Check PdfReader was initialized

@pytest.mark.asyncio
@patch('app.utils.pdf_parser.PdfReader')
async def test_extract_pdf_error(mock_pdf_reader, sample_pdf_bytes):
    """Test PDF extraction handling errors."""
    mock_pdf_reader.side_effect = Exception("PDF parse error")

    text = await extract_text_from_pdf(sample_pdf_bytes)
    assert text == "" # Should return empty string on error

@pytest.mark.asyncio
@patch('app.utils.pdf_parser.Document')
async def test_extract_docx_success(mock_document, sample_docx_bytes):
     """Test successful DOCX text extraction using mocking."""
     mock_para1 = AsyncMock()
     mock_para1.text = "Paragraph 1."
     mock_para2 = AsyncMock()
     mock_para2.text = "Paragraph 2."
     mock_doc_instance = AsyncMock()
     mock_doc_instance.paragraphs = [mock_para1, mock_para2]
     mock_document.return_value = mock_doc_instance

     text = await extract_text_from_docx(sample_docx_bytes)
     assert text == "Paragraph 1.\nParagraph 2."
     mock_document.assert_called_once()

@pytest.mark.asyncio
async def test_extract_unsupported_type(sample_pdf_bytes):
     """Test the main extract function with an unsupported extension."""
     text = await extract_text("document.txt", b"some text content")
     assert text == ""

# --- Test groq_client ---

def test_groq_api_key_load():
    """Test if API key loading is attempted (requires .env or env var)."""
    # This mainly tests if the module loads without immediate error
    # We expect GROQ_API_KEY to be loaded via load_dotenv()
    # In a CI/CD environment, you'd set this as an environment variable
    # For local testing, ensure .env exists and has a (potentially fake) key
    if not os.getenv("GROQ_API_KEY"):
         print("\nWarning: GROQ_API_KEY not set for groq_client tests. Skipping API interaction tests.")
         pytest.skip("GROQ_API_KEY not set")

    assert groq_client.API_KEY is not None
    assert len(groq_client.API_KEY) > 0


# Requires GROQ_API_KEY to be set
@pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="GROQ_API_KEY not set")
def test_get_groq_chat_llm_initialization():
     """Test ChatGroq instance creation."""
     llm = groq_client.get_groq_chat_llm()
     # Check if it's the correct type (or has expected attributes)
     assert hasattr(llm, "invoke") # Basic check for LangChain LLM interface
     assert llm.model_name == groq_client.MODEL_NAME


# Example test for direct async Groq call (requires mocking the API call itself)
@pytest.mark.asyncio
@patch('app.services.groq_client.async_groq_client.chat.completions.create', new_callable=AsyncMock)
async def test_get_groq_completion_mocked(mock_create_completion):
     """Test the direct async Groq call helper with mocking."""
     # Configure the mock response
     mock_choice = AsyncMock()
     mock_choice.message.content = "Mocked AI Response"
     mock_completion_result = AsyncMock()
     mock_completion_result.choices = [mock_choice]
     mock_create_completion.return_value = mock_completion_result

     prompt = "What is the capital of France?"
     response = await groq_client.get_groq_completion(prompt)

     assert response == "Mocked AI Response"
     mock_create_completion.assert_called_once()
     # You could add more assertions here to check the messages sent to the mock


# --- Test contract_templates ---
from app.utils.contract_templates import get_contract_prompt

def test_get_nda_prompt():
    prompt = get_contract_prompt("nda")
    assert prompt is not None
    assert "Non-Disclosure Agreement" in prompt
    assert "[Party 1 Name]" in prompt

def test_get_rental_prompt():
    prompt = get_contract_prompt("rental_agreement")
    assert prompt is not None
    assert "Residential Rental Agreement" in prompt
    assert "[Landlord Name]" in prompt

def test_get_unknown_prompt():
    prompt = get_contract_prompt("unknown_type")
    assert prompt is None
