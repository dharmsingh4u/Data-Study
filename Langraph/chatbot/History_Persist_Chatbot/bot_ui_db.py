import sys
from langchain_openai import ChatOpenAI,OpenAIEmbeddings
from langchain_core.messages import HumanMessage,AIMessage,SystemMessage,BaseMessage
from langchain_core.output_parsers import StrOutputParser,PydanticOutputParser
from langchain_core.prompts import PromptTemplate,ChatPromptTemplate
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
sys.path.insert(1, r'D:\Notebooks\LLM\env')
from enviorment import load_env
import os 
load_env()
model =ChatOpenAI()
from langgraph.graph import StateGraph,START, END
from typing import TypedDict,Annotated
from langchain_community.tools.tavily_search import TavilySearchResults
import operator
from langgraph.prebuilt import ToolNode, tools_condition
search_Tavily = TavilySearchResults(max_results=1)
tools = [search_Tavily]
llm_with_tools = model.bind_tools(tools)
tool_node = ToolNode(tools)
class bot(TypedDict):
    messages :Annotated[list[BaseMessage],add_messages]


def Chatbot(state:bot):
    text =state['messages']
    #messages =[HumanMessage(text)]
    result=llm_with_tools.invoke (text)
    #messages =[AIMessage(result.content)]
        #print ('AI response is ',result.content)
    return {'messages' :[result]}
#checkpoint =InMemorySaver()
conn = sqlite3.connect(database='chatbot_dharmendra1.db', check_same_thread=False)
# Checkpointer=InMemorySaver()
Checkpointer = SqliteSaver(conn=conn)
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
# def retrieve_all_threads():
#     threads = set()

#     for cp in Checkpointer.list(None):
#         thread_id = cp.config["configurable"]["thread_id"]

#         chk = cp.checkpoint or {}

#         has_content = (
#             bool(chk.get("writes")) or
#             bool(chk.get("state")) or
#             bool(chk.get("metadata"))
#         )

#         if has_content:
#             threads.add(thread_id)

#     return list(threads)


# def retrieve_all_threads():
#     """
#     Retrieves thread IDs that have at least one AIMessage or HumanMessage.
    
#     Args:
#         checkpointer: The Checkpointer instance (e.g., InMemorySaver, SqliteSaver).
        
#     Returns:
#         A list of thread IDs.
#     """
#     all_threads_with_messages = set()
    
#     # 1. Get the latest checkpoint metadata for all threads
#     # Note: list(None) or list({}) returns all threads for the current Checkpointer
#     all_checkpoints = Checkpointer.list(None)

#     for checkpoint in all_checkpoints:
#         thread_id = checkpoint.config['configurable']['thread_id']
        
#         # 2. Load the full state for the latest checkpoint of this thread
#         # We need the full state to inspect the 'messages'
#         config = {"configurable": {"thread_id": thread_id}}
        
#         # get_state returns StateSnapshot (or None if thread is empty/deleted)
#         state_snapshot = Checkpointer.get_state(config) 

#         if state_snapshot and state_snapshot.values:
#             # The actual messages are usually stored in the 'messages' key of the state values
#             messages = state_snapshot.values.get('messages', [])
            
#             # 3. Check if any message is an AIMessage or HumanMessage
#             has_messages = any(
#                 isinstance(msg, (AIMessage, HumanMessage)) for msg in messages
#             )
            
#             if has_messages:
#                 all_threads_with_messages.add(thread_id)

#     return list(all_threads_with_messages)

