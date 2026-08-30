from agents.Data_Agent import data_agent
from models.schema import DataAgentSchema
from langchain_core.messages import HumanMessage

if __name__ == "__main__":

    initial_message = HumanMessage(content="What are the different types of Payment Methods available in the system?")

    response = data_agent.invoke(
        DataAgentSchema(
            messages=[initial_message],
            router_response=""
        )
    )
    
    print(response)