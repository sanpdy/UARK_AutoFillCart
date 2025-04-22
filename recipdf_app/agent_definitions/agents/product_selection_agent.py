import yaml
from pydantic import BaseModel, Field

from recipdf_app.agent_definitions.agent_superclass import Agent
from recipdf_app.agent_definitions.agent_utilities import user_prompt_to_message
from recipdf_app.walmart_affiliate_api_utils import filter_walmart_search_result_props


output_best_item_tool_def = {
    "type": "function",
    "function": {
        "name": "output_best_item",
        "description": "Output the best product selection for the ingredient provided in the prompt.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "rationale": {
                    "type": "string",
                    "description": "The rationale for selecting this product."
                },
                "itemId": {
                    "type": "integer",
                    "description": "The Walmart item ID of the selected product."
                },
                "quantity": {
                    "type": "integer",
                    "description": "The quantity to order of the selected product."
                }
            },
            "required": ["rationale", "itemId", "quantity"],
            "additionalProperties": False
        }
    }
}


class ProductSelection(BaseModel):
    rationale: str
    itemId: int


class ProductSelectionAgent(Agent):
    def __init__(self, llm='gpt-4o-mini', llm_api_provider='openai'):
        system_prompt = "You are a product selection agent. Your task is to choose the product from the list of Walmart search results that best matches the ingredient description."
        super().__init__(llm=llm, llm_api_provider=llm_api_provider, system_prompt=system_prompt)
        self.response_format = ProductSelection
        self.reset()

    def reset(self):
        self.reset_context()

    def select_product(self, products, ingredient_name, ingredient_quantity, verbose=False):
        itemIds = [
            product.get("itemId")
            for product in products
            if isinstance(product, dict) and "itemId" in product
        ] # product.get('itemId') for product in products if 'itemId' in product]
        if not isinstance(products, list) or not all(isinstance(p, dict) for p in products):
            raise TypeError(f"[ProductSelectionAgent] Expected list of dicts, got: {type(products)} | Sample: {products[:1]}")
        
        products_filtered_props = filter_walmart_search_result_props(products)
        products_str = yaml.dump(products_filtered_props, sort_keys=False)
        # products_str = json.dumps(products_filtered_props, indent=4)

        if verbose:
            print(products_str)

        prompt = (f"Ingredient: {ingredient_name}\n"
                  f"Quantity: {ingredient_quantity}\n"
                  f"\n"
                  f"Please select the best product from the list below that matches the ingredient description. "
                  f"{products_str}\n")

        user_message = user_prompt_to_message(prompt, api_provider=self.llm_api_provider)
        self.context.append(user_message)
        response_message = self.llm_api_wrapper.query(
            model=self.model,
            context=self.context,
            temperature=0.0,
            tools=[output_best_item_tool_def],
            tool_choice='required',
            parallel_tool_calls=False
        )

        # Check if the response is valid
        tool_calls = self.llm_api_wrapper.get_tool_calls(response_message)
        if not tool_calls:
            raise Exception("No tool call received from LLM query to retrieve screenshot")

        # Run the tool call and add screenshots to context
        tool_call = next(iter(tool_calls))
        tool_call_name = self.llm_api_wrapper.get_name_from_tool_call(tool_call)
        tool_call_args = self.llm_api_wrapper.get_arguments_from_tool_call(tool_call)
        if tool_call_name == self.llm_api_wrapper.get_tool_name_from_definition(output_best_item_tool_def):
            # Take the screenshots and add them to agent context
            itemId = tool_call_args.get('itemId')
            quantity = tool_call_args.get('quantity')
            if itemId not in itemIds:
                ...
            if quantity < 1:
                ...
            return tool_call_args
        else:
            raise Exception(f"Unexpected tool call name: {tool_call_name}")
