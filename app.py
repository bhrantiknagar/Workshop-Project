"""Application factory and entry point for SmartPDF AI."""

from flask import Flask, render_template


from config import Config
from routes.api import api_bp
from routes.chat import chat_bp
from routes.history import history_bp
from routes.home import home_bp
from routes.summary import summary_bp
from routes.upload import upload_bp
from utils.logger import configure_logger


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    configure_logger(app)

    app.register_blueprint(home_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(summary_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(api_bp)

    @app.errorhandler(404)
    def not_found(error):
        """Render a friendly page when a route cannot be found."""
        return render_template("error.html", error=error, code=404), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Render a friendly page for unexpected application errors."""
        return render_template("error.html", error=error, code=500), 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"])
