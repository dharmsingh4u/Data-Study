import streamlit as st
from langchain_core.messages import HumanMessage
from agents_stock import workflow
st.title('Stock analyzer')
st.set_page_config(
        page_title="Stock-Analyzer Agent",
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
if user_input:

    
    st.session_state['message_history'].append({'role':'assitant','content':user_input})
    with st.chat_message('user'):
        st.text(user_input)
    #message ={'messages':[HumanMessage(content=user_input)]}
    prompt =user_input
    #message ={'messages':[user_input]}
    #print ('message is -->',message)
    #result =chatbot.invoke (message,config=CONFIG)
    initial_state={'prompt':prompt}
    result =workflow.invoke (initial_state)
    ai_message = result['summary']
    #result['Confidence_score'][-1].content
        
    st.session_state['message_history'].append({'role':'assitant','content':ai_message})
    with st.chat_message('assitant'):
        st.text(ai_message)