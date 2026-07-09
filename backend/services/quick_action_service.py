"""Quick AI actions powered by the existing RAG service."""

from typing import Dict, List, Optional

from services.quick_action_prompts import QUICK_ACTIONS
from services.rag_service import answer_with_rag
from services.vector_store import VectorStoreError


def run_quick_action(
    action: str,
    pdf_ids: Optional[List[str]] = None,
    provider: Optional[str] = None,
) -> Dict:
    """Run a predefined action through the existing RAG workflow."""
    action_key = (action or "").strip().lower()
    action_config = QUICK_ACTIONS.get(action_key)
    if not action_config:
        raise VectorStoreError("Unknown quick AI action.")

    pdf_ids = [str(pdf_id) for pdf_id in (pdf_ids or []) if pdf_id]
    if not pdf_ids:
        raise VectorStoreError("Upload at least one PDF before using Quick AI Actions.")

    result = answer_with_rag(
        action_config["prompt"],
        top_k=14,
        pdf_ids=pdf_ids,
        provider=provider,
    )
    result["action"] = action_key
    result["action_label"] = action_config["label"]
    return result
