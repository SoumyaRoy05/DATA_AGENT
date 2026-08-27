import os
import sys
from typing import cast

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

from utils.llm_pick import pick_llm
from models.schema import AgentSchema, JudgeSchema
from utils.database import Database


# ------------------------------------------------------------------- AI Agent Configuration -------------------------------------------------------------------

# This function curates the user question into a more detailed and specific prompt for SQL query generation.
def curated_prompt(state: AgentSchema) -> AgentSchema:

    user_question = state.user_question #Bcz this is a Pydantic model

    llm = pick_llm("low")  # Pick the appropriate LLM based on the desired level

    response = llm.invoke(f"Curate the user question: '{user_question}' into a more detailed and specific prompt for SQL query generation.")

    state.curated_prompt = response.text  # Update the curated prompt in the state
    state.messages = state.messages + [HumanMessage(content=f"Curated Prompt: {response.text}")]  # Append the curated prompt to the messages
    return state


# creating a different node to generate the prompt_query_context from the curated_prompt node
def prompt_query_context(state: AgentSchema) -> AgentSchema:
    curated_prompt = state.curated_prompt  # Get the curated prompt from the state

    conn_details = {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "dbname": os.getenv("DB_NAME")
    }

    obj = Database(conn_details)  # Create a Database object with the connection details
    schema_info = obj.schema_details("public")  # Fetch schema details for the "public" schema

    # Constructing the prompt query for the agent to generate the SQL query
    # Guardrailing at line number 6 from "Unless"
    prompt = f"""
    You are an SQL analyst agent. Your task is to convert the user's natural language 
    query into Postgres SQL query that can be executed on the database. You are provided 
    with the user's original query and the schema details of the database, including
    table names, column names, data types, and sample data for each table so that 
    you can understand the structure of the database and generate an accurate SQL query.
    Unless user explicitly asks for specific number of rows, always limit the output to 10 rows.
    Note - Just generate the SQL query without any explanation or additional text because
    this query will be executed directly on the database. So, the output should be SQL
    ready to be executed without any modifications.
    
    User's Original Query: {curated_prompt}

    Database Schema Details:
    {schema_info}
    
    """ 

    state.prompt_query_context = prompt  # Update the prompt query context in the state

    return state  # Return the updated state with the generated SQL query and prompt context


# creating a different node to generate the sql query from the prompt_query_context node
# because it is a separate task and can be reused in other agents as well
def generate_sql(state: AgentSchema) -> AgentSchema:

    prompt = state.prompt_query_context  # Get the prompt query context from the state

    llm = pick_llm("medium")  # Pick the appropriate LLM based on the desired level
    generated_sql_query = llm.invoke(prompt)  # Generate the SQL query using the LLM

    state.generated_sql_query = generated_sql_query.text  # Update the generated SQL query in the state

    return state  # Return the updated state with the generated SQL query

# is safe node
def is_safe(state: AgentSchema) -> AgentSchema:

    sql_query = state.generated_sql_query  # Get the generated SQL query from the state
    llm = pick_llm("medium")  # Pick the appropriate LLM based on the desired level
    llm_judge = llm.with_structured_output(JudgeSchema)  # Use the same LLM for judging with structured output

    prompt = f"""
    You are an SQL Judge for data security. Your task is to determine whether the SQL query is
    safe or not. The SQL query should only be used for data retrival and should not modify the
    database in any way. Neither the SQL query nor the prompt should contain any modify the database,
    such as INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, or any other SQL commands that can
    change the database structure or data. If the SQL query is safe, respond with "Yes" and provide a
    brief comment explaining why it is safe. If the SQL query is not safe, respond with "No" and
    provide a brief comment explaining why it is not safe.
    Here is the SQL query to judge:
    {sql_query}

    """
    
    response = cast(JudgeSchema, llm_judge.invoke(prompt))  # Invoke the LLM judge with the prompt
    state.is_safe = response.answer  # Update the safety status in the state

    return state  # Return the updated state with the safety status