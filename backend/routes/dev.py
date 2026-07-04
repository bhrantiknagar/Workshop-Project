"""Developer routes for inspecting embeddings and triggering generation."""

from flask import Blueprint, current_app, render_template, request, jsonify

from services.embedding_service import (
    generate_embeddings_for_all_pdfs,
    list_embeddings,
    EmbeddingError,
)
from services.vector_store import get_collection_info
from services.vector_store import search_similar_chunks, VectorStoreError

dev_bp = Blueprint("dev", __name__, url_prefix="/dev")


@dev_bp.get("/embeddings")
def embeddings_dashboard():
    """Render developer view showing embedding summaries and samples."""
    store = list_embeddings()

    summaries = []
    from services.vector_store import get_collection_info

    collection_info = get_collection_info()

    for pdf_id, chunks in store.items():
        embedding_dim = len(chunks[0]["embedding"]) if chunks else 0
        summaries.append(
            {
                "filename": chunks[0].get("filename") if chunks else pdf_id,
                "pdf_id": pdf_id,
                "chunks": len(chunks),
                "embedding_dim": embedding_dim,
                "status": "Generated" if chunks else "No chunks",
                "samples": [
                    {
                        "chunk_id": c["chunk_id"],
                        "preview": c["text"][:100],
                        "embedding_length": len(c["embedding"]),
                    }
                    for c in chunks[:5]
                ],
            }
        )

    return render_template("dev_embeddings.html", summaries=summaries, collection=collection_info)


@dev_bp.post("/generate")
def generate_embeddings():
    """Trigger embedding generation for all PDFs in the configured upload folder.

    Returns JSON with summaries for the processed PDFs.
    """
    upload_folder = current_app.config.get("UPLOAD_FOLDER")

    if not upload_folder:
        return jsonify({"success": False, "message": "UPLOAD_FOLDER not configured."}), 500

    try:
        summaries = generate_embeddings_for_all_pdfs(upload_folder)
    except EmbeddingError as exc:
        current_app.logger.exception("Embedding generation failed")
        return jsonify({"success": False, "message": str(exc)}), 500
    except Exception:
        current_app.logger.exception("Unexpected error during embedding generation")
        return (
            jsonify({"success": False, "message": "Unexpected error during embedding generation."}),
            500,
        )

    total_stored = sum(item.get("stored_embeddings", 0) for item in summaries)
    message = f"Successfully stored {total_stored} embeddings in ChromaDB."
    if request.is_json:
        return (
            jsonify(
                {
                    "success": True,
                    "message": message,
                    "summaries": summaries,
                }
            ),
            200,
        )

    collection = get_collection_info()
    return render_template(
        "dev_embeddings.html",
        summaries=summaries,
        collection=collection,
        message=message,
    )


@dev_bp.get("/search")
def search_page():
    """Render a simple developer search UI for semantic retrieval."""
    return render_template("dev_search.html")


@dev_bp.post("/search")
def run_search():
    """Handle search requests from the developer UI and show top chunks."""
    question = request.form.get("question", "").strip()
    if not question:
        return render_template("dev_search.html", error="Please enter a question.")

    try:
        results = search_similar_chunks(question, top_k=5)
    except VectorStoreError as exc:
        return render_template("dev_search.html", error=str(exc))
    except Exception:
        current_app.logger.exception("Unexpected error during search")
        return render_template("dev_search.html", error="Unexpected search error.")

    if not results:
        return render_template("dev_search.html", question=question, results=[], message="No matching chunks found.")

    return render_template("dev_search.html", question=question, results=results)
