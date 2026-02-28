import streamlit as st
from backend import agent, retrive_all_threads
from langchain_core.messages import HumanMessage, AIMessage
import uuid
from dotenv import load_dotenv

load_dotenv()
#********************************************************** utility functions *******************************************

def create_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

def new_chat():
    thread_id = create_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(thread_id)
    st.session_state['message_history'] = []
 

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_thread']:
        st.session_state['chat_thread'].append(thread_id)

def load_conversation(thread_id):
    config_ = {"configurable":{"thread_id":thread_id}}
    messages = agent.get_state(config=config_).values
    return messages.get("messages",[])  


#************************************************************ session set up ********************************************

if "message_history" not in st.session_state:
    st.session_state['message_history'] = []

if "user_input" not in st.session_state:
    st.session_state['user_input'] = False

if "chat_thread" not in st.session_state:
    st.session_state["chat_thread"] = retrive_all_threads()


if "thread_id" not in st.session_state:
    st.session_state['thread_id'] = create_thread_id()
    add_thread(st.session_state['thread_id'])
   


# ***************************************************************** sidebar ui ******************************************

st.sidebar.title("NEXUS_DeepAgent")

if st.sidebar.button("New chat"):
    new_chat()

st.sidebar.header("My Conversations")

for thread_id in st.session_state['chat_thread'][::-1]:

    label = "Name is not declared"

    if st.sidebar.button(label=label ,key=str(thread_id)):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)
        
        temp = []

        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = 'user'
            else :
                role = 'assistant'
            temp.append({'role':role,"content":msg.content})    
        st.session_state['message_history'] = temp
        


# *********************************************************** main ui **************************************************

config = {'configurable':{"thread_id":st.session_state['thread_id']},
          "metadata":{"thread_id":st.session_state['thread_id']},
          "run_name":"model_call"  }



for msg in st.session_state['message_history']:
    with st.chat_message(msg['role']):
        st.text(msg['content'])        


user_input = st.chat_input("Type here...") 

if user_input:
    st.session_state['user_input'] = True


if st.session_state['user_input']:

    st.session_state['message_history'].append({'role':'user','content':user_input})
    with st.chat_message('user'):
        st.text(user_input)

    with st.chat_message('assistant'):
        def ai_stream():
            for msg, _ in agent.stream(
                {"messages":[HumanMessage(user_input)]},
                config=config,
                stream_mode = "messages"
            ):
                if isinstance(msg,AIMessage):
                    yield msg.content

        ai_message = st.write_stream(ai_stream())

    st.session_state['message_history'].append({'role':'assistant','content':ai_message})
    st.session_state['user_input'] = False
    
 



   