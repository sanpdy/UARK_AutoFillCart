import json
import asyncio
import logging
from config import get_walmart_api

logger = logging.getLogger(__name__)
walmart_api = get_walmart_api()

async def search_product(query):
    """
    Search for a product in Walmart's API
    """
    try:
        search_results_str = await asyncio.to_thread(
            walmart_api.get_walmart_search_results,
            query
        )
        return json.loads(search_results_str)
    except Exception as e:
        logger.error(f"Error searching for product {query}: {e}")
        return {"items": []}

async def process_ingredients(ingredients):
    """
    Process ingredients to find Walmart products
    """
    cart_items = []
    
    for ingredient in ingredients:
        ingredient_name = ingredient.get('ingredient', '')
        ingredient_quantity = ingredient.get('quantity', '')
        
        try:
            search_results = await search_product(ingredient_name)
            products = search_results.get('items', [])
            
            if not products:
                cart_items.append({
                    'main': {
                        'id': 0,
                        'name': f"{ingredient_name} (Not found)",
                        'image': '',
                        'quantity': ingredient_quantity,
                        'price': 'Not available'
                    },
                    'alternatives': [],
                    'original_ingredient': {
                        'name': ingredient_name,
                        'quantity': ingredient_quantity
                    }
                })
                continue
            
            main_product = products[0]
            alternatives = products[1:4] if len(products) > 1 else []
            
            main_item = {
                'id': main_product.get('itemId'),
                'name': main_product.get('name', 'Unknown product'),
                'image': main_product.get('image', ''),
                'quantity': ingredient_quantity,
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
            
            cart_items.append({
                'main': main_item,
                'alternatives': alt_items,
                'original_ingredient': {
                    'name': ingredient_name,
                    'quantity': ingredient_quantity
                }
            })
        except Exception as e:
            logger.error(f"Error processing ingredient {ingredient_name}: {e}")
            cart_items.append({
                'main': {
                    'id': 0,
                    'name': f"{ingredient_name} (Error finding product)",
                    'image': '',
                    'quantity': ingredient_quantity,
                    'price': 'Not available'
                },
                'alternatives': [],
                'original_ingredient': {
                    'name': ingredient_name,
                    'quantity': ingredient_quantity
                }
            })
    
    return cart_items