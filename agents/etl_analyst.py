# ReAct Agent for ETL Operations
# This agent is responsible for processing messages related to ETL (Extract, Transform, Load) operations. 
# It uses the LLMs to analyze the messages and generate appropriate responses or actions.

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.llm_pick import pick_llm
from utils.etl_tools import ETL_Tools
from models.schema import ETLAgentSchema
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langchain.tools import tool


# ----------------------------------------------------------- ETL Agent -----------------------------------------------------------


@tool
def extract_load_tool(url: str, output_folder: str, format: str) -> str:
    """
    Tool to extract data from the source (API[url]) and load it into the target or desired location (output_folder).

    Args:
        url (str): The URL of the source from which data needs to be extracted.
        output_folder (str): The folder path where the extracted data will be loaded.
        format (str): The format in which the data should be saved (e.g., 'csv', 'json', 'parquet').

    Returns:
        str: A message indicating the success or failure of the operation.
    """
    etl_tools = ETL_Tools()
    return etl_tools.extract_load(url, output_folder, format)


@tool
def transform_load_tool(input_file_path: str, n: int, output_folder: str, output_format: str, user_question: str) -> str:
    """
    Tool to transform the extracted data from the specified file and load it into the desired location (output_folder).

    Args:
        input_file_path (str): The path to the input file containing the extracted data.
        n (int): The number of rows to process or transform.
        output_folder (str): The folder path where the transformed data will be loaded.
        output_frame (str): The name of the output frame.
        user_question (str): The question posed by the user regarding the data transformation.

    Returns:
        str: A message indicating the success or failure of the operation.
    """
    etl_tools = ETL_Tools()

    top_n_rows_message = etl_tools.transform_load(input_file_path, n)

    llm = pick_llm("high")  # You can change the level as needed: "high", "medium", or "low"

    prompt = f"""
            You are a Python Data Analyst who uses Pandas to analyze data. 
            You need to provide only the Pandas Code that will help to perform the right ETL operations on the data stored in the file : {input_file_path}
            as per the user's question. Do not provide any explanation or comments, only
            the code should be provided. The code should be in a format that can be executed 
            in a Python environment with Pandas installed. 
            Don't write anything else than Pandas Code. \n
            
            Create the Pandas Dataframe from the data stored in the file : {input_file_path} and then 
            write the code to transform and save the data at {output_folder}.
            Here's the user's question: {user_question}\n
            Here's the context of the data you will be analyzing: {top_n_rows_message}\n

        """

    response = str(llm.invoke(prompt).content)

    # Optional cleaning of the response to extract only the code block if needed
    pandas_code = response.strip().strip('```').strip().lstrip('python').strip()  # Remove any code block markers if present

    # Execute the generated Pandas code
    execution_result = etl_tools.execute_code(pandas_code)

    return f"The data is transformed and saved at {output_folder} in {output_format} format. \n\n Pandas Code Executed: \n {pandas_code} \n\n Execution Result: \n {execution_result}"


# Toolkit
tools = [extract_load_tool, transform_load_tool]

llm = pick_llm("high")  # You can change the level as needed: "high", "medium", or "low"
llm_bind = llm.bind_tools(tools)


# ------------------------------------------------------------ AGENT GRAPH ------------------------------------------------------------

def llm_node(state:ETLAgentSchema):

    messages = state.messages

    prompt = f"""
            You are a Python Data Analyst who has access to tools that can extract and load, 
            transform and load data. You will be provided with a user's question 
            and you would need to perform the right ETL operations as per the user's question. 
            If the operation is performed then inform the user and end the coversation.
            Here's the chat history: {messages}\n
    """

    final_answer = llm_bind.invoke(prompt)

    # Update the state with the final answer from the LLM
    state.messages = messages + [final_answer]

    return state


def tool_node(state:ETLAgentSchema):
    """
    This node is responsible for invoking the appropriate tool based on the user's question and the context provided by the LLM.
    """

    # would contain the results of the tool invocations
    tools_results = []

    # Create a mapping of tool names to tool instances for easy access
    tools_by_name = {tool.name: tool for tool in tools}

    # Get the tool calls from the last message in the state
    tool_calls = state.messages[-1].tool_calls

    for tool_call in tool_calls:

        tool = tools_by_name[tool_call['name']] # Get the tool instance based on the name
        observation = tool.invoke(tool_call['args']) # Invoke the tool with the provided arguments and get the observation/result

        # Append the observation to the tools_results list as a ToolMessage, including the tool_call_id for reference
        tools_results.append(ToolMessage(content=observation, tool_call_id = tool_call['id']))

    # Update the state with the results of the tool invocations along with the previous messages
    state.messages = state.messages + tools_results

    return state


# Nodes & Edges
etl_analyst_graph = StateGraph(ETLAgentSchema)
etl_analyst_graph.add_node("LLM Node", llm_node)
etl_analyst_graph.add_node("Tool Node", tool_node)

etl_analyst_graph.add_edge(START, "LLM Node")

# to check if the tool is safe to use or not
def is_tool_safe(state: ETLAgentSchema):

    tool_calls = state.messages[-1].tool_calls

    if tool_calls:
        return "Tool Node"
    else:
        return "END"

etl_analyst_graph.add_conditional_edges(
    "LLM Node", is_tool_safe,
    {
        "Tool Node": "Tool Node",
        "END": END
    }
)

etl_analyst_graph.add_edge("Tool Node", "LLM Node")

etl_analyst = etl_analyst_graph.compile()

if __name__ == "__main__":

    # # Picture
    # from IPython.display import Image
    # img = etl_analyst.get_graph().draw_mermaid_png()
    # with open("etl_analyst_graph.png", "wb") as f:
    #     f.write(img)

    # response = etl_analyst.invoke(
    #     ETLAgentSchema(
    #         messages=[
    #             HumanMessage(content="I want to extract the data from the API endpoint 'https://pokeapi.co/api/v2/pokemon' and save it to data/extractions folder in the csv folder.")
    #         ]
    #     )
    # )

    response = etl_analyst.invoke(
        ETLAgentSchema(
            messages=[
                HumanMessage(content=f"""I want to transform the data stored in the 'c:\\Data_Agent\\data\\extract\\extracted_data.csv' file 
                            and save the transformed data in the 'd:\\Data_Agent\\data\\transformations' folder in the csv format.
                            The transformation should filter the data to show charizard pokemon only.
              """)
            ]
        )
    )