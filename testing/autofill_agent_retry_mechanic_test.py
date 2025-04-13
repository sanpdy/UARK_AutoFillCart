import asyncio
import json
import unittest

# Import the agent class from your module.
from agent_definitions.agents.unified_cart_autofill_agent import UnifiedCartAutofillAgent

# For demonstration purposes, we assume the UnifiedCartAutofillAgent is defined in the current scope.

# --- Fake wrappers to simulate behavior in tests --- #

class FakeWalmartAPIWrapper:
    def __init__(self):
        self.get_count = 0

    def get_walmart_search_results(self, term):
        """Always return an empty list to force the retry path."""
        self.get_count += 1
        return json.dumps({"items": []})

    def generate_walmart_cart_url(self, items):
        """Return a dummy cart URL."""
        return "https://www.walmart.com/cart?items=dummy"

class DummyToolCall:
    def __init__(self, id, name, args):
        self.id = id
        self.name = name
        self.args = args

class FakeLLMWrapper:
    def query(self, model, context, temperature, tools, tool_choice, parallel_tool_calls):
        """
        Return a dummy response.
        In our tests the actual content is irrelevant because our fake
        walmart API always returns empty products.
        """
        # Return a dummy response (could be any dummy object as long as our other methods work on it).
        return {"dummy_response": True}

    def get_tool_calls(self, response):
        """
        Return a list with a single dummy tool call.
        For the retry tool, we provide a dummy payload that would be passed to
        process_shopping_list_item. The content here is arbitrary.
        """
        dummy_tool = DummyToolCall(
            id="dummy1",
            name="retry_product_search",
            args={"ingredient": "dummy ingredient", "product": "dummy product", "quantity": "1"}
        )
        return [dummy_tool]

    def get_tool_name_from_definition(self, tool_def):
        """Return the tool name as defined in the tool definition."""
        return tool_def["function"]["name"]

    def create_tool_response_message(self, tool_call_id, function_name, function_response):
        """Return a dummy tool response message (dictionary)."""
        return {"tool_call_id": tool_call_id, "function_name": function_name, "function_response": function_response}

    def get_name_from_tool_call(self, tool_call):
        """Return the name of the dummy tool call."""
        return tool_call.name

    def get_arguments_from_tool_call(self, tool_call):
        """Return the arguments of the dummy tool call."""
        return tool_call.args

# --- Unit tests for the retry mechanic --- #

class TestRetryMechanic(unittest.TestCase):
    def setUp(self):
        # Set max_retries to a low value for testing (e.g., 2).
        self.agent = UnifiedCartAutofillAgent(max_retries=2)
        # Override the agent's wrappers with our fake implementations.
        self.agent.walmart_api_wrapper = FakeWalmartAPIWrapper()
        self.agent.llm_api_wrapper = FakeLLMWrapper()

    def test_retry_mechanic_fallback(self):
        """
        Test that when the product search always returns empty results, the agent
        eventually returns a fallback selection after reaching max_retries.
        """
        # Create a fake item search dictionary.
        fake_item = {"product": "dummy product search", "quantity": "1"}
        dummy_context = []  # A simple context list for testing

        # Run process_shopping_list_item asynchronously.
        result = asyncio.run(
            self.agent.process_shopping_list_item(fake_item, dummy_context, verbose=True, retry_count=0)
        )

        # In the fallback, the agent returns itemId=0 and a rationale mentioning failure.
        self.assertEqual(result.get("itemId"), 0)
        self.assertIn("after", result.get("rationale", ""))
        # Verify that the fake Walmart API was queried the expected number of times
        # The expected number is max_retries + 1 (initial attempt plus each retry attempt).
        expected_calls = self.agent.max_retries + 1
        self.assertEqual(self.agent.walmart_api_wrapper.get_count, expected_calls)

    # Optionally, add more tests to simulate a scenario in which one of the retries eventually
    # returns a non-empty product search result. This would require enhancing the fake wrapper
    # to switch its behavior based on the number of calls.

if __name__ == "__main__":
    unittest.main()
