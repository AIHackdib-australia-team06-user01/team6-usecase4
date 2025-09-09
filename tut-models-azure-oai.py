import asyncio
import os

from dotenv import load_dotenv
from autogen_core.models import UserMessage
from autogen_ext.auth.azure import AzureTokenProvider
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from azure.identity import DefaultAzureCredential

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if api_key is None:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

azure_endpoint = os.getenv("AZURE_ENDPOINT")
if azure_endpoint is None:
    raise ValueError("AZURE_ENDPOINT environment variable not set.")

az_model_client = AzureOpenAIChatCompletionClient(
    azure_deployment="gpt-5-mini",
    model="gpt-5-mini",
    api_version="2024-12-01-preview",
    azure_endpoint=azure_endpoint,
    # azure_ad_token_provider=token_provider,  # Optional if you choose key-based authentication.
    api_key=api_key, # For key-based authentication.
)

# Run the agent and stream the messages to the console.
async def main() -> None:
    result = await az_model_client.create([UserMessage(content="What is the capital of France?", source="user")])
    print(result)
    
    await az_model_client.close()

# NOTE: if running this inside a Python script you'll need to use asyncio.run(main()).
# await main()
asyncio.run(main())