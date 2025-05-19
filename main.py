import os
import json
import logging
import time
from pathlib import Path
from typing import List

from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from langchain_ollama.llms import OllamaLLM
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate


def extract_structured_pdf(file_path: str):
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.do_cell_matching = True

    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
                backend=PyPdfiumDocumentBackend,
            )
        }
    )

    result = doc_converter.convert(file_path)
    return result


def save_exports(result, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = result.input.file.stem

    (output_dir / f"{filename}.json").write_text(
        json.dumps(result.document.export_to_dict(), indent=2),
        encoding="utf-8"
    )

    (output_dir / f"{filename}.txt").write_text(
        result.document.export_to_text(),
        encoding="utf-8"
    )

    (output_dir / f"{filename}.md").write_text(
        result.document.export_to_markdown(),
        encoding="utf-8"
    )

    (output_dir / f"{filename}.doctags").write_text(
        result.document.export_to_document_tokens(),
        encoding="utf-8"
    )

    print(f"✅ Extracted data saved to {output_dir}")


def create_vector_store(texts: List[str]) -> FAISS:
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L12-v2"
    )
    return FAISS.from_texts(texts, embeddings)


def get_qa_chain(vector_store):
    llm = OllamaLLM(model="gemma:2b")

    prompt_template = """
Use the following context to answer the question.

Context: {context}

Question: {question}

Answer:"""

    prompt = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True,
    )


def main():
    logging.basicConfig(level=logging.INFO)

    file_path = os.path.join("input", "sample-1.pdf")
    output_dir = Path("output")
    result = extract_structured_pdf(file_path)

    save_exports(result, output_dir)

    # Vector store from Markdown
    md_path = output_dir / f"{result.input.file.stem}.md"
    markdown_text = md_path.read_text(encoding="utf-8")

    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=100)
    chunks = splitter.split_text(markdown_text)

    vector_store = create_vector_store(chunks)
    qa_chain = get_qa_chain(vector_store)

    question = "Hey Give me the summary of this pdf document."
    print(f"\n📌 Question: {question}")
    response = qa_chain.invoke({"query": question})
    print(f"\n🧠 Answer: {response['result']}")


if __name__ == "__main__":
    main()
