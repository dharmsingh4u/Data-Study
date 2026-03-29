import sys
from langchain_openai import ChatOpenAI,OpenAIEmbeddings
from langchain_core.messages import HumanMessage,AIMessage,SystemMessage,BaseMessage
from langchain_core.output_parsers import StrOutputParser,PydanticOutputParser
from langchain_core.prompts import PromptTemplate,ChatPromptTemplate
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
import requests
sys.path.insert(1, r'C:\Users\Dharmendra Vartika\LLM\env')
from enviorment import load_env
import os 
load_env()
model =ChatOpenAI()
from langgraph.graph import StateGraph,START, END
from typing import TypedDict,Annotated
import operator
class bot(TypedDict):
    messages :Annotated[list[BaseMessage],add_messages]
search_tool = DuckDuckGoSearchRun(region="us-en")
@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations: add, sub, mul, div
    """
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {"error": "Division by zero is not allowed"}
            result = first_num / second_num
        else:
            return {"error": f"Unsupported operation '{operation}'"}
        
        return {"first_num": first_num, "second_num": second_num, "operation": operation, "result": result}
    except Exception as e:
        return {"error": str(e)}




@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA') 
    using Alpha Vantage with API key in the URL.
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=C9PE94QUEW9VWGFM"
    r = requests.get(url)
    return r.json()



tools = [search_tool, get_stock_price, calculator]
llm_with_tools = model.bind_tools(tools)
def Chatbot(state:bot):
    text =state['messages']
    #messages =[HumanMessage(text)]
    result=llm_with_tools.invoke (text)
    #messages =[AIMessage(result.content)]
        #print ('AI response is ',result.content)
    return {'messages' :[result]}
#checkpoint =InMemorySaver()
conn = sqlite3.connect(database='chatbot_dharmendra.db', check_same_thread=False)
# Checkpointer
Checkpointer = SqliteSaver(conn=conn)
tool_node = ToolNode(tools)
graph=StateGraph(bot)
graph.add_node('Chatbot',Chatbot)
graph.add_node('tools',tool_node)
graph.add_edge(START,'Chatbot')
graph.add_conditional_edges('Chatbot',tools_condition)
graph.add_edge('tools','Chatbot')
graph.add_edge('Chatbot',END)
chatbot =graph.compile(checkpointer=Checkpointer)

def retrieve_all_threads():
    all_threads = set()
    for checkpoint in Checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])

    return list(all_threads)

