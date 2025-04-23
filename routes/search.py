import logging
import asyncio
from flask import Blueprint, request

from utils.response import success_response, error_response
from services.walmart_service import search_product

logger = logging.getLogger(__name__)
search_bp = Blueprint('search', __name__, url_prefix='/api')

@search_bp.route('/search-product', methods=['POST'])
def handle_search_product():
    """Search for a single product"""
    data = request.json
    
    if not data or 'query' not in data:
        return error_response('Missing query parameter')
    
    query = data.get('query')
    quantity = data.get('quantity', '')
    
    try:
        search_results = asyncio.run(search_product(query))
        products = search_results.get('items', [])
        
        if not products:
            return success_response(f"No products found for {query}", {
                'success': False,
                'query': query
            })
        
        main_product = products[0]
        alternatives = products[1:4] if len(products) > 1 else []
        
        main_item = {
            'id': main_product.get('itemId'),
            'name': main_product.get('name', 'Unknown product'),
            'image': main_product.get('image', ''),
            'price': main_product.get('price', {}).get('priceString', 'Price unavailable')
        }
        
        alt_items = []
        for alt in alternatives:
            alt_items.append({
                'item_details': alt,
                'id': alt.get('itemId'),
                'name': alt.get('name', 'Unknown product'),
                'image': alt.get('image', ''),
                'price': alt.get('price', {}).get('priceString', 'Price unavailable')
            })
        
        return success_response(f"Found products for {query}", {
            'success': True,
            'product': main_item,
            'alternatives': alt_items,
            'query': query,
            'quantity': quantity
        })
    except Exception as e:
        logger.error(f"Error searching for product {query}: {e}")
        return error_response(f"Error searching for product: {str(e)}", 500)