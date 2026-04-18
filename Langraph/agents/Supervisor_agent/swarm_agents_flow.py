from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage
from langchain_core.messages import BaseMessage,SystemMessage
from langchain_core.prompts import ChatPromptTemplate,PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import DirectoryLoader,PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma, FAISS
from langchain_openai import ChatOpenAI,OpenAIEmbeddings
from langgraph.graph import StateGraph,START, END,add_messages
from typing import TypedDict,Annotated,Literal
import os 
import sys
sys.path.insert(1, r'D:\Notebooks\LLM\env')
#sys.path.insert(2, r'C:\Users\Dharmendra Vartika\LLM\langchain_document_loader')
from enviorment import load_env
from langgraph.prebuilt import ToolNode,tools_condition
from typing import TypedDict,Literal,Annotated
from langchain_core.tools import tool
#from pydirectoryloader import rag_function
import os 
load_env()
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.chat_models import init_chat_model

from langgraph.checkpoint.memory import InMemorySaver
from langgraph_swarm import create_handoff_tool, create_swarm
            # Web search tool
model=ChatOpenAI()
import requests
from langchain.agents import create_agent
def get_weather_data(city: str) -> str:
  """
  This function fetches the current weather data for a given city
  """
  url = f'https://api.weatherstack.com/current?access_key=ec07421f5107d04ec9fa783c8fcfd6c5&query={city}'

  response = requests.get(url)

  return response.json()
def get_currency(base_currency:str,target_currency:str)->float:
    """this functions gives the latest currency exchange rate from a given one currency to anohter currency"""
    url=f"https://v6.exchangerate-api.com/v6/5b1e43ae2540e95e7a3490fc/pair/{base_currency}/{target_currency}"
    #
    print (url)
    r=requests.get(url)
    print ('response is ',r)
    return r.json()['conversion_rate']
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA') 
    using Alpha Vantage with API key in the URL.
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=C9PE94QUEW9VWGFM"
    r = requests.get(url)
    return r.json()
stock_agent=create_agent(model,[get_stock_price, create_handoff_tool(agent_name="weather",description="Transfer to weather , he can help with weather report")],
                   system_prompt='you are a broker who fetches latest stock price of a given stock in  US market ',
                   name="stock")
weather_agent=create_agent(model,[get_weather_data, create_handoff_tool(agent_name="currency",description="Transfer to Currency, he can help with currency exchange from base currency to another")],
                   system_prompt='you works in weather department who provides the current weather  of a given city ',
                   name="weather")
currency_agent=create_agent(model,[get_currency, create_handoff_tool(agent_name="stock",description="Transfer to stock, he can help with stock price")],
                   system_prompt='you works in currency exchange department who provides the exchange rate from one base currency to target currecny ',
                   name="currency")

#config = {"configurable": {"thread_id": "11"}}
workflow = create_swarm(
    [weather_agent, currency_agent,stock_agent],
    default_active_agent="currency"
)
#checkpointer = InMemorySaver()
#app = workflow.compile(checkpointer=checkpointer)
app = workflow.compile()
question=input("Please ask question: ")
state={"messages": [{"role": "user", "content": question}]}
#result =app.invoke(state,config=config)
result =app.invoke(state)
for i in result['messages']:
    i.pretty_print()