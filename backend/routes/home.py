"""Home and page-rendering routes."""

from flask import Blueprint, render_template, current_app

home_bp = Blueprint("home", __name__)


@home_bp.get("/")
def index():
    """Render the landing page."""
    return render_template("index.html", config=current_app.config)


@home_bp.get("/dashboard")
def dashboard():
    """Render the main PDF QA dashboard."""
    return render_template("dashboard.html", config=current_app.config)


@home_bp.get("/about")
def about():
    """Render the project information page."""
    return render_template("about.html", config=current_app.config)
