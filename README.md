# SmartPDF AI

SmartPDF AI is a Flask-based web application for uploading PDFs, previewing extracted content, and testing local Ollama LLM responses. The project is now organized into a `backend/` folder for Python server logic and a `frontend/` folder for static assets and templates.

## Project Overview

This project is designed as an educational prototype for a PDF AI assistant. It currently supports:

- uploading PDF files
- previewing extracted text
- a temporary LLM test panel for verifying Ollama connectivity
- clean separation between backend and frontend resources
- error handling for Ollama availability, missing models, empty prompts, and timeouts

## Repository Structure

```
Workshop_Project/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── routes/
│   ├── services/
│   ├── utils/
│   ├── tests/
│   ├── data/
│   ├── database/
│   ├── logs/
│   ├── models/
│   ├── prompts/
│   ├── .env
│   ├── .env.example
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   └── templates/
└── .venv/
```

## What Changed

- backend code is now under `backend/`
- frontend templates and static assets are now under `frontend/`
- `backend/app.py` is configured to load `frontend/templates` and `frontend/static`
- environment variables are loaded from `backend/.env`
- the root project now acts as a container for the two main folders

## Prerequisites

Make sure you have the following installed:

- Python 3.11+ (or compatible version)
- Git (optional)
- Ollama locally installed and running
- `pip` available in your Python environment

## Install Dependencies

Open PowerShell and run:

```powershell
cd D:\Workshop_Project\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```
 
Then edit `backend/.env` if you need to override values:

```text
FLASK_DEBUG=true
SECRET_KEY=replace-with-a-secure-secret
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:latest
OLLAMA_TIMEOUT=180
```

## Start the Application from PowerShell

From the `backend` folder, run:

```powershell
cd D:\Workshop_Project\backend
.\.venv\Scripts\Activate.ps1
python app.py
```

Open the browser at:

```text
http://localhost:5000
```

## Verify Ollama

Before using the LLM Test panel, make sure Ollama is running and the model is available:

```powershell
ollama list
ollama ps
```

If the model is not available, pull it by running:

```powershell
ollama pull llama3:latest
```

If Ollama is already running, you can verify the server with:

```powershell
curl.exe http://localhost:11434/api/tags
```

## How to Use

1. Start the backend server from `backend/`
2. Open `http://localhost:5000`
3. Upload a PDF using the homepage upload widget
4. Preview extracted PDF text
5. Use the `LLM Test` panel to send a prompt to your local Ollama model

## Tech Stack

- Python 3
- Flask web framework
- Jinja2 templating
- Vanilla JavaScript for frontend interactions
- HTML/CSS for responsive UI
- PyMuPDF for PDF extraction
- Ollama for local LLM inference

## Libraries Used

- `Flask`
- `python-dotenv`
- `PyMuPDF`
- `chromadb`
- `langchain`
- `langchain-community`
- `langchain-ollama`
- `ollama`

## Notes for Teachers

This project is structured to separate frontend and backend concerns. The backend handles:

- route definitions in `backend/routes/`
- Ollama integration and service logic in `backend/services/`
- configuration in `backend/config.py`

The frontend handles:

- UI templates in `frontend/templates/`
- static assets in `frontend/static/`

This setup allows you to show clean architecture and future extension points for RAG, embeddings, ChromaDB, and PDF analysis.

## Future Work

- connect uploaded PDF content to the LLM prompt flow
- implement retrieval-augmented generation (RAG)
- add persistent chat history
- add more test coverage under `backend/tests/`
- add production deployment instructions with a WSGI server
