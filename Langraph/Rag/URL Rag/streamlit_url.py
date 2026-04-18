from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage,AIMessage
from langchain_core.prompts import ChatPromptTemplate,PromptTemplate,MessagesPlaceholder
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
from langgraph.prebuilt import ToolNode,tools_condition
from langchain_core.tools import tool
#from pydirectoryloader import rag_function
import os 
load_env()
from weburl import URL_selector,URL_loader,retriver_questions
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
import streamlit as st

st.title('Web Insights Chatbot')
def format_docs(retrieved_docs):
  context_text = "\n\n".join(doc.page_content for doc in retrieved_docs)
  return context_text
model =ChatOpenAI(temperature=0,max_completion_tokens=1000,model='gpt-4')
st.set_page_config(
        page_title="QnA",
)

if 'message_history' not in st.session_state:
     st.session_state['message_history']=[]
     print ('inside')
if 'url_uploaded' not in st.session_state:
     st.session_state['url_uploaded']=0
if 'file_path' not in st.session_state:
     st.session_state['file_path']=''
if "url_uploader_key" not in st.session_state:
        st.session_state["url_uploader_key"] = ''
if "url_processed" not in st.session_state:
        st.session_state["url_processed"] = ''
if "url_done" not in st.session_state:
        st.session_state["url_done"] = ''

with st.sidebar:
     input_url=st.text_input(
            "🌐 Introduce a URL", 
            placeholder="https://example.com",
            key= st.session_state["url_uploader_key"],
        )
     process_button = st.button(label="Process")
     if process_button:
          st.session_state["url_uploader_key"]=input_url
          st.session_state["url_processed"]=input_url
          st.toast(f"Document from URL *{input_url}* loaded successfully.", icon="✅")
          #st.text_input("URL uploaded is :",key=st.session_state["url_processed"], value= st.session_state["url_processed"], disabled=True)
          #st.link_button("Go to website",input_url)
     if st.session_state["url_processed"]:
          #st.markdown("check out this [link](%s)" % input_url)
          #st.write("URL processed now is [link](%s)" % st.session_state["url_processed"])
          st.markdown(
    f'URL processed now is <a href="{st.session_state["url_processed"]}" '
    'style="background-color: #ffe08c; padding: 3px 6px; border-radius: 4px; font-weight: bold;">'
    f'{st.session_state["url_processed"]}</a>',
    unsafe_allow_html=True
)
          #st.text_input("URL uploaded is :",key=st.session_state["url_done"], value= st.session_state["url_processed"], disabled=True)
          #url_list=URL_loader(url)
     st.markdown('''
        ### About
        This app is an LLM-powered chatbot built using:
        - [Streamlit](https://streamlit.io/)
        - [LangChain](https://python.langchain.com/)
        - [OpenAI gpt-3.5-turbo](https://platform.openai.com/docs/models/gpt-3-5)
        - [Azure OpenAI Tutorial](https://techcommunity.microsoft.com/t5/startups-at-microsoft/build-a-chatbot-to-query-your-documentation-using-langchain-and/ba-p/3833134)
        - [Git Hub](https://github.com/dharmsingh4u/Study)
        ''')
     st.write("Made ❤️ by Dharmendra")
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])
model=ChatOpenAI(model='gpt-4o',temperature=0, max_completion_tokens=2000)
prompt=ChatPromptTemplate.from_messages([('system','You are a Education education counsellor who helps students to resolve queries'),('human','Answer this quesiton {question} from the provided context only and here is the context {context} and if you dont the please say dont know')])
input = st.chat_input("What would you like to know from this URL")
if input and  st.session_state["url_uploader_key"]:
     st.session_state['message_history'].append({'role':'user','content':input})
     #chat_history.append(HumanMessage(content=input))
     with st.chat_message('user'):
        st.text(input)
     url_list=URL_selector(model,input,st.session_state["url_uploader_key"])
     retriever=URL_loader(url_list)
     parallel_chain=RunnableParallel({'question':RunnablePassthrough(),'context':retriever|retriver_questions})
     parser=StrOutputParser()
     final_chain=parallel_chain | prompt|model|parser
     result=final_chain.invoke(input)
     #result=final_chain.invoke({'input':input,'chat_history':chat_history})
     st.session_state['message_history'].append({'role':'assitant','content':result})
     #chat_history.append(AIMessage(content=result))
     with st.chat_message('assitant'):

        st.text(result)



