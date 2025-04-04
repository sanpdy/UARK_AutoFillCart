# modules/walmart_integration.py

from playwright.sync_api import sync_playwright

def search_item_on_walmart(page, item: str) -> bool:
    """
    Searches for an item on Walmart.com.
    Returns True if an item is found and navigated to its detail page.
    """
    try:
        # Fill in the search query; adjust the selector as necessary.
        search_input_selector = "input[aria-label='Search Walmart.com']"
        page.fill(search_input_selector, item)
        page.press(search_input_selector, "Enter")
        page.wait_for_load_state("networkidle", timeout=10000)
        
        # Click the first product link; the selector may need tweaking.
        first_item_selector = "a.product-title-link"
        first_item = page.query_selector(first_item_selector)
        if first_item:
            first_item.click()
            page.wait_for_load_state("networkidle", timeout=10000)
            return True
    except Exception as e:
        print(f"Error searching for '{item}': {e}")
    return False

def add_item_to_cart(page) -> bool:
    """
    Clicks the 'Add to Cart' button on a product detail page.
    Returns True if the button is clicked.
    """
    try:
        # Adjust the selector based on Walmart’s current page design.
        add_button_selector = "button.prod-ProductCTA--primary"
        add_button = page.query_selector(add_button_selector)
        if add_button:
            add_button.click()
            page.wait_for_timeout(2000)  # Wait for any animations or cart updates.
            return True
    except Exception as e:
        print(f"Error adding item to cart: {e}")
    return False

def add_items_to_walmart_cart(items: list) -> dict:
    """
    For each item in the list, search and add it to the Walmart cart.
    Returns a dictionary with item names and a boolean indicating success.
    """
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://www.walmart.com/")
        page.wait_for_load_state("networkidle", timeout=10000)

        for item in items:
            print(f"Processing '{item}'...")
            found = search_item_on_walmart(page, item)
            if found:
                added = add_item_to_cart(page)
                results[item] = added
            else:
                results[item] = False
            page.goto("https://www.walmart.com/")
            page.wait_for_load_state("networkidle", timeout=10000)

        browser.close()
    return results

if __name__ == '__main__':
    test_items = ["eggs", "milk"]
    result = add_items_to_walmart_cart(test_items)
    print("Cart update results:", result)
