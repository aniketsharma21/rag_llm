import argparse
import sys
import os
import yaml
from .ingest import process_document
from .embed_store import build_vector_store, load_vector_store, get_retriever
from .llm import get_llm
from .config import PROMPTS_DIR, RAW_DATA_DIR

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

def handle_index(file_name):
    """Handles the 'index' command."""
    # If the path is not absolute, assume it's a filename in RAW_DATA_DIR
    if not os.path.isabs(file_name):
        file_path = os.path.join(RAW_DATA_DIR, file_name)
    else:
        file_path = file_name

    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'")
        sys.exit(1)

    print(f"Starting indexing for file: {file_path}")
    chunks = process_document(file_path)
    if chunks:
        build_vector_store(chunks)
    else:
        print("Indexing skipped as the document has not changed or failed to process.")


def load_prompt_template():
    """Loads the RAG prompt template from the YAML file."""
    prompt_path = os.path.join(PROMPTS_DIR, "rag_prompts.yaml")
    with open(prompt_path, 'r') as f:
        prompt_config = yaml.safe_load(f)
    return prompt_config['template']

def handle_query(question):
    """Handles the 'query' command."""
    print(f"\nReceived query: '{question}'")
    vectordb = load_vector_store()
    if not vectordb:
        sys.exit(1)  # Exit if vector store doesn't exist

    retriever = get_retriever(vectordb)
    llm = get_llm()

    # Define a clear and specific prompt template
    template = load_prompt_template()
    prompt = ChatPromptTemplate.from_template(template)

    # Build the RAG chain using LangChain Expression Language (LCEL)
    rag_chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
    )

    # Invoke the chain and print the response
    print("\nGenerating answer...")
    response = rag_chain.invoke(question)
    print("\n--- Answer ---\n")
    print(response)
    print("\n--------------\n")


def main():
    """Main function to parse command-line arguments."""
    parser = argparse.ArgumentParser(description="An Enterprise-Ready RAG Pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # Sub-parser for the 'index' command
    index_parser = subparsers.add_parser("index", help="Index a document into the vector store.")
    index_parser.add_argument("--file", type=str, required=True, help="File name in 'data/raw' or a full path to the file.")

    # Sub-parser for the 'query' command
    query_parser = subparsers.add_parser("query", help="Query the indexed documents.")
    query_parser.add_argument("question", type=str, help="The question to ask.")

    args = parser.parse_args()

    if args.command == "index":
        handle_index(args.file)
    elif args.command == "query":
        handle_query(args.question)


if __name__ == "__main__":
    main()