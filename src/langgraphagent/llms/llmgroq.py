import os
import sys
from langchain_groq import ChatGroq

class GroqLLM:
    """
    A class to configure and provide the Groq LLM model.
    """
    def __init__(self):
        """
        The .env file is loaded in main.py, so we just need to access the environment variables here.
        """
        pass

    def get_llm_model(self):
        """
        Initializes and returns the Groq LLM client.
        Checks for the API key from environment variables and exits if not found.
        """
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("Error: GROQ_API_KEY not found in environment variables.")
            print("Please create a .env file in the root directory and add GROQ_API_KEY='your-key'.")
            sys.exit(1)

        try:
            llm = ChatGroq(api_key=api_key, model_name="openai/gpt-oss-120b", temperature=0)
            return llm
        except Exception as e:
            raise ValueError(f"Error occurred while initializing Groq LLM: {e}")

