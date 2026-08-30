import os
import asyncio
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import context_precision, faithfulness, answer_relevancy
from src.llm import EnhancedRAGChain
from src.embed_store import load_vector_store
from src.logging_config import get_logger

logger = get_logger(__name__)

# Sample dataset for evaluation
SAMPLE_DATA = {
    "question": [
        "What is data drift?",
        "How do you monitor data drift?"
    ],
    "ground_truth": [
        "Data drift occurs when the statistical properties of the target variable, which the model is trying to predict, change over time in unforeseen ways. This causes model predictions to become less accurate.",
        "Data drift can be monitored using statistical tests like the Kolmogorov-Smirnov (K-S) test, Population Stability Index (PSI), or by comparing the distributions of features in the training data vs inference data."
    ]
}

async def run_evaluation():
    logger.info("Initializing Ragas Evaluation...")
    
    # Load existing vector store (Make sure you have ingested some relevant docs first!)
    vector_store = load_vector_store()
    if not vector_store:
        logger.error("No vector store found. Please ingest documents before running evaluation.")
        return

    # Initialize RAG Chain
    # We pass empty docs list for BM25 since we're just testing the vector retrieval part here for simplicity
    rag_chain = EnhancedRAGChain(vector_store, documents=[])

    answers = []
    contexts = []

    logger.info("Generating answers for evaluation dataset...")
    for question in SAMPLE_DATA["question"]:
        try:
            # Query the RAG pipeline
            result = rag_chain.query(question=question, k=3, include_sources=True, conversation_context=False)
            answers.append(result["answer"])
            
            # Extract contexts
            context_list = [source["content"] for source in result.get("sources", [])]
            contexts.append(context_list)
        except Exception as e:
            logger.error(f"Failed to process query '{question}': {e}")
            answers.append("Error generating answer")
            contexts.append([])

    # Prepare dataset for Ragas
    data = {
        "question": SAMPLE_DATA["question"],
        "answer": answers,
        "contexts": contexts,
        "ground_truth": SAMPLE_DATA["ground_truth"]
    }
    dataset = Dataset.from_dict(data)

    logger.info("Running Ragas metrics (Faithfulness, Answer Relevancy, Context Precision)...")
    try:
        # Note: Ragas uses the LLM configured in the environment (e.g., OPENAI_API_KEY) by default.
        # Ensure you have the necessary API keys set in your .env
        result = evaluate(
            dataset=dataset,
            metrics=[
                context_precision,
                faithfulness,
                answer_relevancy,
            ],
        )
        logger.info("Evaluation Complete!")
        print("\n--- Evaluation Results ---")
        print(result)
        
    except Exception as e:
        logger.error(f"Ragas evaluation failed: {e}")

if __name__ == "__main__":
    # Ensure OPENAI_API_KEY is set in environment for default Ragas metrics
    # Alternatively, you can pass custom LLMs to Ragas metrics if using Groq
    asyncio.run(run_evaluation())
