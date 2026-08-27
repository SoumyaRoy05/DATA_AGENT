import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

from utils.llm_pick import pick_llm
from models.schema import AgentSchema, JudgeSchema
from utils.database import Database

llm = pick_llm("medium")  # Pick the appropriate LLM based on the desired level
llm_judge = llm.with_structured_output(JudgeSchema)  # Use the same LLM for judging with structured output

sql_query = "SELECT * FROM users;"  # Example SQL query to judge

prompt = """
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

response = llm_judge.invoke(prompt)
print(response)