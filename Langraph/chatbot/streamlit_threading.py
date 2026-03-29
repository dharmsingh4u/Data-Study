import streamlit as st
from langchain_core.messages import HumanMessage
from bot_ui import chatbot
import uuid # for generating the unique identifier


######################utlitify function############################

def thread_id():

    id=uuid.uuid4()
    return id


def reset_chat(): ## for loading new conversation
    id=thread_id()
    st.session_state['thread_id']=id
    st.session_state['message_history']=[]
    add_thread(st.session_state['thread_id'])
def add_thread(current_thread):
    if current_thread  not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(current_thread)
def load_conversation(thread_id):
    #CONFIG_Coversation = {'configurable': {'thread_id': thread_id}}
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    return  state.values.get('messages', [])
def load_conversation_first(thread_id):
    #CONFIG_Coversation = {'configurable': {'thread_id': thread_id}}
    try:
        msg = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
        return 'Chat_history:' + msg.values.get('messages', [])[0].content
    except Exception as e:
        return 'Chat_history :' +str(thread_id)

################################ Session set up###################################

## setting the page 
st.set_page_config(
        page_title="QnA Chatbot", 
)
st.title('Dharmendra-Chatbot')
with st.chat_message('user'):
    st.text('Hi')

with st.chat_message('assistant'):
    st.text('how i can help you..')
if 'chat_threads' not in st.session_state:
        st.session_state['chat_threads']=[]
if 'thread_id' not in st.session_state:
    id=thread_id()
    st.session_state['thread_id']=id
    #st.session_state['chat_threads'].append(id)
#print ('current thread is ',st.session_state['thread_id'])
add_thread(st.session_state['thread_id'])
#load_conversation_first(st.session_state['thread_id'])




####################################Sidebar UI#####################################

st.sidebar.title('language chatbot')
#st.sidebar.button('New Chat')
if st.sidebar.button('New Chat'):
    reset_chat()
st.sidebar.header('My conversation')

#for i in st.session_state['chat_threads']:
    #st.sidebar.text(i) ## just for text
#    st.sidebar.button(str(i))# convert text display into button


for i in st.session_state['chat_threads']:
    #st.sidebar.text(i) ## just for text
    msg=load_conversation_first(i)
    #if st.sidebar.button(str(i)):
    if st.sidebar.button(msg):
        messages=load_conversation(i)
        temp_messages = []

        for msg in messages:
            if isinstance(msg, HumanMessage):
                role='user'
            else:
                role='assistant'
            temp_messages.append({'role': role, 'content': msg.content})
        st.session_state['message_history']=temp_messages

#################################################################################
if 'message_history' not in st.session_state:
    st.session_state['message_history']=[]
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])



CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}
#with st.chat_message('assitant'):
#    st.text('how i can help you')

user_input =st.chat_input('Please type here..')
if user_input:

    
    st.session_state['message_history'].append({'role':'assitant','content':user_input})
    with st.chat_message('user'):
        st.text(user_input)
    message ={'messages':[HumanMessage(content=user_input)]}
    #message ={'messages':[user_input]}
    #print ('message is -->',message)
    #result =chatbot.invoke (message,config=CONFIG)
    result=chatbot.stream(message,config=CONFIG,stream_mode='messages') ## for handling the stream
    ai_message=st.write_stream( message_chunk.content for message_chunk, metadata in result)

    #ai_message=st.write_stream(result)
    #ai_message = result['messages'][-1].content
    #for message_chunk, metadata in result:
    #    print ('content is ',message_chunk.content, end=' ',flush=True)   
    st.session_state['message_history'].append({'role':'assitant','content':ai_message})
    with st.chat_message('assitant'):   
        st.text(ai_message)