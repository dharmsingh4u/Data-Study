import streamlit as st
from langchain_core.messages import HumanMessage
from bot_ui import chatbot
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
if user_input:

    
    st.session_state['message_history'].append({'role':'assitant','content':user_input})
    with st.chat_message('user'):
        st.text(user_input)
    message ={'messages':[HumanMessage(content=user_input)]}
    #message ={'messages':[user_input]}
    #print ('message is -->',message)
    result =chatbot.invoke (message,config=CONFIG)
    ai_message = result['messages'][-1].content
        
    st.session_state['message_history'].append({'role':'assitant','content':ai_message})
    with st.chat_message('assitant'):
        st.text(ai_message)