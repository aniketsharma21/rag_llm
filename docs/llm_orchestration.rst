LLM Orchestration
==================

The LLM orchestration layer coordinates provider selection, prompt construction, and output normalization.

.. mermaid::

   graph TD
       A[Query] --> B{RAGService};
       B --> C[Get or Create Conversation];
       C --> D{EnhancedRAGChain};
       D --> E[Select Prompt Template];
       E --> F{Get LLM Provider};
       F --> G[Invoke LLM];
       G --> H[Process Response];
       H --> I[Calculate Confidence Score];
       I --> J[Format Citations];
       J --> K[Persist Conversation];
       K --> L[Return Response];

Provider Registry
-----------------

`src/llm.py` registers providers via `LLMProviderRegistry`, supporting Groq by default with optional OpenAI fallback:

.. code-block:: python
   :caption: Provider registration snippet

   registry = LLMProviderRegistry()
   registry.register("groq", factory=_create_groq_llm, health_check=_groq_health_check)
   registry.register("openai", factory=_create_openai_llm, health_check=_openai_health_check)

`get_llm()` accepts overrides for `provider`, `model`, `temperature`, `request_timeout`, and `max_retries`, sourcing defaults from `src/config.py`. All instances are cached per option signature to avoid repeated client instantiation.

Enhanced RAG Chain
------------------

`EnhancedRAGChain` encapsulates advanced retrieval, prompt management, and output shaping. It is the core component of the LLM orchestration layer, responsible for generating a response from a given query and context.

.. code-block:: python
   :caption: `EnhancedRAGChain.query()` abridged

   result = chain.query(
       question=question,
       template_type=None,
       k=5,
       include_sources=True,
       chat_history=chat_history,
   )

   prompt = get_enhanced_prompt(...)
   llm = self._resolve_llm(llm_overrides)
   response = llm.invoke(prompt)

   sources = self._extract_source_info(documents)
   confidence_score = self._calculate_confidence_score(answer, documents)
   observe_rag_generation(... token_usage=token_usage)

   return {
       "answer": answer,
       "sources": sources,
       "confidence_score": confidence_score,
       "template_used": template_type,
       "num_sources": len(documents),
       "retrieval_stats": self.retriever.get_retrieval_stats(),
   }

Conversation Persistence
------------------------

`RAGService.generate_response()` persists chat transcripts through `ConversationRepository` when a `conversation_id` is supplied. Messages are appended in `append_to_conversation()` with both user and assistant payloads, including rendered sources.

Prompt Selection
----------------

`PromptManager.select_template_by_query_type()` inspects the query to classify it as `technical`, `analysis`, `synthesis`, `source_attribution`, or default `base`. This classification is based on a set of keywords and heuristics. `get_enhanced_prompt()` then formats context strings (including metadata like `page_number` and `snippet`) and optionally injects chat history for conversational templates.

Confidence & Citations
----------------------

*   **Confidence Scoring**: `EnhancedRAGChain._calculate_confidence_score()` produces a score between 0 and 1, reflecting the system's confidence in the generated answer. The score is based on the number and relevance of the retrieved documents, as well as the clarity of the LLM's response.
*   **Citation Formatting**: The system uses a two-stage process for citations. First, `replace_bracket_citations()` converts intermediate `[1]` style references into a structured format. Then, `src.utils.source_formatting.apply_superscript_citations()` replaces these with Unicode superscripts for a clean, academic-style presentation in the frontend.

Performance Instrumentation
---------------------------

`observe_rag_generation()` records latency and token usage metrics per provider/model. Coupled with `observe_rag_retrieval()` this enables dashboards correlating response times with prompt complexity and retrieval hit rates.
