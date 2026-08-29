import os
import sys
from typing import cast

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain.messages import HumanMessage, AIMessage
from dotenv import load_dotenv

load_dotenv()

from utils.llm_pick import pick_llm
from models.schema import AgentSchema, JudgeSchema
from utils.database import Database
from langgraph.graph import StateGraph, START, END


# ------------------------------------------------------------------- AI Agent Configuration -------------------------------------------------------------------

# This function curates the user question into a more detailed and specific prompt for SQL query generation.
# from schema.py
def curated_prompt(state: AgentSchema) -> AgentSchema:

    user_question = state.user_question #Bcz this is a Pydantic model

    llm = pick_llm("medium")  # Pick the appropriate LLM based on the desired level

    response = str(llm.invoke(f"Curate the user question: '{user_question}' into a more detailed and specific prompt for SQL query generation.").content)

    state.curated_prompt = response  # Update the curated prompt in the state
    state.messages = state.messages + [HumanMessage(content=f"Curated Prompt: {response}")]  # Append the curated prompt to the messages
    return state


# creating a different node to generate the prompt_query_context from the curated_prompt node
# from schema.py
def prompt_query_context(state: AgentSchema) -> AgentSchema:
    curated_prompt = state.curated_prompt  # Get the curated prompt from the state

    conn_details = {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "dbname": os.getenv("DB_NAME", "data_agent").lower()
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
# from schema.py
def generate_sql(state: AgentSchema) -> AgentSchema:

    prompt = state.prompt_query_context  # Get the prompt query context from the state

    llm = pick_llm("high")  # Pick the appropriate LLM based on the desired level
    generated_sql_query = str(llm.invoke(prompt).content)  # Generate the SQL query using the LLM

    state.generated_sql_query = generated_sql_query  # Update the generated SQL query in the state

    return state  # Return the updated state with the generated SQL query


# is safe node
# from schema.py
def is_safe(state: AgentSchema) -> AgentSchema:

    sql_query = state.generated_sql_query  # Get the generated SQL query from the state
    llm = pick_llm("high")  # Pick the appropriate LLM based on the desired level
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
    state.comments = response.comment  # Update the comments in the state

    return state  # Return the updated state with the safety status


# Cancelled SQL Query node
def cancelled_sql(state: AgentSchema) -> AgentSchema:
    # If the SQL query is not safe, we can cancel the execution and provide a message
    
    comments = state.comments  # Get the comments from the state

    state.final_answer = f"The SQL query is not safe to execute. Reason: {comments}"  # Update the final answer in the state
    state.messages = state.messages + [AIMessage(content=f"Final Answer: {state.final_answer}")]  # Append the final answer to the messages 

    return state  # Return the updated state with the final answer


# Execute SQL Query node
# from database.py
def execute_sql(state: AgentSchema) -> AgentSchema:
    # If the SQL query is safe, we can execute it and provide the result

    sql_query = state.generated_sql_query  # Get the generated SQL query from the state

    # Get the database connection details from environment variables
    conn_details = {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "dbname": os.getenv("DB_NAME", "data_agent").lower()
    }

    obj = Database(conn_details)  # Create a Database object with the connection details
    execution_result = obj.execute_sql(sql_query)  # Execute the SQL query and get the result

    state.sql_query_execution_result = execution_result  # Update the SQL query execution result in the state
    state.messages = state.messages + [AIMessage(content=f"SQL Query Execution Result: {execution_result}")]  # Append the execution result to the messages
    state.final_answer = f"The SQL query executed successfully. Result: {execution_result}"  # Update the final answer in the state

    return state  # Return the updated state with the final answer


# Represent the final answer node
def represent_final_answer(state: AgentSchema) -> AgentSchema:
    # This node represents the final answer generated by the agent based on the SQL query execution result

    execution_result = state.sql_query_execution_result  # Get the SQL query execution result from the state
    curated_prompt = state.curated_prompt  # Get the curated prompt from the state

    llm = pick_llm("low")  # Pick the appropriate LLM based on the desired level

    prompt = f"""
    You are an SQL analyst agent. Your task is to provide a final answer to the user based on the
    execution result of the SQL query and the user's original question. The final answer should be
    concise, clear, and directly address the user's query. Avoid including any SQL code or technical
    details in the final answer. The final answer should be in a user-friendly format that is easy to
    understand. If the execution result is empty or does not provide a clear answer to the user's question, explain this in the final answer. \n
    Here is the execution result: {execution_result} \n
    Here is the user's original question: {curated_prompt}
    """

    llm_response = str(llm.invoke(prompt).content)  # Invoke the LLM with the prompt to generate the final answer

    state.final_answer = llm_response  # Update the final answer in the state
    state.messages = state.messages + [AIMessage(content=f"Final Answer: {llm_response}")]  # Append the final answer to the messages

    return state  # Return the updated state with the final answer


# ----------------------------------------------------------------- Graph Construction -----------------------------------------------------------------

sql_agent_graph = StateGraph(AgentSchema)  # Create a StateGraph object with the AgentSchema

# Nodes in the graph
sql_agent_graph.add_node("curated_prompt", curated_prompt)  # Node to curate the user question
sql_agent_graph.add_node("prompt_query_context", prompt_query_context)  # Node to generate the prompt query context
sql_agent_graph.add_node("generate_sql", generate_sql)  # Node to generate the SQL query
sql_agent_graph.add_node("is_safe", is_safe)  # Node to check if the SQL query is safe
sql_agent_graph.add_node("cancelled_sql", cancelled_sql)  # Node to handle cancelled SQL sql_query_execution_result
sql_agent_graph.add_node("execute_sql", execute_sql)  # Node to execute the SQL query
sql_agent_graph.add_node("represent_final_answer", represent_final_answer)  # Node to represent the final answer

# Edges in the graph
sql_agent_graph.add_edge(START, "curated_prompt")  # Edge from START to curated_prompt
sql_agent_graph.add_edge("curated_prompt", "prompt_query_context")  # Edge from curated_prompt to prompt_query_context
sql_agent_graph.add_edge("prompt_query_context", "generate_sql")  # Edge from prompt_query_context to generate_sql
sql_agent_graph.add_edge("generate_sql", "is_safe")  # Edge from generate_sql to is_safe

# Conditional edge function
def is_safe_edge(state: AgentSchema) -> str:
    is_safe = state.is_safe  # Get the safety status from the state

    if is_safe == "Yes":
        return "execute_sql"
    else:
        return "cancelled_sql"

# Add conditional edges based on the safety status
sql_agent_graph.add_conditional_edges("is_safe", is_safe_edge,
                                      {
                                          "execute_sql": "execute_sql",
                                          "cancelled_sql": "cancelled_sql"
                                      })  # Add conditional edges based on the safety status

sql_agent_graph.add_edge("cancelled_sql", END)  # Edge from cancelled_sql to represent_final_answer
sql_agent_graph.add_edge("execute_sql", "represent_final_answer")  # Edge from execute_sql to represent_final_answer
sql_agent_graph.add_edge("represent_final_answer", END)  # Edge from represent_final_answer to END


if __name__ == "__main__":
    # Graph Compilation
    sql_analyst = sql_agent_graph.compile()  # Compile the graph to finalize its structure and prepare it for execution

    # # Generate a visual representation of the graph in Mermaid format
    # img = sql_analyst.get_graph().draw_mermaid_png()  # Generate a visual representation of the graph in PNG format
    # with open("sql_analyst_graph.png", "wb") as f:
    #     f.write(img)  # Save the graph image to a file

    input_schema = AgentSchema(
        messages=[],
        user_question="What are the different types of Payment Methods available in the system?",
        curated_prompt="",
        prompt_query_context="",
        generated_sql_query="",
        is_safe="No",
        comments="",
        sql_query_execution_result="",
        final_answer=""
    )

    # Execute the graph with the provided input schema
    try:
        sql_analyst_response = sql_analyst.invoke(input_schema)  # Execute the graph with the provided input schema

        print(sql_analyst_response['messages'])  # Print the messages generated during the execution of the graph

        print("****************************************************************************")

        print(sql_analyst_response['generated_sql_query'])  # Print the generated SQL query

        print("****************************************************************************")

        print(sql_analyst_response['sql_query_execution_result'])  # Print the result of executing the SQL query

        print("****************************************************************************")

        print(sql_analyst_response['prompt_query_context'])  # Print the prompt query context used for generating the SQL query

        print("****************************************************************************")

        print(sql_analyst_response['final_answer'])  # Print the final answer generated by the agent based on the SQL query execution result
    except Exception as e:
        print(f"Error during graph execution: {str(e)}")
        print(f"Error type: {type(e).__name__}")