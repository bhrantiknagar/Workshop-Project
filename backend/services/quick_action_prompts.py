"""Prompt templates for PDF quick AI actions."""

QUICK_ACTIONS = {
    "summarize": {
        "label": "Summarize PDF",
        "prompt": (
            "Generate a concise summary of the uploaded PDF content. "
            "Use only the retrieved PDF context. Include the main topic, purpose, "
            "important sections, and final takeaway."
        ),
    },
    "study_notes": {
        "label": "Generate Study Notes",
        "prompt": (
            "Create revision study notes from the uploaded PDF content. "
            "Use clear headings, short explanations, and exam-friendly bullets. "
            "Use only the retrieved PDF context."
        ),
    },
    "key_points": {
        "label": "Extract Key Points",
        "prompt": (
            "Extract the 10 most important points from the uploaded PDF content. "
            "Return a numbered list. Use only the retrieved PDF context."
        ),
    },
    "quiz": {
        "label": "Generate Quiz",
        "prompt": (
            "Generate 10 multiple-choice questions from the uploaded PDF content. "
            "Each question should have four options and include the correct answer. "
            "Use only the retrieved PDF context."
        ),
    },
    "flashcards": {
        "label": "Generate Flashcards",
        "prompt": (
            "Generate question-and-answer flashcards from the uploaded PDF content. "
            "Use the format Question -> Answer. Use only the retrieved PDF context."
        ),
    },
}
