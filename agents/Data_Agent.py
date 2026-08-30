# This file is the main routing agent, 
# which is responsible for determining whether to use the SQL Analyst or ETL Analyst agent based on the user's question and the context provided by the LLM.

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.llm_pick import pick_llm
from utils.etl_tools import ETL_Tools
from models.schema import RouterSchema, DataAgentSchema, ETLAgentSchema, AgentSchema
from agents.sql_analyst import sql_analyst
from agents.etl_analyst import etl_analyst
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langchain.tools import tool
from typing import cast


llm = pick_llm("high")  # You can change the level as needed: "high", "medium", or "low"
llm_router = llm.with_structured_output(RouterSchema)  # Configure the LLM to produce structured output based on the RouterSchema


# ----------------------------------------------------------- DATA AGENT GRAPH -----------------------------------------------------------

def router_node(state: DataAgentSchema):

    message = state.messages[-1].content  # Get the last message from the list of messages

    router_response_dict = dict(cast(RouterSchema, llm_router.invoke(message)))  # Invoke the LLM with the last message to get a routing decision

    router_response = router_response_dict['answer']  # Convert the LLM response to a dictionary

    state.router_response = router_response  # Store the router response in the state

    return state


def etl_node(state: DataAgentSchema):

    message = state.messages[-1]  # Get the last message from the list of messages

    response = etl_analyst.invoke(
        ETLAgentSchema(
            messages=[
                HumanMessage(content=f"""{message.content}
              """)
            ]
        )
    )  # Invoke the ETL Analyst agent with the last message

    state.messages = state.messages + [response]  # Update the state with the response from the ETL Analyst agent

    return state


def sql_node(state: DataAgentSchema):

    message = state.messages[-1]  # Get the last message from the list of messages

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

    response = sql_analyst.invoke(input_schema)  # Invoke the SQL Analyst agent with the last message

    state.messages = state.messages + [response]  # Update the state with the response from the SQL Analyst agent

    return state


# ----------------------------------------------------------- Graph Configuration -----------------------------------------------------------

data_agent_graph = StateGraph(DataAgentSchema)

data_agent_graph = StateGraph(DataAgentSchema)

data_agent_graph.add_node("router_node", router_node)
data_agent_graph.add_node("etl_node", etl_node)
data_agent_graph.add_node("sql_node", sql_node)

data_agent_graph.add_edge(START, "router_node")

def route_edge(state: DataAgentSchema) -> str:
    """
    This function determines the next node in the graph based on the router's response.
    """
    if state.router_response == "SQL_Analyst":
        return "sql_node"
    elif state.router_response == "ETL_Analyst":
        return "etl_node"
    else:
        raise ValueError(f"Invalid route response: {state.router_response}")


data_agent_graph.add_conditional_edges(
    "router_node",
    route_edge,
    {
        "sql_node": "sql_node",
        "etl_node": "etl_node",
    },
)

data_agent = data_agent_graph.compile()

# Optional|
from IPython.display import display, Image
img = data_agent.get_graph().draw_mermaid_png()
with open("data_agent_graph.png", "wb") as f:
    f.write(img)


# for testing the Data Agent
if __name__ == "__main__":

    # Example usage of the Data Agent
    initial_message = HumanMessage(content="What are the different types of Payment Methods available in the system?")  # Example user question

    response = data_agent.invoke(
        DataAgentSchema(
            messages=[initial_message],
            router_response=""
        )
    )  # Invoke the Data Agent with the initial message

    print(response)