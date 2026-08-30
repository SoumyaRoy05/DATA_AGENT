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
  
## Database:
- The PostgreSQL database is used to store the data extracted from files and transformed into a suitable format.  
- The database is used by the SQL Analyst Agent to execute SQL queries and fetch results based on the user's question.  
  
## FILES:
- main.py: The main entry point of the application. It calls the main Data Agent to process the user's question and route it to the appropriate agent (SQL Analyst or ETL Analyst) based on the context of the question and the database.  
  
- feed_db.py: This file is used for writing out data into the PostgreSQL database. It contains functions for extracting data from files, transforming it into a suitable format, and loading it into the PostgreSQL database.  
  It also contains functions for creating the necessary tables in the database if they don't already exist.  

- data_agent_graph.py: Image of the Data Agent Graph made after compilation of the configured graph from respective nodes and edges.  
  D:\Codes\DATA_AGENT\data_agent_graph.png
  
- sql_analyst_graph.py: Image of the SQL Analyst Graph made after compilation of the configured graph from respective nodes and edges.  
  D:\Codes\DATA_AGENT\sql_analyst_graph.png
  
- etl_analyst_graph.py: Image of the ETL Analyst Graph made after compilation of the configured graph from respective nodes and edges.  
  D:\Codes\DATA_AGENT\etl_analyst_graph.png
  
# Agents:
The Agents folder contains the implementation of the different agents used in the End-to-End Agentic System. Each agent is responsible for handling specific tasks related to the user's question and the database. The agents use LLMs to analyze the user's question and generate appropriate responses or actions.  
  
- agents/Data_Agent.py: This agent is responsible for routing the user's question to the appropriate agent (SQL Analyst or ETL Analyst) based on the context of the question and the database. It uses the LLMs to analyze the user's question and generate a response indicating which agent should handle the question.  
  
- agents/sql_analyst.py: This agent is responsible for analyzing the user's question, generating a SQL query, and executing it against the database. It uses the LLMs to curate the user's question into a more detailed prompt, generate the SQL query, and judge the safety of the generated SQL query.  
  
- agents/etl_analyst.py: This agent is responsible for processing messages related to ETL (Extract, Transform, Load) operations. It uses the LLMs to analyze the messages and generate appropriate responses or actions.
  
# Utils:
The Utils folder contains utility functions that are used by the agents to perform various tasks, such as interacting with the database, picking an LLM based on the user's question, and performing agentic operations.  
  
- utils/llm_pick.py: Used to pick an LLM out of the three LLMs (high, medium, low) based on the user's question and the context of the database.  

- utils/database.py: Contains utility functions for interacting with the database, such as executing SQL queries and fetching results.  

- utils/etl_tools.py: Contains utility functions for ETL operations, such as extracting data from files, transforming data, and loading data into the database.
  
# Models:
The Models folder contains Pydantic models for validating the input and output data structures used by the agents by defining schemas for all of the agents.  
  
- models/schema.py: Contains Pydantic models for validating the input and output data structures used by the agents. It defines schemas for the SQL Analyst Agent, ETL Analyst Agent, LLM as a Judge, and Data Agent.  
  
# Data:  
The data folder contains the datasets used for training and testing the agents. It includes CSV files, JSON files, and other data formats.  

- data/extractions: Folder containing extracted data files used for extraction by the ETL Analyst Agent.  
  
- data/tranformations: Folder containing transformed data files which are loaded after transformation by the ETL Analyst Agent.  
  
  
## Future Improvements:  
  
To make it work reliably, you need to do one of these:  
  
switch to a model/provider that supports structured output  
remove with_structured_output(...) and parse plain-text JSON manually  
keep the route logic but avoid the incompatible backend  
