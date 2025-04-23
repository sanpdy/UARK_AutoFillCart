import logging
import traceback
from flask import Blueprint, request

from config import active_conversations
from utils.response import success_response, error_response
from utils.conversation import get_cart_items
from services.cart_service import create_cart_url, format_cart_items_for_walmart
from agent_definitions.agents.unified_cart_autofill_agent import UnifiedCartAutofillAgent


logger = logging.getLogger(__name__)
cart_bp = Blueprint('cart', __name__, url_prefix='/api')

@cart_bp.route('/generate-cart', methods=['POST'])
def generate_cart():
    """Generate a Walmart cart URL from provided items"""
    try:
        logger.info(f"Generate cart request received")
        
        data = request.json
        if not data:
            return error_response('No JSON data received')
        #deprecated -- clean later
        conversation_id = data.get('conversation_id')
        if not conversation_id:
            return error_response('Missing conversation_id parameter')
        
        chat_agent = active_conversations.get(conversation_id)
        if not chat_agent:
            return error_response('Conversation not found', 404)
        
        # Get cart items from various sources
        cart_items = get_cart_items(chat_agent, data.get('cart_items'))
        if not cart_items:
            return error_response('No cart items found', 404)
        
        logger.info(f"Found {len(cart_items)} cart items")
        
        formatted_items = format_cart_items_for_walmart(cart_items)
        
        if not formatted_items:
            return error_response('No valid items to add to cart')
        
        try:
            # First try using UnifiedCartAutofillAgent if available
            agent = UnifiedCartAutofillAgent()
            cart_url = agent.walmart_api_wrapper.generate_walmart_cart_url(formatted_items)
            logger.info("Generated cart URL using UnifiedCartAutofillAgent")
        except Exception as e:
            logger.warning(f"Error using UnifiedCartAutofillAgent: {e}")
            
            cart_url = create_cart_url(cart_items)
            if not cart_url:
                return error_response('Failed to generate cart URL')
            logger.info("Generated cart URL using fallback method")
        
        logger.info(f"Generated cart URL")
        
        return success_response('Cart generated successfully', {'cart_url': cart_url})
    except Exception as e:
        logger.error(f"Error generating cart: {e}")
        logger.error(traceback.format_exc())
        return error_response(f"Error generating cart: {str(e)}", 500)