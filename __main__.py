import asyncio

from recipe_processing import select_file_and_extract_text
from agent_definitions.agents.unified_cart_autofill_agent import UnifiedCartAutofillAgent

if __name__ == "__main__":
    agent = UnifiedCartAutofillAgent()
    example_recipe = select_file_and_extract_text(verbose=True)
    example_cart = asyncio.run(agent.get_cart_from_recipe(example_recipe, verbose=False))
    example_cart_url = agent.walmart_api_wrapper.generate_walmart_cart_url(example_cart)
    print(f"Generated Walmart Cart URL: {example_cart_url}")
    # Expected Output: Generated Walmart Cart URL: https://www.walmart.com/cart?items=...
