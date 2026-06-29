# SmartPDF AI

SmartPDF AI is a Flask starter project for an AI-powered PDF question answering dashboard. The current implementation provides a complete project structure, responsive UI, Flask blueprints, upload endpoints, and service placeholders for future Ollama, LangChain, ChromaDB, and PyMuPDF integration.

## Features

- Flask application factory with blueprints
- Responsive dashboard using Jinja templates
- PDF upload validation and storage
- Thin route handlers with business logic in services
- Placeholder services for chunking, embeddings, retrieval, LLM responses, summaries, and history
- Organized static CSS and vanilla JavaScript modules

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python app.py
```

Open `http://localhost:5000` in your browser.

## AI Integration TODO

The AI pipeline is intentionally stubbed for now. Add real logic inside the `services/` modules when you are ready to connect PyMuPDF, LangChain, ChromaDB, and Ollama.
