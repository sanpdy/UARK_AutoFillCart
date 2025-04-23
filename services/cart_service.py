import logging

logger = logging.getLogger(__name__)

def format_cart_items_for_walmart(cart_items):
    """
    Format cart items for Walmart cart URL generation
    """
    formatted_items = []
    for item in cart_items:
        main_item = item.get('main', {})
        
        item_id = None
        
        if main_item.get('id') and main_item.get('id') != 0:
            item_id = main_item.get('id')
        
        elif main_item.get('itemId') and main_item.get('itemId') != 0:
            item_id = main_item.get('itemId')
            
        elif main_item.get('item_details', {}).get('itemId') and main_item.get('item_details', {}).get('itemId') != 0:
            item_id = main_item.get('item_details', {}).get('itemId')
        
        if item_id and item_id != 0:
            formatted_items.append({
                'itemId': item_id,
                'quantity': 1,
                'seller': 'walmart',
                'item_details': main_item,
                'rationale': f"Selected for {item.get('original_ingredient', {}).get('name', 'recipe')}"
            })
    
    return formatted_items

def create_cart_url(cart_items):
    """
    Create a Walmart cart URL from the items
    """
    formatted_items = format_cart_items_for_walmart(cart_items)
    
    if not formatted_items:
        logger.warning("No valid items to add to cart")
        return None
    
    # Generate cart URL params
    item_params = []
    for item in formatted_items:
        item_id = item.get('itemId')
        if item_id:
            item_params.append(f"items={item_id}:1:walmart")
            logger.debug(f"Added item {item_id} to cart URL")
    
    if not item_params:
        logger.warning("No valid items to add to cart")
        return None
    
    logger.info(f"Creating cart URL with {len(item_params)} valid items")
    return f"https://www.walmart.com/cart?" + "&".join(item_params)

def substitute_product(cart_items, ingredient_index, substitute_index):
    """
    Substitute a product with an alternative
    """
    if ingredient_index < 0 or ingredient_index >= len(cart_items):
        return {
            'success': False,
            'message': f'Invalid ingredient index: {ingredient_index}, max index is {len(cart_items)-1}'
        }
    
    item = cart_items[ingredient_index]
    substitutes = item.get('alternatives', [])
    
    if substitute_index < 0 or substitute_index >= len(substitutes):
        return {
            'success': False,
            'message': f'Invalid substitute index: {substitute_index}, max index is {len(substitutes)-1}'
        }
    
    substitute = substitutes[substitute_index]
    
    #two possible structures i think so handling both in case
    if 'item_details' in substitute:
        substitute_details = substitute['item_details']
        new_main_item = {
            'id': substitute_details.get('itemId'),
            'name': substitute_details.get('name', 'Unknown product'),
            'image': substitute_details.get('image', ''),
            'quantity': item['main']['quantity'],
            'price': substitute_details.get('price', {}).get('priceString', 'Price unavailable'),
            'item_details': substitute_details  # Keep the full details for cart generation
        }
    else:
        new_main_item = {
            'id': substitute.get('id'),
            'name': substitute.get('name', 'Unknown product'),
            'image': substitute.get('image', ''),
            'quantity': item['main']['quantity'],
            'price': substitute.get('price', 'Price unavailable')
        }
    
    cart_items[ingredient_index]['main'] = new_main_item
    logger.info(f"Substitution successful for ingredient {ingredient_index}")
    
    return {
        'success': True,
        'cart_items': cart_items
    }