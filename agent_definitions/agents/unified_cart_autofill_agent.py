import asyncio
import copy
import json
import yaml

from agent_definitions.agent_superclass import Agent
from recipe_processing import select_file_and_extract_text
from walmart_affiliate_api_utils import WalmartAPI, filter_walmart_search_result_props

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


class UnifiedCartAutofillAgent(Agent):
    def __init__(self, llm='gpt-4o-mini', llm_api_provider='openai', max_retries=1):
        system_prompt = "You are an agent in charge of finding items from an online shopping website to put in the user's cart based on a recipe."
        super().__init__(llm=llm, llm_api_provider=llm_api_provider, system_prompt=system_prompt)
        self.walmart_api_wrapper = WalmartAPI(
            consumer_id="fe944cf5-2cd6-4664-8d8a-1a6e0882d722",
            key_version="1",
            key_file_path=r"C:\Users\Stephen Pierson\.ssh\rsa_key_20250410_v2"
        )
        # Set the maximum retries for a single shopping list item.
        self.max_retries = max_retries
        self.ingredient_extraction_context = None
        self.reset()

    def reset(self):
        self.ingredient_extraction_context = []
        self.reset_context()

    async def get_cart_from_recipe(self, recipe: str, batch_size: str = "1", verbose=False):
        shopping_list = self.extract_shopping_list_from_recipe(recipe, batch_size)
        # Example shopping list:
        #  [{"ingredient": "flour", "prep_work_reasoning": "None required", "product": "all-purpose flour", "quantity": "1 cup"}, ...]
        print(f"Shopping List ({len(shopping_list)} items):\n"
              f"{json.dumps(shopping_list, indent=2)}\n")
        return await self.get_cart_from_shopping_list(
            shopping_list,
            initial_agent_context=self.ingredient_extraction_context,
            verbose=verbose,
            bypass_retry=True
        )

    async def get_cart_from_shopping_list(self, shopping_list: list, initial_agent_context=None, bypass_retry=True, verbose=False):
        """
        Generate an online cart URL from a shopping list.

        This function processes a shopping list of items, retrieves product details
        from the Walmart API, and generates a cart URL for the selected products.

        Parameters:
            shopping_list (list): A list of dictionaries, where each dictionary contains
                details about a product to search for (e.g., 'product' and 'quantity').

                Expected schema:
                    [
                        {
                            "product": "flour",
                            "quantity": "1 cup"
                        },
                        ...
                    ]

            initial_agent_context (list, optional): The initial context for the agent,
                used to maintain conversation state. Defaults to an empty list.
            verbose (bool, optional): Whether to print detailed logs for debugging.
                Defaults to False.
            bypass_retry (bool, optional): If True, do not retry on failures and instead
                warn the user and skip the item. Defaults to True.

        Returns:
            str: A cart URL containing the selected products.
        """
        if not initial_agent_context:
            initial_agent_context = []
        branching_context_threads = [copy.deepcopy(initial_agent_context) for _ in shopping_list]
        tasks = [
            self.process_shopping_list_item(item_data,
                                            context_thread=branching_context_threads[i],
                                            verbose=verbose,
                                            retry_count=0,
                                            bypass_retry=bypass_retry)
            for i, item_data in enumerate(shopping_list)
        ]
        # Gather results from processing each shopping list item.
        items = await asyncio.gather(*tasks)

        print("Proposed Cart:")
        for item in items:
            print(json.dumps(item, sort_keys=False))
        print()

        # Identify and print out items that have quantity == 0, and filter them out from the proposed cart
        skipped_item_names = []
        cart = []
        for idx, result in enumerate(items):
            if result.get("quantity", 0) == 0:
                # Use the ingredient name from the original shopping list for reporting.
                skipped_item_names.append(shopping_list[idx].get("product", "Unknown"))
            else:
                cart.append(result)

        if skipped_item_names:
            print("The following items were skipped due to being unable to find a matching product:")
            for name in skipped_item_names:
                print(f"- {name}")
            print()

        return cart

    def extract_shopping_list_from_recipe(self, recipe: str, batch_size: str = "1"):
        # Example Output:
        #  [{"ingredient": "flour", "prep_work_reasoning": "None required", "product": "all-purpose flour", "quantity": "1 cup"}, ...]
        recipe_message_content = (
            f"Extract the ingredients from the following recipe, phrasing them as search terms for a shopping website "
            f"likely to yield relevant results. The user wants to make {batch_size} batches:" 
            f"\n\n<recipe>\n{recipe}\n</recipe>")
        context = [self.system_message, {'role': 'user', 'content': recipe_message_content}]
        response_message = self.llm_api_wrapper.query(
            model=self.model,
            context=context,
            temperature=0.0,
            tools=[output_shopping_list_tool_def],
            tool_choice='required',
            parallel_tool_calls=False,
        )
        context.append(response_message)
        tool_calls = self.llm_api_wrapper.get_tool_calls(response_message)
        if not tool_calls:
            raise Exception("No tool call received from LLM query to retrieve shopping list")
        tool_call = next(iter(tool_calls))
        tool_call_id = tool_call.id
        tool_call_name = self.llm_api_wrapper.get_name_from_tool_call(tool_call)
        tool_call_args = self.llm_api_wrapper.get_arguments_from_tool_call(tool_call)
        if tool_call_name == self.llm_api_wrapper.get_tool_name_from_definition(output_shopping_list_tool_def):
            shoppingList = tool_call_args.get('shoppingList')
            tool_message = self.llm_api_wrapper.create_tool_response_message(
                tool_call_id=tool_call_id,
                function_name=tool_call_name,
                function_response="Ingredients parsed successfully."
            )
            context.append(tool_message)
            self.ingredient_extraction_context = context
            return shoppingList
        else:
            raise Exception(f"Unexpected tool call name: {tool_call_name}")

    async def process_shopping_list_item(self, item_search_data, context_thread, verbose=False, retry_count=0, bypass_retry=True):
        """Process a single ingredient asynchronously."""
        product_search_term = item_search_data.get("product")
        quantity = item_search_data.get("quantity")
        search_results_str = await asyncio.to_thread(self.walmart_api_wrapper.get_walmart_search_results,
                                                     product_search_term)
        search_results = json.loads(search_results_str)
        products = search_results.get('items', [])
        if not products:
            if bypass_retry:
                if verbose:
                    print(f"No products found for search term '{product_search_term}'. Bypassing retry and skipping item.\n")
                return {'rationale': f"Failed to retrieve products for {product_search_term} - skipping due to bypass retry setting.",
                        'itemId': 0, 'quantity': 0}
            if retry_count >= self.max_retries:
                if verbose:
                    print(f"Maximum retries ({self.max_retries}) exceeded for search term '{product_search_term}'. Skipping this item.\n")
                return {'rationale': f'Failed to retrieve products for {product_search_term} after {retry_count} attempts.',
                        'itemId': 0, 'quantity': 0}
            if verbose:
                print(f"No products found for search term '{product_search_term}'. Retrying product search. Retry count: {retry_count + 1}")
            return await self.retry_product_selection(context_thread, retry_count=retry_count + 1)

        # Pass the bypass flag along to select_product.
        selected_product = await asyncio.to_thread(
            self.select_product,
            products,
            product_search_term,
            quantity,
            context_thread,
            bypass_retry,
            retry_count,
            verbose,
        )
        return selected_product

    def select_product(self, available_products, item_name, item_quantity, context, bypass_retry=True, retry_count=0, verbose=False):
        itemIds = [product.get('itemId') for product in available_products if 'itemId' in product]
        products_filtered_props = filter_walmart_search_result_props(available_products)
        products_str = yaml.dump(products_filtered_props, sort_keys=False)
        if verbose:
            print(f"Products found for \"{item_name}\":\n{products_str}")
        prompt = (f"Requested item: {item_name}\n"
                  f"Quantity: {item_quantity}\n\n"
                  f"Please select the product from the list below that best matches the requested item description. "
                  f"{products_str}\n")
        user_message = {"role": "user", "content": prompt}
        context.append(user_message)
        response_message = self.llm_api_wrapper.query(
            model=self.model,
            context=context,
            temperature=0.0,
            tools=[select_best_item_tool_def],
            tool_choice='required',
            parallel_tool_calls=False
        )
        context.append(response_message)
        tool_calls = self.llm_api_wrapper.get_tool_calls(response_message)
        if not tool_calls:
            raise Exception("No tool call received from LLM query to select the best product")
        tool_call = next(iter(tool_calls))
        tool_call_id = tool_call.id
        tool_call_name = self.llm_api_wrapper.get_name_from_tool_call(tool_call)
        tool_call_args = self.llm_api_wrapper.get_arguments_from_tool_call(tool_call)
        if tool_call_name == self.llm_api_wrapper.get_tool_name_from_definition(select_best_item_tool_def):
            itemId = tool_call_args.get('itemId')
            product_quantity = tool_call_args.get('quantity')
            rationale = tool_call_args.get('rationale')
            # Check for invalid selections.
            retry_flag = False
            retry_reason = ""
            if itemId not in itemIds:
                tool_call_response_content = f"Product selection failed: itemId \"{itemId}\" not a valid selection."
                retry_reason = "invalid_itemId"
                retry_flag = True
            elif product_quantity < 1:
                tool_call_response_content = f"Product selection failed: quantity \"{product_quantity}\" is invalid (cannot be < 1)."
                retry_reason = "invalid_quantity"
                retry_flag = True
            else:
                tool_call_response_content = "Product selection successful."

            tool_message = self.llm_api_wrapper.create_tool_response_message(
                tool_call_id=tool_call_id,
                function_name=tool_call_name,
                function_response=tool_call_response_content
            )
            context.append(tool_message)
            if retry_flag:
                if bypass_retry:
                    if verbose:
                        print(f"Bypassing retry for item '{item_name}' due to bypass flag, skipping this item.\n")
                    return {'itemId': 0, 'quantity': 0, 'seller': 'walmart', 'rationale': f"Product selection for {item_name} skipped due to bypass retry setting."}
                if retry_count >= self.max_retries:
                    if verbose:
                        print(f"Maximum retries ({self.max_retries}) exceeded for item '{item_name}'. Skipping this item.\n")
                    return {'itemId': 0, 'quantity': 0, 'seller': 'walmart', 'rationale': f'Failed to select product for {item_name} after {retry_count} attempts.'}
                if verbose:
                    print(f"Retrying product selection for \"{item_name}\". Reason: {retry_reason}. Retry count: {retry_count+1}")
                selected_product = asyncio.run(self.retry_product_selection(context, retry_count=retry_count+1))
                return selected_product
            else:
                # Return the selected product.
                index = next((i for i, product in enumerate(available_products) if product.get('itemId') == itemId), None)
                return {
                    'itemId': itemId,
                    'quantity': product_quantity,
                    'seller': 'walmart',
                    'rationale': rationale,
                    'item_details': available_products[index] if index is not None else None,
                }
        else:
            raise Exception(f"Unexpected tool call name: {tool_call_name}")

    async def retry_product_selection(self, context, retry_count):
        """Retry product selection with the current context (async version)"""
        response_message = self.llm_api_wrapper.query(
            model=self.model,
            context=context,
            temperature=0.0,
            tools=[retry_product_search_tool_def],
            tool_choice='required',
            parallel_tool_calls=False
        )
        context.append(response_message)
        tool_calls = self.llm_api_wrapper.get_tool_calls(response_message)
        if not tool_calls:
            raise Exception("No tool call received from LLM query to retry product search")
        tool_call = next(iter(tool_calls))
        tool_call_id = tool_call.id
        tool_call_name = self.llm_api_wrapper.get_name_from_tool_call(tool_call)
        tool_call_args = self.llm_api_wrapper.get_arguments_from_tool_call(tool_call)
        if tool_call_name == self.llm_api_wrapper.get_tool_name_from_definition(retry_product_search_tool_def):
            tool_message = self.llm_api_wrapper.create_tool_response_message(
                tool_call_id=tool_call_id,
                function_name=tool_call_name,
                function_response="Product search successful."
            )
            context.append(tool_message)
            return await self.process_shopping_list_item(item_search_data=tool_call_args, context_thread=context,
                                                         verbose=False, retry_count=retry_count)
        else:
            raise Exception(f"Unexpected tool call name: {tool_call_name}")


if __name__ == "__main__":
    agent = UnifiedCartAutofillAgent()
    example_recipe = select_file_and_extract_text(verbose=True)
    example_cart = asyncio.run(agent.get_cart_from_recipe(example_recipe, verbose=False))
    example_cart_url = agent.walmart_api_wrapper.generate_walmart_cart_url(example_cart)
    print(f"Generated Walmart Cart URL: {example_cart_url}")
    # Expected Output: Generated Walmart Cart URL: https://www.walmart.com/cart?items=...
