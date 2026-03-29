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
import os 
import uuid
load_env()
from Pgvector import create_workflow,init_vector_store,CHECKPOINT_CONNECTION_STRING
from langchain_core.output_parsers import StrOutputParser
import streamlit as st
from langchain_community.vectorstores.pgvector import PGVector
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_community.tools import DuckDuckGoSearchRun
st.title('Postgres-Backed AI Chat')

with st.chat_message('user'):
    st.text('Hi')

with st.chat_message('assistant'):
    st.text('how i can help you..')


if "vector_store" not in st.session_state:
    st.session_state.vector_store = init_vector_store()

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
if 'message_history' not in st.session_state:
    st.session_state['message_history']=[]
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])
user_input =st.chat_input('Please type here..')
if "thread_id" not in st.session_state:
    st.session_state.thread_id = "chat_thread_streamlit"
thread_id=st.session_state.thread_id
CONFIG = {'configurable': {'thread_id': thread_id}}
if user_input:
    st.session_state['message_history'].append({'role':'assitant','content':user_input})
    with st.chat_message('user'):
        st.text(user_input)
    with PostgresSaver.from_conn_string(CHECKPOINT_CONNECTION_STRING) as checkpointer:
        checkpointer.setup() 
        initial_state ={'messages':[HumanMessage(content=user_input)]}
        result=st.session_state.workflow.invoke.invoke(initial_state,config=CONFIG)
        ai_message = result['messages'][-1].content
        st.session_state['message_history'].append({'role':'assitant','content':ai_message})
        with st.chat_message('assitant'):
            st.text(ai_message)

