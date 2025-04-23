import os
import logging
from agent_definitions.agents.RecipeChatAgent import RecipeChatAgent
from walmart_affiliate_api_utils import WalmartAPI

# Active conversations dictionary - shared across routes
active_conversations = {}

# Initialize WalmartAPI
def get_walmart_api():
    """Initialize and return the Walmart API client"""
    consumer_id = os.environ["CONSUMER_ID"]
    rsa_key = os.environ["RSA_KEY_PATH"]
    return WalmartAPI(
        consumer_id=consumer_id,
        key_version="1",
        key_file_path=rf'{rsa_key}'
    )

# Create a new chat agent
def create_chat_agent():
    """Create a new RecipeChatAgent instance"""
    return RecipeChatAgent()

# Configure logging
def configure_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )