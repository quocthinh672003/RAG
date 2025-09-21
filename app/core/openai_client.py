# AsyncOpenAI init (singleton)
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)
