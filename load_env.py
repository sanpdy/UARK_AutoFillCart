from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv(override=True)

# Retrieve the API keys from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
