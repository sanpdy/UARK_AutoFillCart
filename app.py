from flask import Flask
from flask_cors import CORS
import logging
from routes.chat import chat_bp
from routes.substitute import substitute_bp
from routes.cart import cart_bp
from routes.search import search_bp
from routes.general import general_bp
from config import configure_logging
import sys
import os

#allows me to run as file and not as module. caused too many problems for me to want to go back and fix. dirty fix for now.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def create_app():
    """Create and configure the Flask application"""
    # Configure logging
    configure_logging()
    logger = logging.getLogger(__name__)
    
    # Create Flask app
    app = Flask(__name__)
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(chat_bp)
    app.register_blueprint(substitute_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(general_bp)
    
    logger.info("Flask app configured with all routes")
    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    logging.getLogger(__name__).info("Starting Flask server with Recipe Chat Agent...")
    app.run(host='0.0.0.0', port=8080, debug=True)