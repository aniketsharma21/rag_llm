"""
main.py

Command-line entry point for the RAG pipeline. Handles document indexing and querying via CLI commands.
Coordinates ingestion, embedding, retrieval, and LLM-based answer generation.

Usage:
    Run this module as a script to index documents or query the RAG system.
"""
import argparse
import sys
import os
import yaml
from .ingest import process_document
from .embed_store import build_vector_store, load_vector_store, get_retriever
from .llm import get_llm
from .config import PROMPTS_DIR, RAW_DATA_DIR, logger

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

def handle_index(file_name):
    """
    Handles the 'index' CLI command to ingest and index a document.

    Args:
        file_name (str): Name or path of the document to index.
    """
    if not os.path.isabs(file_name):
        file_path = os.path.join(RAW_DATA_DIR, file_name)
    else:
        file_path = file_name

    if not os.path.exists(file_path):
        logger.error(f"File not found at '{file_path}'")
        sys.exit(1)

    logger.info(f"Starting indexing for file: {file_path}")
    chunks = process_document(file_path)
    if chunks:
        build_vector_store(chunks)
    else:
        logger.warning("Indexing skipped as the document has not changed or failed to process.")

def load_prompt_template():
    """
    Loads the RAG prompt template from the YAML file in the prompts directory.

    Returns:
        str: The prompt template string.
    """
    prompt_path = os.path.join(PROMPTS_DIR, "rag_prompts.yaml")
    with open(prompt_path, 'r') as f:
        prompt_config = yaml.safe_load(f)
    return prompt_config['template']

def handle_query(question):
    """
    Handles the 'query' CLI command to answer a question using the indexed documents and LLM.

    Args:
        question (str): The user's question.
    """
    logger.info(f"Received query: '{question}'")
    vectordb = load_vector_store()
    if not vectordb:
        logger.error("Vector store doesn't exist. Run 'index' first.")
        sys.exit(1)

    retriever = get_retriever(vectordb)
    llm = get_llm()
    template = load_prompt_template()
    prompt = ChatPromptTemplate.from_template(template)
    rag_chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
    )
    logger.info("Generating answer...")
    response = rag_chain.invoke(question)
    logger.info("--- Answer ---\n%s\n--------------", response)

def main():
    parser = argparse.ArgumentParser(description="An Enterprise-Ready RAG Pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")
    index_parser = subparsers.add_parser("index", help="Index a document into the vector store.")
    index_parser.add_argument("--file", type=str, required=True, help="File name in 'data/raw' or a full path to the file.")
    query_parser = subparsers.add_parser("query", help="Query the indexed documents.")
    query_parser.add_argument("question", type=str, help="The question to ask.")
    args = parser.parse_args()
    if args.command == "index":
        handle_index(args.file)
    elif args.command == "query":
        handle_query(args.question)


if __name__ == "__main__":
    main()