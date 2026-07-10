# SmartPDF AI backend

The backend is a Flask RAG service. PDFs are extracted with PyMuPDF, embedded by the Google Gemini embedding API, stored in ChromaDB, and answered through Groq using LangChain `ChatGroq`.

## Setup

```powershell
cd D:\Workshop_Project\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python app.py
```

Configure these values in `.env` or your deployment provider:

```text
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama-3.1-8b-instant
GROQ_TIMEOUT=60
GOOGLE_API_KEY=your-google-api-key
GOOGLE_EMBEDDING_MODEL=models/gemini-embedding-001
```

The service requires internet access for generation and embeddings. No local AI runtime, model download, or embedding cache is used.
