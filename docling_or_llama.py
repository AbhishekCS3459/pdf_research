import os
from typing import List
from docling.document_converter import DocumentConverter
from langchain_ollama.llms import OllamaLLM
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# Get the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

def extract_pdf_content(file_path) -> str:
    converter = DocumentConverter()
    result = converter.convert(file_path)
    return result.document.export_to_markdown()

def create_vector_store(texts: List[str]) -> FAISS:
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L12-v2"
    )
    vector_store = FAISS.from_texts(texts, embeddings)
    return vector_store

def get_qa_chain(vector_store):
    # Updated model name from "llama3.1" to "llama3"
    llm = OllamaLLM(model="llama3")

    prompt_template = """
    Use the following pieces of context to answer the question at the end.

    Check context very carefully and reference and try to make sense of that before responding.
    If you don't know the answer, just say you don't know.
    Don't try to make up an answer.
    Answer must be to the point.
    Think step-by-step.

    Context: {context}

    Question: {question}

    Answer:"""

    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
        chain_type_kwargs={"prompt": PROMPT},
        return_source_documents=True,
    )
    return qa_chain

def main():
    file_path = project_root + "/input/sample-4.pdf"  # Adjust path as needed

    structured_content = extract_pdf_content(file_path)
    with open("output.txt", 'w') as file:
        file.write(structured_content)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=100,
        is_separator_regex=False
    )
    text_chunks = text_splitter.split_text(structured_content)

    vector_store = create_vector_store(text_chunks)
    qa_chain = get_qa_chain(vector_store)

    question = "What is Embodied Intelligence?"  # Customize this
    print(f"\nQuestion: {question}")
    response = qa_chain.invoke({"query": question})
    print(f"\nAnswer: {response['result']}")

if __name__ == "__main__":
    main()
