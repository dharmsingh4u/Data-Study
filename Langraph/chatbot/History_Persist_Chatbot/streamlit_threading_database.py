import streamlit as st
from langchain_core.messages import HumanMessage
from bot_ui_db import chatbot,retrieve_all_threads
import uuid # for generating the unique identifier
from langchain_core.messages import HumanMessage,AIMessage,SystemMessage,BaseMessage

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
        if msg.values.get('messages', [])[0].content:

            return  msg.values.get('messages', [])[0].content
        else:
            'New_Chat: ' +str(thread_id)
    except Exception as e:
        return 'Chat_history :' +str(thread_id)

################################ Session set up###################################

## setting the page 
st.set_page_config(
        page_title="QnA Chatbot", 
)
st.title('Chatbot')
# with st.chat_message('user'):
#     st.text('Hi')

# with st.chat_message('assistant'):
#     st.text('how i can help you..')
if 'chat_threads' not in st.session_state:
        #st.session_state['chat_threads']=[]
        st.session_state['chat_threads']=retrieve_all_threads()
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

is_active = (thread_id == st.session_state.get('thread_id'))
for i in st.session_state['chat_threads'][::-1]:
    #st.sidebar.text(i) ## just for text
    msg=load_conversation_first(i)

    #if st.sidebar.button(str(i)):
    if st.sidebar.button(str(msg)):
        messages=load_conversation(i)
        temp_messages = []

        for msg in messages:
            if isinstance(msg, HumanMessage):
                role='user'
            else:
                role='assistant'
            if ((isinstance(msg, HumanMessage)) or (isinstance(msg, AIMessage))) and msg.content!='' :

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
    #result=chatbot.stream(message,config=CONFIG,stream_mode='messages') ## for handling the stream
    result=chatbot.invoke(message,config=CONFIG)
    result=result['messages'][-1]
    #ai_message=st.write_stream( message_chunk.content for message_chunk, metadata in result)
    # with st.chat_message("assistant"):
    #     def ai_only_stream():
    #         for message_chunk, metadata in chatbot.stream(
    #             {"messages": [HumanMessage(content=user_input)]},
    #             config=CONFIG
    #         ):
    #             if isinstance(message_chunk, AIMessage):
    #                 # yield only assistant tokens
    #                 yield message_chunk.content

    #     ai_message = st.write_stream(ai_only_stream())

    #ai_message=st.write_stream(result)
    #ai_message = result['messages'][-1].content
    #for message_chunk, metadata in result:
    #    print ('content is ',message_chunk.content, end=' ',flush=True)   
    
    with st.chat_message('assitant'):   
        st.text(result.content)
    st.session_state['message_history'].append({'role':'assitant','content':result.content})