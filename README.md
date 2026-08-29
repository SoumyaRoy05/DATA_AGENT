# RAG Guide
## LLMs Used:
High Level --> Gemini 3.6 flash  
Through API Key made from https://aistudio.google.com/api-keys  

Medium Level --> Nvidia Nemotron 3 Ultra (550B)  
Through API Key made from https://build.nvidia.com/settings/api-keys  

Low Level --> Ollama Qwen2.5-Coder (7B)
Downloaded locally from Ollama

Vector Folder is used to store the vector database for future use.  
Not added to GitHub for security reasons. Please create your own vector folder and add it to the .gitignore file.
  
## FILES:
# Agents:
- agents/sql_analyst.py: This agent is responsible for analyzing the user's question, generating a SQL query, and executing it against the database. It uses the LLMs to curate the user's question into a more detailed prompt, generate the SQL query, and judge the safety of the generated SQL query.
- agents/etl_analyst.py: This agent is responsible for processing messages related to ETL (Extract, Transform, Load) operations. It uses the LLMs to analyze the messages and generate appropriate responses or actions.

# Utils:
- utils/llm_pick.py: Used to pick an LLM out of the three LLMs (high, medium, low) based on the user's question and the context of the database.
- utils/database.py: Used to connect to the database and perform operations like creating tables, inserting data, and querying data.

# Models:
- models/agent_schema.py: Defines the schema for the agent's state, including the user's question, the generated SQL query, and the prompt query context.

- feed_db.py: Used to feed the database with data from the vector folder.
