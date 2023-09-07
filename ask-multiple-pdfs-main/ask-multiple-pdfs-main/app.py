import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceInstructEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from htmlTemplates import css, bot_template, user_template
from langchain.llms import HuggingFaceHub
from pymongo import MongoClient

# Set page configuration (this should be the first Streamlit command)
st.set_page_config(page_title="Chat with PDF", page_icon=":books:")

# MongoDB Configuration
client = MongoClient("mongodb+srv://sowjanya:senapathi@cluster0.6ldr2pk.mongodb.net/cosmos?retryWrites=true&w=majority")
db = client["chat_app"]
collection = db["chats"]

# Define a function to save chat history to MongoDB
def save_chat_to_db(chat_history, chat_name):
    chat_records = []
    for message in chat_history:
        if hasattr(message, 'role') and message.role == 'user':
            chat_records.append({"role": "user", "content": message.content})
        elif hasattr(message, 'role') and message.role == 'assistant':
            chat_records.append({"role": "assistant", "content": message.content})
        else:
            # Handle messages without a 'role' attribute (e.g., plain text messages)
            chat_records.append({"role": "unknown", "content": str(message)})
    
    # Save the chat history with the specified name
    collection.insert_one({"chat_name": chat_name, "chat_history": chat_records})

# Define a function to load chat history from MongoDB
def load_chat_from_db():
    chats = collection.find()
    chat_list = []
    for chat in chats:
        chat_list.append((chat["chat_name"], chat["chat_history"]))
    return chat_list


# Define a function to get text from PDF documents
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

# Define a function to handle user input and conversation
def handle_userinput(user_question, vectorstore):
    if st.session_state.conversation is None:
        # Initialize the conversation if it's None
        st.session_state.conversation = get_conversation_chain(vectorstore)
        st.session_state.chat_history = []

    response = st.session_state.conversation({'question': user_question})

    if st.session_state.chat_history is None:
        st.session_state.chat_history = response['chat_history']
    else:
        st.session_state.chat_history.extend(response['chat_history'])

    # Save user chat to MongoDB with a unique chat name
    chat_count = len(saved_chats)
    chat_name = f"Chat_{chat_count + 1}"
    saved_chats[chat_name] = st.session_state.chat_history
    save_chat_to_db(st.session_state.chat_history, chat_name)

    for i, message in enumerate(st.session_state.chat_history):
        if hasattr(message, 'role') and message.role == 'user':
            st.write(user_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
        elif hasattr(message, 'content'):
            st.write(bot_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
        elif isinstance(message, str):  # Handle plain text messages
            st.write(user_template.replace("{{MSG}}", message), unsafe_allow_html=True)
        # else:
        #     st.write(bot_template.replace("{{MSG}}", str(message)), unsafe_allow_html=True)

# Define a function to split text into chunks
def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

# Define a function to create a vector store from text chunks
def get_vectorstore(text_chunks):
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore

# Define a function to create a conversation chain
def get_conversation_chain(vectorstore):
    llm = ChatOpenAI()
    memory = ConversationBufferMemory(
        memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )
    return conversation_chain

# Define a dictionary to store saved chats
saved_chats = {}

# Load and display existing user chats in the sidebar
with st.sidebar:
    st.subheader("Chats")
    user_chats = load_chat_from_db()
    selected_chat = st.selectbox("Select a Chat", [f"Chat_{idx + 1}" for idx, chat in enumerate(user_chats)])
    
    if selected_chat:
        chat_name, chat_history = next((chat for chat in user_chats if chat[0] == selected_chat), (None, []))
        st.session_state.chat_history = chat_history
        st.write("Chat History:")
        for message in chat_history:
            if isinstance(message, dict) and message.get("role") == "user":
                st.write(f"User: {message.get('content')}")
            elif isinstance(message, dict) and message.get("role") == "assistant":
                st.write(f"Bot: {message.get('content')}")
    
    new_chat_button_key = f"new_chat_button_{st.session_state.get('button_count', 0)}"
    
    if st.button("New Chat", key=new_chat_button_key):
        # Store the current chat under a unique name
        if st.session_state.chat_history:
            chat_count = len(saved_chats)
            chat_name = f"Chat_{chat_count + 1}"
            saved_chats[chat_name] = st.session_state.chat_history
            save_chat_to_db(st.session_state.chat_history, chat_name)
        
        # Start a new chat
        st.session_state.conversation = None
        st.session_state.chat_history = None
        st.session_state.button_count = st.session_state.get('button_count', 0) + 1

# Define the main function
def main():
    load_dotenv()
    st.write(css, unsafe_allow_html=True)

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    st.header("Chat with PDF :books:")
    user_question = st.text_input("Ask a question about your documents:")
    if user_question:
        handle_userinput(user_question, st.session_state.vectorstore)

    with st.sidebar:
        st.subheader("Your documents")
        pdf_docs = st.file_uploader(
            "Upload your PDFs here and click on 'Process'", accept_multiple_files=True)
        
        if st.button("Process"):
            if pdf_docs:
                # Get PDF text
                raw_text = get_pdf_text(pdf_docs)

                # Get text chunks
                text_chunks = get_text_chunks(raw_text)

                # Create vector store
                st.session_state.vectorstore = get_vectorstore(text_chunks)

if __name__ == '__main__':
    main()