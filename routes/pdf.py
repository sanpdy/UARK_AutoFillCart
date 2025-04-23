import os
import logging
import tempfile
import time
import asyncio
from flask import Blueprint, request
from utils.response import success_response, error_response
from utils.conversation import get_or_create_conversation, serialize_context, store_cart_items
from ..agent_definitions.agents.ingredient_extractor_agent import IngredientExtractorAgent
from services.walmart_service import process_ingredients
from pdfminer.high_level import extract_text
from utils.pdf_to_txt_util import replace_fractions

logger = logging.getLogger(__name__)
pdf_bp = Blueprint('pdf', __name__, url_prefix='/api')

@pdf_bp.route('/process-pdf', methods=['POST'])
async def process_pdf():
    """Process a PDF file and extract ingredients directly"""
    if 'recipe_pdf' not in request.files:
        return error_response('Missing recipe_pdf file')
    
    pdf_file = request.files['recipe_pdf']
    temp_dir = tempfile.gettempdir()
    pdf_path = os.path.join(temp_dir, f"recipe_{int(time.time())}.pdf")
    
    try:
        pdf_file.save(pdf_path)
        logger.info(f"Received PDF recipe, saved to: {pdf_path}")
        
        pdf_text = extract_text(pdf_path)
        pdf_text = replace_fractions(pdf_text)
        
        logger.info(f"Successfully extracted text from PDF ({len(pdf_text)} characters)")
        
        # Create a new conversation
        conversation_id, chat_agent = get_or_create_conversation()
        
        ingredient_extractor = IngredientExtractorAgent()
        ingredients = ingredient_extractor.extract_ingredients_from_recipe(pdf_text)
        
        if not ingredients or len(ingredients) == 0:
            return error_response('Could not extract ingredients from the PDF')
        
        logger.info(f"Successfully extracted {len(ingredients)} ingredients from PDF")
        
        cart_items = await process_ingredients(ingredients)
        
        chat_agent.extracted_ingredients = ingredients
        store_cart_items(chat_agent, cart_items)
        
        chat_agent.context.append({
            'role': 'user',
            'content': f"I've uploaded a recipe file: {pdf_file.filename}"
        })
        
        chat_agent.context.append({
            'role': 'assistant',
            'content': f"I've extracted the ingredients from your recipe and found matching products at Walmart."
        })
        
        chat_agent.conversation_complete = True
        
        serializable_context = serialize_context(chat_agent.context)
        
        response_data = {
            'conversation_complete': True,
            'ingredients': ingredients,
            'cart_items': cart_items,
            'conversation_id': conversation_id,
            'conversation_history': serializable_context,
            'pdf_filename': pdf_file.filename
        }
        
        return success_response(
            f"Successfully processed recipe from {pdf_file.filename}",
            response_data
        )
    except Exception as e:
        logger.error(f"Error processing PDF: {e}", exc_info=True)
        return error_response(f"Error processing PDF: {str(e)}", 500)
    finally:
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
        except Exception as e:
            logger.error(f"Error removing temporary PDF file: {e}")