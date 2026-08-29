from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_nvidia_ai_endpoints import ChatNVIDIA, ChatNVIDIADynamo
from langchain_ollama import ChatOllama
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

def pick_llm(level: str):
    """
    Picks the appropriate LLM based on the given level.

    Args:
        level (str): The level of the LLM to pick. Can be "high", "medium", or "low".

    Returns:
        str: The name of the picked LLM.
    """
    if level.lower() == "high":
        llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash")

    elif level.lower() == "medium":
        llm = ChatNVIDIA(model="nvidia/nemotron-3-ultra-550b-a55b") 
        # try to use ChatNVIDIADynamo for caching and faster responses, but may have some limitations compared to the full model
        # llm = ChatNVIDIADynamo(base_url="http://localhost:8099/v1", model="nvidia/nemotron-3-ultra-550b-a55b")

    elif level.lower() == "low":
        llm = ChatOllama(model="qwen2.5-coder:7b", # Model name to be used for generating responses
                         base_url="http://localhost:11434",  # Default local Ollama host
                         temperature=0)
        
    else:
        raise ValueError("Invalid level. Choose from 'high', 'medium', or 'low'.")


    return llm


# Note: Module-level code removed to prevent connection errors during import
# Uncomment below to test LLM locally
# if __name__ == "__main__":
#     llm_obj = pick_llm("high")  # Change the level as needed: "high", "medium", or "low"
#     response=llm_obj.invoke("What is the capital of France?")  # Example usage of the picked LLM
#     print(response.content)  # Print the response from the LLM