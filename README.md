# 🧠 LegalMind – Your AI Legal Assistant

LegalMind is an AI-powered legal assistant that helps users understand legal documents, ask legal questions in plain language, and generate contracts using advanced LLMs via the Groq API. It’s built using FastAPI, Jinja2 for templating, and LangGraph for stateful workflows.

## Features

- 🗂️ Upload & analyze legal documents (PDF/DOCX)
- 🧾 Generate AI-crafted contracts like NDAs and rental agreements
- 🤖 Chat with an intelligent legal assistant
- 🔁 Multi-step conversations with LangGraph
- 🌐 Simple and responsive web interface using Jinja2

## Tech Stack

- **FastAPI** – Web framework
- **Groq API** – LLM inference
- **LangGraph** – Stateful workflows
- **Jinja2** – Templating
- **pypdf/python-docx** – Document parsing

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/sfantaye/legalmind.git
    cd legalmind
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure environment variables:**
    - Create a `.env` file in the project root.
    - Add your Groq API key:
      ```env
      GROQ_API_KEY="YOUR_GROQ_API_KEY"
      GROQ_MODEL_NAME="llama3-8b-8192" # Optional: specify model
      ```
5.  **Run the application:**
    ```bash
    ./run.sh
    # OR
    uvicorn app.main:app --reload
    ```
6.  Access the application at `http://localhost:8000`.

