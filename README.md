# SmartPDF AI

SmartPDF AI is a Flask RAG application for uploading PDFs, retrieving relevant pages with ChromaDB, and answering questions with cloud AI services.

## Cloud configuration

Create `backend/.env` from `backend/.env.example` and set:

```text
FLASK_DEBUG=true
SECRET_KEY=replace-with-a-secure-secret
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama-3.1-8b-instant
GROQ_TIMEOUT=60
GOOGLE_API_KEY=your-google-api-key
GOOGLE_EMBEDDING_MODEL=models/gemini-embedding-001
```

Groq generates answers through LangChain's `ChatGroq`. Google Gemini creates hosted embeddings; no local LLM or embedding model is downloaded or cached. ChromaDB persists the resulting vectors under `backend/database/chroma_db`.

## Run locally

```powershell
cd D:\Workshop_Project\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000`, upload one or two PDFs, and use PDF Chat, comparison, or Quick AI Actions. Deployments must supply both cloud API keys as environment variables.

## Stack

- Flask and PyMuPDF for the application and PDF extraction
- ChromaDB for vector persistence
- LangChain Groq for chat generation
- LangChain Google GenAI for cloud embeddings
