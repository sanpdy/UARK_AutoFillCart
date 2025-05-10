from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv(override=True)

openai_api_key = os.environ["OPENAI_API_KEY"]
walmart_consumer_id = os.environ["WALMART_CONSUMER_ID"]
walmart_key_version = os.environ["WALMART_KEY_VERSION"]
walmart_private_key_path = os.environ["WALMART_PRIVATE_KEY_PATH"]


# Retrieve the API keys from environment variables
# openai_api_key = os.getenv("OPENAI_API_KEY")
# anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
# TODO: Add other API keys as needed
