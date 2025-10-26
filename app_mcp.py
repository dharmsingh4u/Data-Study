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
import streamlit as st
from langgraph.graph import StateGraph,START, END
from typing import TypedDict,Annotated,Literal
import operator
import asyncio
import os
os.environ["ANONYMIZED_TELEMETRY"] = "false"
#from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient
st.title('Dharmendra-Chatbot')
st.set_page_config(
        page_title="QnA",
)
with st.chat_message('user'):
    st.text('Hi')

with st.chat_message('assistant'):
    st.text('how i can help you..')
#CONFIG = {'configurable': {'thread_id': 'thread-1'}}
#with st.chat_message('assitant'):
#    st.text('how i can help you')
if 'message_history' not in st.session_state:
    st.session_state['message_history']=[]
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])
async def main():
    # Load environment variables

    # Create MCPClient from config file
   
    client = MCPClient.from_config_file('browser.json')
    #client = MCPClient.from_dict(config)
    #print ('client is ',client)
    # Create LLM
    model =ChatOpenAI(model="gpt-4o")
    llm = model
    # Alternative models:
    # llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")
    # llm = ChatGroq(model="llama3-8b-8192")

    # Create agent with the client
    agent = MCPAgent(llm=llm, client=client, max_steps=30,disallowed_tools=["file_system", "network"])
    #print ('agent is ',agent)
    # Run the querycls
    user_input =st.chat_input('Please type here..')
    if user_input:
        st.session_state['message_history'].append({'role':'user','content':user_input})
        with st.chat_message('user'):
            st.text(user_input)
        message ={'messages':[HumanMessage(content=user_input)]}
        #text="can you highlight key risk for buying apple stock by looking at the stock price history from past 1 year"
        result = await agent.run(user_input)
        #print ('result is ',result) 
        ai_message = result
        st.session_state['message_history'].append({'role':'assitant','content':ai_message})
        with st.chat_message('assitant'):
            st.text(ai_message)

if __name__ == "__main__":
    asyncio.run(main())