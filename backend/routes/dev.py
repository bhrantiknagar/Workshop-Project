"""Developer routes for inspecting embeddings and triggering generation."""

from flask import Blueprint, current_app, render_template, jsonify

from services.embedding_service import (
    generate_embeddings_for_all_pdfs,
    list_embeddings,
    EmbeddingError,
)

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

    return jsonify({"success": True, "summaries": summaries}), 200
