import sys
from langchain_openai import ChatOpenAI,OpenAIEmbeddings
from langchain_core.messages import HumanMessage,AIMessage,SystemMessage,BaseMessage
from langchain_core.output_parsers import StrOutputParser,PydanticOutputParser
from langchain_core.prompts import PromptTemplate,ChatPromptTemplate
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages
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

def Chatbot(state:bot):
    text =state['messages']
    #messages =[HumanMessage(text)]
    result=model.invoke (text)
    #messages =[AIMessage(result.content)]
        #print ('AI response is ',result.content)
    return {'messages' :[result]}
checkpoint =InMemorySaver()
graph=StateGraph(bot)
graph.add_node('Chatbot',Chatbot)
graph.add_edge(START,'Chatbot')
graph.add_edge('Chatbot',END)
chatbot =graph.compile(checkpointer=checkpoint)
#user_input='what is AI'
#CONFIG = {'configurable': {'thread_id': 'thread-1'}}
#message ={'messages':[HumanMessage(content=user_input)]}
#generator=chatbot.stream(message,config=CONFIG,stream_mode='messages')
#print (type(generator))
#for message_chunk, metadata in generator:
#    print ('content is ',message_chunk.content, end=' ',flush=True)

#messages=['Hi']
#initial_state={'messages':messages}
