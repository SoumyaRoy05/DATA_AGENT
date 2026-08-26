# RAG Guide
LLMs Used:
High Level --> Gemini 2.0 flash  
Through API Key made from https://aistudio.google.com/api-keys  

Medium Level --> Nvidia Nemotron 3 Ultra (550B)  
Through API Key made from https://build.nvidia.com/settings/api-keys  

Low Level --> Ollama Qwen2.5-Coder (7B)
Downloaded locally from Ollama

Vector Folder is used to store the vector database for future use.  
Not added to GitHub for security reasons. Please create your own vector folder and add it to the .gitignore file.
  
FILES:
- utils/llm_pick.py: Used to pick an LLM out of the three LLMs (high, medium, low) based on the user's question and the context of the database.
- utils/

- feed_db.py: Used to feed the database with data from the vector folder.