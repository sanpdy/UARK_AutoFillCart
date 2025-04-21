import asyncio
from recipe_processing import select_file_and_extract_text
from agent_definitions.agents.unified_cart_autofill_agent import UnifiedCartAutofillAgent

def main():
    agent = UnifiedCartAutofillAgent()
    example_recipe = select_file_and_extract_text(verbose=True)
    example_cart_url = asyncio.run(agent.get_cart_from_recipe(example_recipe, verbose=False))
    print(f"Generated Walmart Cart URL: {example_cart_url}")
    # Expected Output: Generated Walmart Cart URL: https://www.walmart.com/cart?items=...

if __name__ == "__main__":
    main()