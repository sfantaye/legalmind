# app/services/groq_client.py
import os
import logging
from groq import Groq, AsyncGroq # Use AsyncGroq for FastAPI
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "llama3-8b-8192")

if not API_KEY:
    logger.error("GROQ_API_KEY not found in environment variables.")
    raise ValueError("GROQ_API_KEY is required.")

# Use AsyncGroq for direct async calls if needed outside LangChain/LangGraph
async_groq_client = AsyncGroq(api_key=API_KEY)

# Use ChatGroq for integration with LangChain/LangGraph
def get_groq_chat_llm() -> ChatGroq:
    """Initializes and returns the ChatGroq LLM instance."""
    try:
        chat = ChatGroq(
            temperature=0.7, # Adjust creativity
            groq_api_key=API_KEY,
            model_name=MODEL_NAME,
            # max_tokens=2048, # Optional: Set max tokens
        )
        logger.info(f"ChatGroq LLM initialized with model: {MODEL_NAME}")
        return chat
    except Exception as e:
        logger.error(f"Failed to initialize ChatGroq: {e}", exc_info=True)
        raise

# Example of a direct async call (if needed separately)
async def get_groq_completion(prompt: str, system_prompt: str = "You are a helpful legal assistant.") -> str:
    """Gets a completion directly from the Groq API (async)."""
    try:
        chat_completion = await async_groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=MODEL_NAME,
        )
        response_content = chat_completion.choices[0].message.content
        logger.info("Received completion from Groq API.")
        return response_content
    except Exception as e:
        logger.error(f"Error calling Groq API: {e}", exc_info=True)
        return "Sorry, I encountered an error trying to contact the AI service."

# Initialize once
try:
    chat_llm = get_groq_chat_llm()
except Exception as e:
    chat_llm = None # Handle gracefully if initialization fails
    logger.error("Could not initialize Groq Chat LLM on startup.")
