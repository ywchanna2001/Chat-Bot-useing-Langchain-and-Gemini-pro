import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os

from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain.vectorstores.faiss import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_text_chunk(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunk):
    embeddings = GoogleGenerativeAIEmbeddings(model="model/embedding-001")
    vector_store = FAISS.from_texts(text_chunk, embedding=embeddings)
    vector_store.save_local("faiss_index")

def get_conversational_chain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide all the details,
    if the answer is not in the provided context just say, "answer is not available in the context", don't provide
    wrong answers\n\n
    Context:\n {context}?\n
    Question:\n{question}\n

    Answer:

    """

    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)

    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model="model/embedding-001")

    new_db = FAISS.load_local("faiss_index", embeddings)
    docs = new_db.similarity_search(user_question)

    chain = get_conversational_chain()

    response = chain(
        {"input_documents": docs, "question": user_question},
        return_only_outputs=True
    )

    print(response)
    st.write("💬 **Reply:**", response["output_text"])

def main():
    st.set_page_config(page_title="Chat With Multiple PDFs 📄", page_icon="📚")
    st.header("Chat With Multiple PDFs using Gemini 🪐")

    st.markdown("""
    <style>
    .big-font {
        font-size:20px !important;
        color: #4CAF50;
    }
    .small-font {
        font-size:14px !important;
        color: #888888;
    }
    </style>
    """, unsafe_allow_html=True)

    user_question = st.text_input("🔍 **Ask a question from the PDF files:**")

    if user_question:
        user_input(user_question)

    with st.sidebar:
        st.title("📚 **Menu:**")
        st.write("Upload your PDF files and click on the submit button:")
        pdf_docs = st.file_uploader("📄 **Upload your PDF files**", accept_multiple_files=True)
        if st.button("Submit & Process"):
            with st.spinner("⚙️ Processing..."):
                raw_text = get_pdf_text(pdf_docs)
                text_chunks = get_text_chunk(raw_text)
                get_vector_store(text_chunks)
                st.success("✅ Done!")

if __name__ == "__main__":
    main()
