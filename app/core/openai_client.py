# AsyncOpenAI init (singleton)
from openai import AsyncOpenAI
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)