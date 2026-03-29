import sys
from langchain_openai import ChatOpenAI,OpenAIEmbeddings
from langchain_core.messages import HumanMessage,AIMessage,SystemMessage
from langchain_core.output_parsers import StrOutputParser,PydanticOutputParser
from langchain_core.prompts import PromptTemplate,ChatPromptTemplate
from langgraph.checkpoint.memory import InMemorySaver
sys.path.insert(1, r'C:\Users\Dharmendra Vartika\LLM\env')
from enviorment import load_env
import os 
load_env()
model =ChatOpenAI()
from langgraph.graph import StateGraph,START, END
from typing import TypedDict,Annotated
import operator
class bot(TypedDict):
    messages :Annotated[list[int], operator.add]

def Chatbot(state:bot):
    while True:
        text =input ('User :')
        messages =[HumanMessage(text)]
        if text=='exit':
            break
        else:
            result=model.invoke (text)
            messages =[AIMessage(result.content)]
            print ('AI response is ',result.content)
    return {'messages' :[messages]}
checkpoint =InMemorySaver()
graph=StateGraph(bot)
graph.add_node('Chatbot',Chatbot)
graph.add_edge(START,'Chatbot')
graph.add_edge('Chatbot',END)
workflow =graph.compile(checkpointer=checkpoint)
messages=['Hi']
initial_state={'messages':messages}
workflow.invoke(initial_state)