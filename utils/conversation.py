import json
import logging
from uuid import uuid4

from config import active_conversations, create_chat_agent

logger = logging.getLogger(__name__)

def get_or_create_conversation(conversation_id=None):
    """
    Get an existing conversation or create a new one
    """
    if conversation_id and conversation_id in active_conversations:
        logger.info(f"Using existing conversation: {conversation_id}")
        return conversation_id, active_conversations[conversation_id]
    
    new_id = str(uuid4())
    logger.info(f"Creating new conversation: {new_id}")
    active_conversations[new_id] = create_chat_agent()
    return new_id, active_conversations[new_id]

def load_conversation_history(chat_agent, conversation_history):
    """
    Load conversation history into the chat agent
    """
    try:
        history = json.loads(conversation_history)
        chat_agent.reset()
        for message in history:
            chat_agent.context.append(message)
        logger.info(f"Loaded conversation history with {len(history)} messages")
    except json.JSONDecodeError:
        logger.warning("Failed to parse conversation history")

def process_agent_message(chat_agent, user_message, extracted_ingredients=None, force_complete=False):
    """
    Process a message with the chat agent
    """
    response = chat_agent.process_chat_message(
        user_message,
        frontend_ingredients=extracted_ingredients,
        force_complete=force_complete
    )
    
    if extracted_ingredients and not getattr(chat_agent, 'extracted_ingredients', None):
        setattr(chat_agent, 'extracted_ingredients', extracted_ingredients)
        
        if len(extracted_ingredients) > 0:
            setattr(chat_agent, 'conversation_complete', True)
            response['conversation_complete'] = True
            response['ingredients'] = extracted_ingredients
    
    return response

def get_cart_items(chat_agent, frontend_cart_items=None):
    """
    Get cart items from the agent or frontend
    """
    logger.debug("Retrieving cart items")
    
    if frontend_cart_items and len(frontend_cart_items) > 0:
        logger.debug(f"Using {len(frontend_cart_items)} cart items from frontend")
        return frontend_cart_items
    
    
    if hasattr(chat_agent, 'cart_items') and chat_agent.cart_items:
        logger.debug(f"Found {len(chat_agent.cart_items)} cart items in agent.cart_items")
        return chat_agent.cart_items
    
    if hasattr(chat_agent, 'get_cart_items') and callable(chat_agent.get_cart_items):
        try:
            items = chat_agent.get_cart_items()
            if items and len(items) > 0:
                logger.debug(f"Found {len(items)} cart items via get_cart_items()")
                return items
        except Exception as e:
            logger.error(f"Error calling get_cart_items: {str(e)}")
    
    if hasattr(chat_agent, 'last_response_data') and 'cart_items' in chat_agent.last_response_data:
        items = chat_agent.last_response_data.get('cart_items', [])
        logger.debug(f"Found {len(items)} cart items in last_response_data")
        return items
    
    if hasattr(chat_agent, 'extracted_ingredients') and chat_agent.extracted_ingredients:
        logger.debug("Found extracted_ingredients but no cart items. Cart needs to be generated first.")
    
    logger.warning("No cart items found")
    return []

def store_cart_items(chat_agent, cart_items):
    """
    Store cart items on the chat agent
    """
    if not cart_items:
        logger.warning("Attempted to store empty cart items")
        return
    
    logger.info(f"Stored {len(cart_items)} cart items on the agent")
    
    chat_agent.cart_items = cart_items
    
    if hasattr(chat_agent, 'set_cart_items') and callable(chat_agent.set_cart_items):
        try:
            chat_agent.set_cart_items(cart_items)
        except Exception as e:
            logger.error(f"Error calling set_cart_items: {str(e)}")
    
    if hasattr(chat_agent, 'last_response_data'):
        chat_agent.last_response_data['cart_items'] = cart_items

def parse_request_data(request):
    """
    Parse and normalize request data from different formats
    """
    data = {
        'is_text': True,
        'recipe_text': None,
        'conversation_id': None,
        'conversation_history': [],
        'extracted_ingredients': None,
        'skip_cart_generation': False,
        'force_complete': False
    }
    
    if request.content_type and request.content_type.startswith('application/json'):
        req_data = request.json or {}
        data['is_text'] = req_data.get('isText', True)
        data['recipe_text'] = req_data.get('recipe_text')
        data['conversation_id'] = req_data.get('conversation_id')
        data['conversation_history'] = req_data.get('conversation_history', [])
        data['extracted_ingredients'] = req_data.get('extracted_ingredients')
        data['skip_cart_generation'] = req_data.get('skip_cart_generation', False)
        data['force_complete'] = req_data.get('force_complete', False)
    else:  # Form data
        data['is_text'] = request.form.get('isText', 'true').lower() == 'true'
        data['recipe_text'] = request.form.get('recipe_text')
        data['conversation_id'] = request.form.get('conversation_id')
        
        try:
            conversation_history = request.form.get('conversation_history', '[]')
            data['conversation_history'] = json.loads(conversation_history)
        except json.JSONDecodeError:
            logger.warning("Invalid conversation history format, using empty list")
            data['conversation_history'] = []
            
        if request.form.get('extracted_ingredients'):
            try:
                data['extracted_ingredients'] = json.loads(request.form.get('extracted_ingredients'))
            except json.JSONDecodeError:
                logger.warning("Invalid extracted ingredients format")
        
        data['skip_cart_generation'] = request.form.get('skip_cart_generation', 'false').lower() == 'true'
        data['force_complete'] = request.form.get('force_complete', 'false').lower() == 'true'
    
    return data