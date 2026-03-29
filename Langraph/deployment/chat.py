from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage,HumanMessage,SystemMessage
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
#sys.path.insert(1, r'C:\Users\Dharmendra Vartika\LLM\env')
#sys.path.insert(2, r'C:\Users\Dharmendra Vartika\LLM\langchain_document_loader')
from enviorment import load_env
from langgraph.prebuilt import ToolNode,tools_condition
from typing import TypedDict,Literal,Annotated
from langchain_core.tools import tool
#from pydirectoryloader import rag_function
import os 
load_env()
from langchain_community.tools.tavily_search import TavilySearchResults


class human(TypedDict):
    message :Annotated[list[BaseMessage],add_messages]
    # :str
    feedack :str
    comment:str
model_llm=ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
def chatbot_dharmendra(state:human):
    ques=state['message']
    result=model_llm.invoke(ques)
    #print ('tool_message',result.tool_calls)
    #state['tool_message']=result
    #state['result']=result.content
    state['message']=[result]
    #state['feeback']='good'
    return state
def approve(state:human):
    return state 
def reject(state:human):
    comment= state['comment']
    msg= f'please look at the user feedback and action accordingly'
    systemmessage=[SystemMessage(content=msg)]
    user_feedback=[HumanMessage(content=comment)]
    state['message']=state['message']+systemmessage+user_feedback
    #msg=state['message']
    result=model_llm.invoke(state['message'])
    state['message']=[result]
    return state
def human_feedback(state: human):
    pass
from langgraph.checkpoint.memory import InMemorySaver
def decision_check(state:human):
    review=state['feedack']
    if review=='Approve':
        return 'approve'
    else:
        return 'reject'
graph=StateGraph(human)
checkpointer = InMemorySaver()
graph.add_node('chatbot',chatbot_dharmendra)
graph.add_node('human_feedback',human_feedback)
graph.add_node('approve',approve)
graph.add_node('reject',reject)
graph.add_edge(START,'chatbot')
graph.add_edge('chatbot','human_feedback')
graph.add_conditional_edges('human_feedback',decision_check)

graph.add_edge('approve',END)
workflow=graph.compile(checkpointer=checkpointer,interrupt_before=["human_feedback"])

    