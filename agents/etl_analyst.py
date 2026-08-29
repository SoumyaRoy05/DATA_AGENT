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
def transform_load_tool(input_file_path: str, n: int, output_folder: str, output_frame: str, user_question: str) -> str:
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

    response = llm.invoke(prompt).content

    # Optional cleaning of the response to extract only the code block if needed
    pandas_code = response.strip().strip("```").strip().lstrip('python').strip()  # Remove any code block markers if present

    # Execute the generated Pandas code
    execution_result = etl_tools.execute_code(pandas_code)

    return f"The data is transformed and saved at {output_folder} in {output_format} format. \n\n Pandas Code Executed: \n {pandas_code} \n\n Execution Result: \n {execution_result}"