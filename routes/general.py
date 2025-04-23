import logging
from flask import Blueprint
from config import active_conversations
from utils.response import success_response

logger = logging.getLogger(__name__)
general_bp = Blueprint('general', __name__, url_prefix='/api')

@general_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return success_response('Flask backend with Recipe Chat Agent is running', {
        'status': 'healthy',
        'active_conversations': len(active_conversations)
    })

@general_bp.route('/', methods=['GET'])
def index():
    """Root endpoint with API information"""
    return success_response('Walmart Recipe API is running', {
        'endpoints': [
            '/api/health',
            '/api/chat',
            '/api/substitute',
            '/api/generate-cart',
            '/api/search-product'
        ]
    })