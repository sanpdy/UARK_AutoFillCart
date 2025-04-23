import json
from agent_definitions.agent_superclass import Agent

# Tool definition for outputting the final ingredient list
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
                                "description": "A single ingredient from the recipe. Omit adjectives related to prep work such as cutting, marinating, and withholding parts of the ingredient."
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

class RecipeChatAgent(Agent):
    def __init__(self, llm='gpt-4o-mini', llm_api_provider='openai'):
        system_prompt = """You are a helpful shopping assistant for recipes. Your goal is to understand exactly what recipe the user wants to make, how many servings they need, and any dietary preferences or restrictions they have.

        Follow these steps:
        1. First, identify the recipe the user wants to make. If it's unclear, ask for clarification.
        2. Determine how many servings they want to prepare. Default to 4 servings if not specified.
        3. Ask about any dietary restrictions or preferences (e.g., gluten-free, vegetarian, etc.)
        4. When you have all the necessary information, extract the ingredients needed for the recipe, adjusting quantities based on the desired number of servings.
        5. For each ingredient, list it in a simple format without preparation instructions (e.g., use "chicken thighs" not "chicken thighs, deboned and diced").
        6. Slightly overestimate quantities to ensure the user has enough ingredients.

        Present all ingredient information in a clear, structured way for adding to a shopping list.

        Important: When listing ingredients, use a dash (-) before each item and include quantities. For example:
        - All-purpose flour - 2 cups
        - Sugar - 1 cup
        - Butter - 1/2 cup"""
        
        super().__init__(llm=llm, llm_api_provider=llm_api_provider, system_prompt=system_prompt)
        self.reset()
        self.recipe_name = None
        self.servings = None
        self.dietary_preferences = []
        self.conversation_complete = False
        self.extracted_ingredients = None
        self.frontend_detected_ingredients = False
        self.cart_items = []  
        self.last_response_data = {}  

    def reset(self):
        self.reset_context()
        self.recipe_name = None
        self.servings = None
        self.dietary_preferences = []
        self.conversation_complete = False
        self.extracted_ingredients = None
        self.frontend_detected_ingredients = False
        self.cart_items = []  
        self.last_response_data = {}  

    def process_chat_message(self, user_message, frontend_ingredients=None, force_complete=False):
        """
        Process a user message in the chat, ask clarifying questions if needed,
        and progress the conversation toward extracting the complete recipe ingredients.
        """
        if frontend_ingredients:
            self.frontend_detected_ingredients = True
            self.extracted_ingredients = frontend_ingredients
        
        if force_complete:
            self.conversation_complete = True
        
        self.context.append({
            'role': 'user',
            'content': user_message
        })
        
        response_message = self.llm_api_wrapper.query(
            model=self.model,
            context=self.context,
            temperature=0.6,
        )
        
        # Add the assistant's response to the context
        self.context.append(response_message)
        
        # Extract the assistant's message content
        # Handle both dictionary and object responses
        assistant_message = ""
        if hasattr(response_message, 'content'):
            assistant_message = response_message.content
        elif isinstance(response_message, dict) and 'content' in response_message:
            assistant_message = response_message['content']
        
        # Check for ingredient list format in the message
        if not self.extracted_ingredients and self._contains_ingredient_list(assistant_message):
            self.extracted_ingredients = self._extract_ingredients_from_message(assistant_message)
            if self.extracted_ingredients and len(self.extracted_ingredients) >= 3:
                self.conversation_complete = True
        
        self._update_conversation_state()
        
        if self._has_sufficient_information() and not self.conversation_complete:
            # Extract the final ingredients using the LLM
            if not self.extracted_ingredients:
                self.extracted_ingredients = self._extract_final_ingredients()
            self.conversation_complete = True
        
        # Return based on conversation state
        if self.conversation_complete:
            response_data = {
                'message': assistant_message,
                'conversation_complete': True,
                'ingredients': self.extracted_ingredients
            }
            self.last_response_data = response_data  # Store the response data
            return response_data
        else:
            response_data = {
                'message': assistant_message,
                'conversation_complete': False,
                'recipe_name': self.recipe_name,
                'servings': self.servings,
                'dietary_preferences': self.dietary_preferences
            }
            self.last_response_data = response_data  # Store the response data
            return response_data
    
    def _contains_ingredient_list(self, message):
        """
        Check if the message contains a formatted list of ingredients.
        """
        lines = message.split('\n')
        ingredient_line_count = 0
        
        for line in lines:
            line = line.strip()
            if line.startswith('-') and ' - ' in line:
                ingredient_line_count += 1
            elif (line.startswith('1.') or line.startswith('2.') or line.startswith('3.')) and \
                 any(unit in line.lower() for unit in ['cup', 'tbsp', 'tsp', 'tablespoon', 'teaspoon', 
                                                      'ounce', 'oz', 'pound', 'lb', 'gram']):
                ingredient_line_count += 1
        
        return ingredient_line_count >= 3
    
    def _extract_ingredients_from_message(self, message):
        """
        Extract ingredients directly from a message containing a list.
        """
        lines = message.split('\n')
        ingredients = []
        
        for line in lines:
            line = line.strip()
            
            if not line or line.startswith('#') or line.startswith('For the') or line.startswith('Here'):
                continue
                
            if line.startswith('-') and ' - ' in line:
                # Remove the leading dash
                line = line[1:].strip()
                parts = line.split(' - ')
                
                if len(parts) >= 2:
                    ingredient = parts[0].strip()
                    quantity = parts[1].strip()
                    
                    # Add to ingredients list if valid
                    if ingredient and len(ingredient) > 2:
                        ingredients.append({
                            'ingredient': ingredient,
                            'quantity': quantity
                        })
            
            elif (line.startswith('1.') or line.startswith('2.') or line.startswith('3.')) and \
                 any(unit in line.lower() for unit in ['cup', 'tbsp', 'tsp', 'tablespoon', 'teaspoon', 
                                                      'ounce', 'oz', 'pound', 'lb', 'gram']):
                line = line.split('.', 1)[1].strip()
                
                if ' - ' in line:
                    parts = line.split(' - ')
                    ingredient = parts[0].strip()
                    quantity = parts[1].strip()
                else:
                    #quantity_pattern = r'(\d+(\.\d+)?\s*(cup|cups|tablespoon|tbsp|tsp|teaspoon|oz|ounce|pound|lb|g|gram|kg|ml|liter|l)s?)'
                    
                    ingredient = line
                    quantity = "as needed"  # Default
                
                # Add to ingredients list if valid
                if ingredient and len(ingredient) > 2:
                    ingredients.append({
                        'ingredient': ingredient,
                        'quantity': quantity
                    })
        
        return ingredients if len(ingredients) >= 3 else None
    
    def _update_conversation_state(self):
        """
        Analyze the conversation to extract recipe name, servings, and dietary preferences.
        This is done by sending a special query to the LLM to analyze the conversation so far.
        """
        if self.recipe_name and self.servings and self.dietary_preferences:
            return
            
        # Create a special query to extract information
        analysis_prompt = """Based on the conversation so far, please extract the following information:
            1. Recipe name (if identified)
            2. Number of servings (if specified)
            3. Dietary preferences or restrictions (if any)

            Format your response as a JSON object with these keys: recipe_name, servings, dietary_preferences.
            If any information is not available, use null for that field."""

        analysis_context = self.context.copy()
        analysis_context.append({
            'role': 'user',
            'content': analysis_prompt
        })
        
        # Query the LLM for analysis
        analysis_response = self.llm_api_wrapper.query(
            model=self.model,
            context=analysis_context,
            temperature=0.0,
        )
        
        try:
            # Extract just the JSON part from the response
            content = ""
            if hasattr(analysis_response, 'content'):
                content = analysis_response.content
            elif isinstance(analysis_response, dict) and 'content' in analysis_response:
                content = analysis_response['content']
            
            # Find JSON block if it exists
            json_match = content
            if '```json' in content:
                json_match = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                json_match = content.split('```')[1].split('```')[0].strip()
            
            analysis = json.loads(json_match)
            
            if analysis.get('recipe_name'):
                self.recipe_name = analysis.get('recipe_name')
            if analysis.get('servings'):
                self.servings = analysis.get('servings')
            if analysis.get('dietary_preferences'):
                self.dietary_preferences = analysis.get('dietary_preferences')
        except Exception as e:
            print(f"Error parsing analysis response: {e}")
            pass
    
    def _has_sufficient_information(self):
        """
        Check if we have enough information to extract the ingredients.
        """
        #If frontend has detected ingredients, we have enough info
        if self.frontend_detected_ingredients:
            return True
            
        #If we already have extracted ingredients, we have enough info
        if self.extracted_ingredients:
            return True
        
        #We need at least the recipe name
        if not self.recipe_name:
            return False
        
        if len(self.context) >= 3:
            last_assistant_message = None
            for msg in reversed(self.context):
                if (hasattr(msg, 'role') and msg.role == 'assistant') or \
                   (isinstance(msg, dict) and msg.get('role') == 'assistant'):
                    content = msg.content if hasattr(msg, 'content') else msg.get('content', '')
                    last_assistant_message = content
                    break
            
            # we might have enough information
            if last_assistant_message:
                if self._contains_ingredient_list(last_assistant_message):
                    return True
                
                confirmation_phrases = [
                    "here's what I understand",
                    "based on our conversation",
                    "to summarize",
                    "shall I proceed",
                    "would you like me to",
                    "ready to extract",
                    "I'll now extract",
                    "I'll create a shopping list"
                ]
                
                if any(phrase in last_assistant_message.lower() for phrase in confirmation_phrases):
                    for msg in reversed(self.context):
                        role = msg.role if hasattr(msg, 'role') else msg.get('role', '')
                        if role == 'user':
                            content = msg.content if hasattr(msg, 'content') else msg.get('content', '')
                            user_response = content.lower()
                            
                            confirmation_words = ["yes", "sure", "okay", "ok", "please do", "go ahead", "sounds good", "correct"]
                            if any(word in user_response for word in confirmation_words):
                                return True
                            break
        
        # Reduced the threshold from 8 to 6 (3 exchanges) ---- 3 changes
        if len(self.context) >= 66:
            return True
        
        return False
    
    def _extract_final_ingredients(self):
        """
        Extract the final list of ingredients based on the conversation.
        This uses the output_ingredients tool to ensure proper formatting.
        """
        if self.extracted_ingredients:
            return self.extracted_ingredients
            
        extraction_prompt = f"""Based on our conversation, please extract all the ingredients needed for {self.recipe_name or 'the recipe'}.
        
        Servings: {self.servings or 4}
        Dietary preferences: {', '.join(self.dietary_preferences) if self.dietary_preferences else 'None specified'}

        For each ingredient:
        1. List only the ingredient name without preparation instructions
        2. Include the quantity (slightly overestimated to ensure enough)
        3. Adjust quantities based on the number of servings

        Use the output_ingredients tool to format the response correctly."""

        extraction_context = self.context.copy()
        extraction_context.append({
            'role': 'user',
            'content': extraction_prompt
        })
        
        response_message = self.llm_api_wrapper.query(
            model=self.model,
            context=extraction_context,
            temperature=0.0,
            tools=[output_ingredients_tool_def],
            tool_choice='required',
            parallel_tool_calls=False,
        )
        
        tool_calls = self.llm_api_wrapper.get_tool_calls(response_message)
        if not tool_calls:
            raise Exception("No tool call received from LLM query to extract ingredients")
        
        tool_call = next(iter(tool_calls))
        tool_call_name = self.llm_api_wrapper.get_name_from_tool_call(tool_call)
        tool_call_args = self.llm_api_wrapper.get_arguments_from_tool_call(tool_call)
        
        if tool_call_name == self.llm_api_wrapper.get_tool_name_from_definition(output_ingredients_tool_def):
            ingredients = tool_call_args.get('ingredients')
            return ingredients
        else:
            raise Exception(f"Unexpected tool call name: {tool_call_name}")
    
    def set_cart_items(self, cart_items):
        """
        Store cart items on the agent for later retrieval.
        """
        self.cart_items = cart_items
        # Also store in last response data
        if not hasattr(self, 'last_response_data'):
            self.last_response_data = {}
        self.last_response_data['cart_items'] = cart_items
    
    def get_cart_items(self):
        if hasattr(self, 'cart_items') and self.cart_items:
            return self.cart_items
        
        # Try to get from last response data
        if hasattr(self, 'last_response_data') and 'cart_items' in self.last_response_data:
            return self.last_response_data['cart_items']
        
        return []
    
    def chat_until_ingredients(self, initial_message):
        """
        Continue the conversation until we have enough information to extract ingredients.
        This is a simplified version for demonstration - in a real extension, this would
        integrate with the chat UI.
        """
        response = self.process_chat_message(initial_message)
        
        print(f"Assistant: {response['message']}")
        
        while not response.get('conversation_complete', False):
            user_input = input("User: ")
            
            response = self.process_chat_message(user_input)
            print(f"Assistant: {response['message']}")
        
        return response.get('ingredients', [])