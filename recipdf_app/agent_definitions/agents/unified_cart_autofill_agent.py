# UnifiedCartAutofillAgent refactor with caching, token tracking, and quota-aware fallback
import asyncio
import copy
import json
import yaml
import hashlib
import os
from functools import lru_cache

from recipdf_app.agent_definitions.agent_superclass import Agent
from recipdf_app.recipe_processing import select_file_and_extract_text
from recipdf_app.walmart_affiliate_api_utils import WalmartAPI, filter_walmart_search_result_props

#create output_shopping_list_tool_def, retry_product_search_tool_def, select_best_item_tool_def
output_shopping_list_tool_def = {
    "type": "function",
    "function": {
        "name": "output_shopping_list",
        "description": "Output a shopping list for all of the ingredients in the recipe provided in the prompt.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "shoppingList": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "ingredient": {
                                "type": "string",
                                "description": "Ingredient, restated from the recipe."
                            },
                            "prep_work_reasoning": {
                                "type": "string",
                                "description": "Brief note on any prep work this ingredient requires."
                            },
                            "product": {
                                "type": "string",
                                "description": "Search term for the store product to purchase. Omit adjectives related to prep work."
                            },
                            "quantity": {
                                "type": "string",
                                "description": "Quantity of the product. Include units if applicable."
                            },
                        },
                        "required": ["ingredient", "prep_work_reasoning", "product", "quantity"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["shoppingList"],
            "additionalProperties": False
        }
    }
}
retry_product_search_tool_def = {
    "type": "function",
    "function": {
        "name": "retry_product_search",
        "description": "Output a search term for an ingredient that didn't yield usable search results the first time.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "ingredient": {
                    "type": "string",
                    "description": "A single ingredient, quoted from the recipe."
                },
                "product": {
                    "type": "string",
                    "description": "Search term for what *product* one would need to buy from the store to get this ingredient. Omit adjectives related to prep work"
                },
                "quantity": {
                    "type": "string",
                    "description": "Quantity of the product. Include units if applicable."
                },
            },
            "required": ["ingredient", "product", "quantity"],
            "additionalProperties": False
        }
    }
}
select_best_item_tool_def = {
    "type": "function",
    "function": {
        "name": "select_best_item",
        "description": "Output the product that best matches the corresponding ingredient in the recipe.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "rationale": {
                    "type": "string",
                    "description": "Brief 1-2 sentence rationale for selecting this product and its quantity."
                },
                "itemId": {
                    "type": "integer",
                    "description": "'itemId' of the selected product."
                },
                "quantity": {
                    "type": "integer",
                    "description": "Quantity to order of the selected product."
                }
            },
            "required": ["rationale", "itemId", "quantity"],
            "additionalProperties": False
        }
    }
}
TOKEN_LIMIT = 100000  # adjustable threshold (in tokens)
MOCK_ITEMS = [
    {"name": "Mock Flour", "itemId": 111, "price": 1.99},
    {"name": "Mock Sugar", "itemId": 112, "price": 2.99}
]
class UnifiedCartAutofillAgent(Agent):
    def __init__(self, llm='gpt-4o-mini', llm_api_provider='openai', max_retries=1):
        system_prompt = "You are an agent in charge of finding items from an online shopping website to put in the user's cart based on a recipe."
        super().__init__(llm=llm, llm_api_provider=llm_api_provider, system_prompt=system_prompt)
        self.walmart_api_wrapper = WalmartAPI(
            consumer_id=os.getenv("WALMART_CONSUMER_ID"), # need to add consumer_id
            key_version="1",
            key_file_path=os.path.expanduser(os.getenv("WALMART_RSA_KEY_PATH")) # need to add RSA key_file_path
        )
        # Set the maximum retries for a single shopping list item.
        self.max_retries = max_retries
        self.ingredient_extraction_context = []
        self.token_usage = 0
        self.reset()

    def reset(self):
        self.ingredient_extraction_context = []
        self.token_usage = 0
        self.reset_context()

    def _track_tokens(self, completion):
        used = getattr(getattr(completion, 'usage', None), 'total_tokens', 0)
        self.token_usage += used
        print(f"[Token usage] +{used} tokens | Total: {self.token_usage}")

    def _should_fallback_to_mock(self):
        return self.token_usage >= TOKEN_LIMIT

    def _make_hash(self, recipe):
        return hashlib.md5(recipe.encode()).hexdigest()

    @lru_cache(maxsize=32)
    def cached_shopping_list(self, recipe_hash):
        return self._extract_shopping_list_from_recipe_uncached(recipe_hash)

    def extract_shopping_list_from_recipe(self, recipe, batch_size="1"):
        if self._should_fallback_to_mock():
            print("[Fallback] Returning mock shopping list due to quota.")
            return [{"ingredient": "flour", "quantity": "1 cup", "product": "flour", "prep_work_reasoning": ""}]
        return self._extract_shopping_list_from_recipe_uncached(recipe, batch_size)

    def _extract_shopping_list_from_recipe_uncached(self, recipe, batch_size="1"):
        prompt = f"Extract ingredients for {batch_size} batches:\n<recipe>{recipe}</recipe>"
        context = [self.system_message, {'role': 'user', 'content': prompt}]
        response = self.llm_api_wrapper.query(
            model=self.model,
            context=context,
            temperature=0.0,
            tools=[output_shopping_list_tool_def],
            tool_choice='required',
            parallel_tool_calls=False,
        )
        self._track_tokens(response)
        tool_call = self.llm_api_wrapper.get_tool_calls(response)[0]
        return self.llm_api_wrapper.get_arguments_from_tool_call(tool_call).get('shoppingList')

    async def get_cart_from_recipe(self, recipe, batch_size="1", verbose=False):
        if self._should_fallback_to_mock():
            return {
                "url": "https://www.walmart.com/cart?mock=true",
                "items": MOCK_ITEMS,
                "summary": "Quota exceeded. Returned mock items."
            }
        shopping_list = self.extract_shopping_list_from_recipe(recipe, batch_size)
        return await self.get_cart_from_shopping_list(shopping_list, verbose=verbose, bypass_retry=True)

    async def get_cart_from_shopping_list(self, shopping_list, initial_agent_context=None, verbose=False, bypass_retry=True):
        if self._should_fallback_to_mock():
            return {
                "url": "https://www.walmart.com/cart?mock=true",
                "items": MOCK_ITEMS,
                "summary": "Quota exceeded. Returned mock items."
            }

        context = initial_agent_context or []
        context_threads = [copy.deepcopy(context) for _ in shopping_list]

        tasks = [
            self.process_shopping_list_item(item, context_threads[i], verbose, 0, bypass_retry)
            for i, item in enumerate(shopping_list)
        ]
        results = await asyncio.gather(*tasks)
        valid_items = [item for item in results if item.get("quantity", 0) > 0]

        cart_url = self.walmart_api_wrapper.generate_walmart_cart_url(valid_items)

        return {
            "url": cart_url,
            "items": valid_items,
            "summary": f"{len(valid_items)} items added to cart."
        }

    async def process_shopping_list_item(self, item_data, context, verbose, retry_count, bypass_retry):
        if self._should_fallback_to_mock():
            return {"itemId": 0, "quantity": 0, "rationale": "Quota exceeded"}

        product_term = item_data["product"]
        search_results_str = await asyncio.to_thread(
            self.walmart_api_wrapper.get_walmart_search_results, product_term
        )
        # ✅ Debug type
        print("DEBUG type(search_results_str):", type(search_results_str))
        try:
            search_results = json.loads(search_results_str) if isinstance(search_results_str, str) else search_results_str
        except Exception as e:
            print("Error decoding search results:", e)
            raise

        products = search_results.get('items', [])
        print("DEBUG products[0]:", products[0] if products else "None")

        #products = json.loads(search_results_str).get('items', [])

        if not products:
            if bypass_retry or retry_count >= self.max_retries:
                return {"itemId": 0, "quantity": 0}
            return await self.retry_product_selection(context, retry_count + 1)

        return await asyncio.to_thread(
            self.select_product, products, item_data["product"], item_data["quantity"], context, verbose, retry_count, bypass_retry
        )

    def select_product(self, products, item_name, quantity, context, verbose, retry_count, bypass_retry):
        # Defensive decode
        if isinstance(products, str):
            try:
                products = json.loads(products)
            except Exception as e:
                raise ValueError(f"Failed to decode products JSON string: {e}")
        if not isinstance(products, list):
            raise TypeError(f"Expected list of dicts for 'products', got {type(products)} with contents: {products}")

        if not all(isinstance(p, dict) for p in products):
            raise TypeError("Each product must be a dictionary")
        filtered = filter_walmart_search_result_props(products[:3])
        prompt = f"Select best product for: {item_name}\nOptions:\n{yaml.dump(filtered)}"
        context.append({"role": "user", "content": prompt})

        response = self.llm_api_wrapper.query(
            model=self.model,
            context=context,
            temperature=0.0,
            tools=[select_best_item_tool_def],
            tool_choice='required',
            parallel_tool_calls=False,
        )
        self._track_tokens(response)

        tool_call = self.llm_api_wrapper.get_tool_calls(response)[0]
        return self.llm_api_wrapper.get_arguments_from_tool_call(tool_call)

    async def retry_product_selection(self, context, retry_count):
        response = self.llm_api_wrapper.query(
            model=self.model,
            context=context,
            temperature=0.0,
            tools=[retry_product_search_tool_def],
            tool_choice='required',
            parallel_tool_calls=False,
        )
        self._track_tokens(response)

        tool_call = self.llm_api_wrapper.get_tool_calls(response)[0]
        args = self.llm_api_wrapper.get_arguments_from_tool_call(tool_call)
        return await self.process_shopping_list_item(args, context, False, retry_count)


if __name__ == "__main__":
    agent = UnifiedCartAutofillAgent()
    recipe = select_file_and_extract_text(verbose=True)
    result = asyncio.run(agent.get_cart_from_recipe(recipe, verbose=True))
    print(f"Cart URL: {result['url']}")
    # Expected Output: Generated Walmart Cart URL: https://www.walmart.com/cart?items=...