from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate,PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import DirectoryLoader,PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma, FAISS
from langchain_openai import ChatOpenAI,OpenAIEmbeddings
from langgraph.graph import StateGraph,START, END,MessagesState
from typing import TypedDict,Annotated,Literal
import os 
import sys
sys.path.insert(1, r'D:\Notebooks\LLM\env')
#sys.path.insert(2, r'D:\Notebooks\LLM\langchain_document_loader')
from enviorment import load_env
load_env()
import logging
#logging.basicConfig(level=logging.DEBUG)
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy import create_engine
from langchain_community.vectorstores.pgvector import PGVector
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import ToolNode, tools_condition
import streamlit as st
from langchain_community.tools import DuckDuckGoSearchRun
search_tool = DuckDuckGoSearchRun()
os.environ['LANGSMITH_PROJECT']='Persistant_memory_langraph'
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
VECTOR_CONNECTION_STRING = "postgresql+psycopg2://postgres:mysecretpassword@localhost:5432/vector"

# ✅ PostgresSaver (psycopg2 DSN)
model = ChatOpenAI(model="gpt-4o-mini", temperature=0.6,max_completion_tokens=1000)
CHECKPOINT_CONNECTION_STRING = "dbname=vector user=postgres password=mysecretpassword host=localhost port=5432"
search_Tavily = TavilySearchResults(max_results=1)
COLLECTION_NAME = "chat_memory"
tool=[search_tool]
#prompt ='can you get ticker symbol only for the Quantum-Si (QSI) stock'
llm_with_tools = model.bind_tools(tool)
tool_node = ToolNode(tool)
# ✅ Initialize vector store (needs SQLAlchemy URL)
vector_store = PGVector(
    connection_string=VECTOR_CONNECTION_STRING,
    collection_name=COLLECTION_NAME,
    embedding_function=embeddings,
)
st.title('Postgres-Backed AI Chat')
with st.chat_message('user'):
    st.text('Hi')

with st.chat_message('assistant'):
    st.text('how i can help you..')
with st.sidebar:
    st.markdown('''
        ### About
        This app is an LLM-powered chatbot built using:
        - [Streamlit](https://streamlit.io/)
        - [PostgreSQL](https://www.postgresql.org/)
        - [LangChain](https://python.langchain.com/)
        - [OpenAI gpt-3.5-turbo](https://platform.openai.com/docs/models/gpt-3-5)
        - [Azure OpenAI Tutorial](https://techcommunity.microsoft.com/t5/startups-at-microsoft/build-a-chatbot-to-query-your-documentation-using-langchain-and/ba-p/3833134)
        - [Git Hub](https://github.com/dharmsingh4u/Study)
        ''')
    st.write("Made ❤️ by Dharmendra")
with PostgresSaver.from_conn_string(CHECKPOINT_CONNECTION_STRING) as checkpointer:
    checkpointer.setup()

    def agent_execution(state: MessagesState):
        user_input = state["messages"]
    # context = state.get("retrieved_context", "")

    # prompt = f"""
    # You are a helpful assistant.

    # Conversation memory:
    # {context}

    # User: {user_input}
    # Assistant:
    # """

        response = llm_with_tools.invoke(user_input)
        assistant_reply = response.content

        # Save memory to pgvector
        vector_store.add_texts(
        texts=[f"user_message: {user_input}\nAssistant: {assistant_reply}"],metadatas=[{}]
    )
        return {'messages' :[response]}
    graph=StateGraph(MessagesState)
#graph.add_node('retrieve_memory',retrieve_memory)
    graph.add_node('agent_execution',agent_execution)
    graph.add_node('tools',tool_node)

    graph.add_edge(START,'agent_execution')
    graph.add_conditional_edges('agent_execution',tools_condition)
    #graph.add_edge('retrieve_memory','agent_execution')
    graph.add_edge('agent_execution',END)
    thread_id='chat-1'
    workflow = graph.compile(checkpointer=checkpointer)
    CONFIG = {'configurable': {'thread_id': thread_id}}
    user_input =st.chat_input('Please type here..')
    if 'message_history' not in st.session_state:
        st.session_state['message_history']=[]
    for message in st.session_state['message_history']:
        with st.chat_message(message['role']):
            st.text(message['content'])
    if user_input:
        st.session_state['message_history'].append({'role':'assitant','content':user_input})
        with st.chat_message('user'):
            st.text(user_input)
        with PostgresSaver.from_conn_string(CHECKPOINT_CONNECTION_STRING) as checkpointer:
            checkpointer.setup() 
            initial_state ={'messages':[HumanMessage(content=user_input)]}
            result=workflow.invoke(initial_state,config=CONFIG)
            ai_message = result['messages'][-1].content
            st.session_state['message_history'].append({'role':'assitant','content':ai_message})
            with st.chat_message('assitant'):
                st.text(ai_message)
    # user_input='my name is dharmendra'
    # thread_id='chat_thread_52'
    # initial_state ={'messages':[HumanMessage(content=user_input)]}
    # result = workflow.invoke(initial_state, config={"configurable": {"thread_id": thread_id}})
    # print("AI:" ,result['messages'][-1].content)