import logging
from flask import Blueprint, request

from config import active_conversations
from utils.response import success_response, error_response
from utils.conversation import get_cart_items, store_cart_items
from services.cart_service import substitute_product

logger = logging.getLogger(__name__)
substitute_bp = Blueprint('substitute', __name__, url_prefix='/api')

@substitute_bp.route('/substitute', methods=['POST'])
def handle_substitute():
    """Substitute a product with an alternative"""
    data = request.json
    
    if not data:
        return error_response('No JSON data received')
    
    logger.info(f"Substitute request received")
    
    required_fields = ['ingredient_index', 'substitute_index', 'conversation_id']
    if not all(field in data for field in required_fields):
        return error_response('Missing required parameters')
    
    ingredient_index = data['ingredient_index']
    substitute_index = data['substitute_index']
    conversation_id = data['conversation_id']
    
    chat_agent = active_conversations.get(conversation_id)
    if not chat_agent:
        return error_response('Conversation not found', 404)
    
    cart_items = get_cart_items(chat_agent, data.get('cart_items'))
    if not cart_items:
        return error_response('No cart items found for this conversation', 404)
    
    try:
        result = substitute_product(cart_items, ingredient_index, substitute_index)
        
        if not result['success']:
            return error_response(result['message'])
        
        store_cart_items(chat_agent, result['cart_items'])
        
        return success_response('Product substituted successfully', {'cart_items': result['cart_items']})
    except Exception as e:
        logger.error(f"Error substituting product: {e}", exc_info=True)
        return error_response(f"Error substituting product: {str(e)}", 500)