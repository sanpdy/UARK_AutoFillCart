import os
import logging
import tempfile
import time
import asyncio
from flask import Blueprint, request

from utils.response import success_response, error_response
from utils.conversation import (
    get_or_create_conversation, 
    load_conversation_history, 
    process_agent_message,
    store_cart_items,
    parse_request_data
)
from utils.serialization import serialize_context
from services.walmart_service import process_ingredients

logger = logging.getLogger(__name__)
chat_bp = Blueprint('chat', __name__, url_prefix='/api')

@chat_bp.route('/chat', methods=['POST'])
def chat():
    """Process chat messages and generate responses"""
    logger.info("Received request to /api/chat")
    
    # Parse request data
    data = parse_request_data(request)
    
    if not data['is_text'] and 'recipe_pdf' not in request.files:
        return error_response('Missing recipe_pdf file')
    
    if data['is_text'] and not data['recipe_text'] and not data['extracted_ingredients']:
        return error_response('Missing recipe_text parameter')
    
    conversation_id, chat_agent = get_or_create_conversation(data['conversation_id'])
    
    if isinstance(data['conversation_history'], str):
        load_conversation_history(chat_agent, data['conversation_history'])
    elif isinstance(data['conversation_history'], list):
        chat_agent.reset()
        for message in data['conversation_history']:
            chat_agent.context.append(message)
    
    # Handle PDF file upload
    if not data['is_text']:
        return handle_pdf_upload(request, chat_agent, conversation_id)

    # CRITICAL FIX: Check if we already have cart items (either from frontend or stored previously)
    existing_cart_items = getattr(chat_agent, 'cart_items', [])
    
    # Check if we have just generated cart items in the agent
    has_recent_cart_items = len(existing_cart_items) > 0
    
    # Log the current state
    logger.info(f"Cart generation state: has_cart_items={has_recent_cart_items}, skip_cart_generation={data['skip_cart_generation']}")
    
    # Process text message
    user_message = data['recipe_text'] or "Please find these ingredients for me"
    
    response = process_agent_message(
        chat_agent, 
        user_message,
        extracted_ingredients=data['extracted_ingredients'],
        force_complete=data['force_complete']
    )
    
    serializable_context = serialize_context(chat_agent.context)
    
    # CRITICAL FIX: Only process ingredients if:
    # 1. The conversation is complete AND
    # 2. We have ingredients AND
    # 3. We haven't been explicitly told to skip cart generation AND
    # 4. We don't already have cart items
    should_process_ingredients = (
        response.get('conversation_complete', False) and 
        response.get('ingredients') and 
        not data['skip_cart_generation'] and 
        not has_recent_cart_items
    )
    
    logger.info(f"Should process ingredients: {should_process_ingredients}")
    
    if should_process_ingredients:
        try:
            logger.info("Generating products for ingredients")
            cart_items = asyncio.run(process_ingredients(response.get('ingredients')))
            
            # Store cart items on the agent
            store_cart_items(chat_agent, cart_items)
            
            response_data = {
                'conversation_complete': True,
                'ingredients': response.get('ingredients'),
                'cart_items': cart_items,
                'conversation_id': conversation_id,
                'conversation_history': serializable_context
            }
            
            if hasattr(chat_agent, 'last_response_data'):
                chat_agent.last_response_data = response_data
            
            return success_response(response['message'], response_data)
        except Exception as e:
            logger.error(f"Error processing ingredients: {e}")
            return error_response(f"Error finding products: {str(e)}", 500)
    
    # Handle case where we're skipping cart generation
    if data['skip_cart_generation'] or has_recent_cart_items:
        logger.info(f"Skipping product search: skip_cart_generation={data['skip_cart_generation']}, has_recent_cart_items={has_recent_cart_items}")
    
    response_data = {
        'conversation_complete': response.get('conversation_complete', False),
        'conversation_id': conversation_id,
        'conversation_history': serializable_context,
        'conversation_state': {
            'recipe_name': getattr(chat_agent, 'recipe_name', None),
            'servings': getattr(chat_agent, 'servings', None),
            'dietary_preferences': getattr(chat_agent, 'dietary_preferences', [])
        }
    }
    
    if response.get('ingredients'):
        response_data['ingredients'] = response.get('ingredients')
    
    # CRITICAL FIX: Always include existing cart items if available
    if existing_cart_items:
        response_data['cart_items'] = existing_cart_items
    
    if hasattr(chat_agent, 'last_response_data'):
        chat_agent.last_response_data = response_data
    
    return success_response(response['message'], response_data)

def handle_pdf_upload(request, chat_agent, conversation_id):
    """Handle PDF file upload"""
    pdf_file = request.files['recipe_pdf']
    temp_dir = tempfile.gettempdir()
    pdf_path = os.path.join(temp_dir, f"recipe_{int(time.time())}.pdf")
    
    try:
        pdf_file.save(pdf_path)
        logger.info(f"Received PDF recipe, saved to: {pdf_path}")
        
        user_message = f"I'm uploading a recipe PDF called {pdf_file.filename}"
        response = chat_agent.process_chat_message(user_message)
        
        serializable_context = serialize_context(chat_agent.context)
        
        response_data = {
            'conversation_complete': False,
            'conversation_id': conversation_id,
            'conversation_history': serializable_context
        }
        
        if hasattr(chat_agent, 'last_response_data'):
            chat_agent.last_response_data = response_data
        
        return success_response(
            "I've received your recipe PDF. " + response['message'],
            response_data
        )
    finally:
        try:
            os.remove(pdf_path)
        except:
            pass
