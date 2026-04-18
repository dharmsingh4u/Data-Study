import sys
from langchain_openai import ChatOpenAI,OpenAIEmbeddings
from langchain_core.messages import HumanMessage,AIMessage,SystemMessage,BaseMessage
from langchain_core.output_parsers import StrOutputParser,PydanticOutputParser
from langchain_core.prompts import PromptTemplate,ChatPromptTemplate,SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages
sys.path.insert(1, r'C:\Users\Dharmendra Vartika\LLM\env')
from enviorment import load_env
import os 
load_env()
model =ChatOpenAI()
from langgraph.graph import StateGraph,START, END
from typing import TypedDict,Annotated,Literal
import operator
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
import yfinance as yf
from ta.momentum import RSIIndicator
from pydantic import BaseModel, Field

class model_output(BaseModel):
    """model output"""
    Trend_analysis: str = Field(description="The gives us the trend analysis of the stock")
    Support_Resistance: str = Field(description="The gives us the Support/Resistance levels of stock")
    Technical_rating : Literal["Bullish", "Neutral", "Bearish"]
    Key_signals :str  = Field(description="The gives us key signals stock by looking at the latest news")
    urls :str  = Field(description="The gives us urls for the refrence"),
    sentiments :Literal["positive", "negative", "neutral"]  = Field(description="The gives us sentiments for the refrence")
    Final_recommendation: Literal["Strong Buy", "Buy", "Hold","Sell",'Strong Sell'] = Field(description="The gives us the final recommendation of the stock")
    Confidence_score: int = Field(description="The gives Confidence score ranging from 0 to 10")
    Target_price_range : float =Field(description='Target price range of the stock')
model_with_structured_output=model.with_structured_output(model_output)
class symbol(BaseModel):
    ticker_symbol: str =Field(description='ticker symbol for the stock')
search=DuckDuckGoSearchRun()
tool=[search]
#prompt ='can you get ticker symbol only for the Quantum-Si (QSI) stock'
llm_with_tools = model.bind_tools(tool)
llm_bind=llm_with_tools.with_structured_output(symbol)
tool_node = ToolNode(tool)
#result=llm_bind.invoke(prompt)
#result.ticker_symbol
class stock_analyzer(TypedDict):
    data  :dict
    prompt :str
    symbol :str
    Trend_analysis:str
    Support_Resistance:str
    Technical_rating:str
    Key_signals :str
    summary: str
    sentiments:str
    Final_recommendation : str
    Confidence_score :int
    Target_price_range : float
news=[]
url =[]
parser=StrOutputParser()
#search_Tavily = TavilySearchResults(max_results=2)
import requests
def get_stock_data(state:stock_analyzer):
    """Node for technical analysis for a given symbol"""
    prompt =state['prompt']
    result =llm_bind.invoke(prompt)
    stock=result.ticker_symbol
    stock = yf.Ticker(stock)
    hist = stock.history(period='1y')

    # Calculate indicators
    sma_20 = hist['Close'].rolling(window=20).mean()
    sma_50 = hist['Close'].rolling(window=50).mean()
    rsi_indicator = RSIIndicator(close=hist['Close'], window=14)
    rsi = rsi_indicator.rsi()
    state['symbol']=stock
    state['data'] = {
    'current_price': hist['Close'].iloc[-1],
    'sma_20': sma_20.iloc[-1],
    'sma_50': sma_50.iloc[-1],
    'rsi': rsi.iloc[-1],
    'volume_trend': hist['Volume'].iloc[-5:].mean() / hist['Volume'].iloc[-20:].mean()}
    return state

def get_stock_analyser(state:stock_analyzer):

    symbol=state['symbol']
    data=state['data']
    chatprompt2 = ChatPromptTemplate.from_messages([SystemMessagePromptTemplate.from_template("""You are a helpful financial assistant """),
                                                HumanMessagePromptTemplate.from_template("""Based on the following analyses  for {symbol}:
        {data}

        Provide:
        1. Trend analysis
        2. Support/Resistance levels
        3. Technical rating (Bullish/Neutral/Bearish)
        4. Key signals using the news provided
        6 Sentiments anlaysis based on the recent news and trend analysis     
        7 :Final recommendation (Strong Buy/Buy/Hold/Sell/Strong Sell)                                                                                                                                                               
        8. Confidence_score ranging from 0 to 10
        9 :Target price range for the stock                                                                                 
        """)])
    chatprompt_final=chatprompt2.invoke({'symbol':symbol,'data':data})
    result=model_with_structured_output.invoke(chatprompt_final)
    state['Trend_analysis']=result.Trend_analysis
    state['Support_Resistance']=result.Support_Resistance
    state['Technical_rating']=result.Technical_rating
    state['Key_signals']=result.Key_signals
    state['urls']=result.urls
    state['sentiments']=result.sentiments
    state['Final_recommendation']=result.Final_recommendation
    state['Confidence_score']=result.Confidence_score
    state['Target_price_range']=result.Target_price_range
    state['data']={}
    return state
def get_stock_summary(state:stock_analyzer):

    Technical_rating=state['Technical_rating']
    Support_Resistance=state['Support_Resistance']
    Trend_analysis=state['Trend_analysis']
    Key_signals=state['Key_signals']
    symbol =state['symbol']
    Final_recommendation=state['Final_recommendation']
    Target_price_range=state['Target_price_range']
    sentiments=state['sentiments']
    chatprompt2 = ChatPromptTemplate.from_messages([SystemMessagePromptTemplate.from_template("""You are a helpful financial assistant """),
                                                
    HumanMessagePromptTemplate.from_template("""Based on the following technical analyses,key signals,support resistence,sentiments, target price
        final recommendation
         please provide a  brief summary, final recommendation ,Target price range,key signals,resistence for a
        retail investor which can give him an idea about this stock behaviour and overall sentiments in public.Please mention key points in bold letters
        {Technical_rating},{Trend_analysis}, {Support_Resistance},{Key_signals},{Target_price_range},{sentiments}
         {Final_recommendation}                                                                
        """)])
    chatprompt_final=chatprompt2.invoke({'symbol':symbol,'Technical_rating':Technical_rating,'Trend_analysis':Trend_analysis,'Support_Resistance':Support_Resistance,'Key_signals':Key_signals,
                     'Final_recommendation':Final_recommendation,'Target_price_range' :Target_price_range,'sentiments':sentiments})
    result=model.invoke(chatprompt_final)
    state['summary']=result.content
    state['data']={}
    return state

graph=StateGraph(stock_analyzer)
graph.add_node('get_stock_data_l',get_stock_data)
graph.add_node('get_stock_analyser_l',get_stock_analyser)
graph.add_node('get_stock_summary_l',get_stock_summary)
#graph.add_node('tools',tool_node)
##########################edge nodes############################
graph.add_edge(START,'get_stock_data_l')
#graph.add_conditional_edges('get_stock_data_l',tools_condition)
#graph.add_edge('tools','get_stock_data_l')
graph.add_edge('get_stock_data_l','get_stock_analyser_l')
graph.add_edge('get_stock_analyser_l','get_stock_summary_l')
graph.add_edge('get_stock_summary_l',END)
workflow=graph.compile()
