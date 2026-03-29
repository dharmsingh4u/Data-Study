from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage
from langchain_core.messages import BaseMessage
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
sys.path.insert(1, r'C:\Users\Dharmendra Vartika\LLM\env')
#sys.path.insert(2, r'C:\Users\Dharmendra Vartika\LLM\langchain_document_loader')
from enviorment import load_env
from langgraph.prebuilt import ToolNode,tools_condition
from typing import TypedDict,Literal,Annotated
from langchain_core.tools import tool
print ('All the import done')
from chat_human import workflow
print ('All workflow')
import streamlit as st
from langchain_core.messages import HumanMessage

st.title('Dharmendra-Chatbot')
st.set_page_config(
        page_title="QnA",
)
with st.chat_message('user'):
    st.text('Hi')

with st.chat_message('assistant'):
    st.text('how i can help you..')
CONFIG = {'configurable': {'thread_id': 'thread-1'}}
#with st.chat_message('assitant'):
#    st.text('how i can help you')
if 'message_history' not in st.session_state:
    st.session_state['message_history']=[]
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])
user_input =st.chat_input('Please type here..')
def handle_user_input(user_input):
    if user_input:
        st.session_state['message_history'].append({'role':'assitant','content':user_input})
        with st.chat_message('user'):
            st.text(user_input)
        #message ={'messages':[HumanMessage(content=user_input)]}
        message ={'message':user_input}
        #message ={'messages':[user_input]}
        #print ('message is -->',message)
        result =workflow.invoke(message,config=CONFIG)
        ai_message = result['message'][-1].content
            
        st.session_state['message_history'].append({'role':'assitant','content':ai_message})
        with st.chat_message('assitant'):
            st.text(ai_message)
            # st.warning("Human review required! Please provide feedback below to continue.")
            # feedback = st.radio("feedback", ["Approve", 'Reject'], horizontal=True)
            # comment = st.text_area("Optional: Add a comment")
            # print ('feedback',feedback)
            # if feedback=='Reject':
            #     workflow.update_state(CONFIG, values={"feedack":feedback,"comment": comment})
            #     result =workflow.invoke(message,config=CONFIG)
            #     ai_message = result['message'][-1].content

            #     st.session_state['message_history'].append({'role':'assitant','content':ai_message})
            #     with st.chat_message('assitant'):
                    
            #         st.text(ai_message)
if user_input:
    handle_user_input(user_input)
