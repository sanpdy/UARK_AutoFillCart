from agent_definitions.agent_superclass import Agent

output_ingredients_tool_def = {
    "type": "function",
    "function": {
        "name": "output_ingredients",
        "description": "Form to output search terms for all of the ingredients in the recipe provided in the prompt.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "ingredients": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "ingredient": {
                                "type": "string",
                                "description": "A single ingredient from the recipe."
                            },
                            "quantity": {
                                "type": "string",
                                "description": "The quantity of the ingredient. Include units if applicable."
                            },
                        },
                        "required": ["ingredient", "quantity"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["ingredients"],
            "additionalProperties": False
        }
    }
}


class IngredientExtractorAgent(Agent):
    def __init__(self, llm='gpt-4o-mini', llm_api_provider='openai'):
        system_prompt = "You are an ingredient extractor agent. Your task is to extract all ingredients from the given text."

        super().__init__(llm=llm, llm_api_provider=llm_api_provider, system_prompt=system_prompt)
        self.reset()

    def reset(self):
        self.reset_context()

    def extract_ingredients_from_recipe(self, recipe: str):
        # Reset the context for each new recipe
        self.reset()

        # Add the text to the context
        self.context.append({
            'role': 'user',
            'content': recipe
        })

        # Generate a response using the LLM
        response_message = self.llm_api_wrapper.query(
            model=self.model,
            context=self.context,
            temperature=0.0,
            tools=[output_ingredients_tool_def],
            tool_choice='required',
            parallel_tool_calls=False,
        )
        # Check if the response is valid
        tool_calls = self.llm_api_wrapper.get_tool_calls(response_message)
        if not tool_calls:
            raise Exception("No tool call received from LLM query to retrieve screenshot")

        # Run the tool call and add screenshots to context
        tool_call = next(iter(tool_calls))
        tool_call_name = self.llm_api_wrapper.get_name_from_tool_call(tool_call)
        tool_call_args = self.llm_api_wrapper.get_arguments_from_tool_call(tool_call)
        if tool_call_name == self.llm_api_wrapper.get_tool_name_from_definition(output_ingredients_tool_def):
            # Take the screenshots and add them to agent context
            ingredients = tool_call_args.get('ingredients')
        else:
            raise Exception(f"Unexpected tool call name: {tool_call_name}")

        return ingredients


if __name__ == "__main__":
    agent = IngredientExtractorAgent()
    recipe = "1 cup of flour, 2 eggs, 1/2 cup of sugar"
    ingredients = agent.extract_ingredients_from_recipe(recipe)
    print(ingredients)  # Output: ['1 cup of flour', '2 eggs', '1/2 cup of sugar']
