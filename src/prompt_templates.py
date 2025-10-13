"""
Enhanced and optimized prompt templates for the RAG pipeline.
This version improves clarity, hallucination resistance, and compatibility with large-context models like openai/gpt-oss-120b.
Maintains identical interfaces and class/method names for backward compatibility.
"""

from typing import List, Dict, Any, Optional
from langchain.prompts import PromptTemplate
import structlog
from transformers import AutoTokenizer
import re
import os

logger = structlog.get_logger(__name__)

# Tokenizer for safe truncation (fallback if unavailable)
try:
    os.environ["PYTHONIOENCODING"] = "utf-8"
    tokenizer = AutoTokenizer.from_pretrained(
        "openai/gpt-oss-120b",
        trust_remote_code=True,
        local_files_only=False
    )
except Exception as e:
    print(f"Tokenizer loading failed: {e}. Falling back to None.")
    tokenizer = None
finally:
    os.environ.pop("PYTHONIOENCODING", None)

SUPERSCRIPT_MAP = {
    "0": "⁰",
    "1": "¹",
    "2": "²",
    "3": "³",
    "4": "⁴",
    "5": "⁵",
    "6": "⁶",
    "7": "⁷",
    "8": "⁸",
    "9": "⁹",
}


class EnhancedPromptTemplates:
    """
    Collection of optimized prompt templates for different RAG scenarios.
    Designed for reasoning-capable LLMs like GPT-OSS-120B.
    """

    BASE_RAG_TEMPLATE = (
        "You are an AI assistant that answers questions using the provided context extracts.\n"
        "Use only information supported by the context. If the answer is not available, say 'The information is not provided in the context.'\n\n"
        "Your answer format:\n"
        "- **Summary**: 1–2 sentences focusing on the question.\n"
        "- **Key Points**: Bullet list of facts directly from the context.\n"
        "- Avoid assumptions or unrelated details.\n\n"
        "Example:\n"
        "Q: What is data drift?\n"
        "A:\n"
        "Summary: Data drift occurs when the statistical properties of input data change over time.\n"
        "Key Points:\n"
        "- It causes model performance degradation.\n"
        "- Can be monitored using KS test or PSI.\n\n"
        "<CONTEXT_START>\n{context}\n<CONTEXT_END>\n\n"
        "Question: {question}\n\nAnswer: "
    )

    SOURCE_ATTRIBUTION_TEMPLATE = (
        "You are an AI assistant that answers questions using the provided documents.\n"
        "Provide a factual and concise answer using only supported information.\n"

        "Cite source names inline in brackets (e.g., [Source: Report A]) only when necessary for clarity.\n"
        "If the answer is not present, reply: 'The information is not provided in the available context.'\n\n"
        "Answer format:\n"
        "- **Summary**: Short overview addressing the question.\n"
        "- **Details**: Bullet list grouped by theme with inline citations.\n\n"
        "Example:\n"
        "Q: What are the effects of inflation?\n"
        "A:\n"
        "Summary: Inflation reduces the purchasing power of money.\n"
        "Details:\n"
        "- Prices of goods and services rise over time [Source: Econ101].\n"
        "- It can benefit borrowers but harm savers [Source: FinanceText].\n\n"
        "<CONTEXT_START>\n{context}\n<CONTEXT_END>\n\nQuestion: {question}\n\nAnswer: "
    )

    CONVERSATIONAL_TEMPLATE = (
        "You are an AI assistant in a conversation about documents.\n"
        "Maintain coherence with the conversation history and accuracy from the context.\n"
        "If a question cannot be answered from context, say so explicitly.\n\n"
        "Previous conversation:\n{chat_history}\n\n"
        "<CONTEXT_START>\n{context}\n<CONTEXT_END>\n\n"
        "Question: {question}\n\nAnswer: "
    )

    SYNTHESIS_TEMPLATE = (
        "You are an AI assistant synthesizing information from multiple sources ({num_sources}).\n"
        "Produce a coherent and factual response using reasoning when needed.\n"
        "If contradictions appear, mention them briefly.\n"
        "Avoid adding a source list; inline references are enough.\n\n"
        "Answer format:\n"
        "- **Summary**: 1–2 sentence overview.\n"
        "- **Insights**: Thematic bullet lists merging information across sources.\n"
        "- **Conflicts**: Note disagreements if present.\n\n"
        "<CONTEXT_START>\n{context}\n<CONTEXT_END>\n\nQuestion: {question}\n\nAnswer: "
    )

    TECHNICAL_TEMPLATE = (
        "You are an AI assistant specializing in technical documentation and code analysis.\n"
        "Respond with accurate, structured technical explanations. Include examples when useful.\n"
        "If context lacks the answer, say so clearly.\n\n"
        "<CONTEXT_START>\n{context}\n<CONTEXT_END>\n\nQuestion: {question}\n\n"
        "Provide a technical response that includes:\n"
        "- **Direct Answer**\n- **Code Example(s)** (if applicable)\n- **Best Practices**\n- **Considerations / Limitations**\n\nAnswer: "
    )

    ANALYSIS_TEMPLATE = (
        "You are an analytical assistant deriving insights from documents.\n"
        "Focus on relationships, implications, and evaluation of key ideas.\n"
        "Provide reasoning before your final answer.\n\n"
        "<CONTEXT_START>\n{context}\n<CONTEXT_END>\n\nQuestion: {question}\n\n"
        "Reasoning:\n- Step 1: Identify key points\n- Step 2: Evaluate implications\n\nFinal Answer:\n"
        "- **Key Findings**\n- **Analysis**\n- **Implications**\n- **Recommendations**\n\nAnswer: "
    )


class PromptManager:
    def __init__(self):
        self.templates = EnhancedPromptTemplates()
        self.template_cache = {}

    def get_prompt_template(
        self, template_type: str = "base", custom_variables: Optional[Dict[str, Any]] = None
    ) -> PromptTemplate:
        cache_key = f"{template_type}_{hash(frozenset(custom_variables.items()) if custom_variables else frozenset())}"
        if cache_key in self.template_cache:
            return self.template_cache[cache_key]

        template_map = {
            "base": self.templates.BASE_RAG_TEMPLATE,
            "source_attribution": self.templates.SOURCE_ATTRIBUTION_TEMPLATE,
            "conversational": self.templates.CONVERSATIONAL_TEMPLATE,
            "synthesis": self.templates.SYNTHESIS_TEMPLATE,
            "technical": self.templates.TECHNICAL_TEMPLATE,
            "analysis": self.templates.ANALYSIS_TEMPLATE,
        }

        if template_type not in template_map:
            logger.warning(f"Unknown template type: {template_type}, defaulting to base.")
            template_type = "base"

        template_string = template_map[template_type]
        input_variables = self._extract_variables(template_string)

        if custom_variables:
            input_variables.extend(custom_variables.keys())
            input_variables = list(set(input_variables))

        prompt_template = PromptTemplate(template=template_string, input_variables=input_variables)
        self.template_cache[cache_key] = prompt_template
        return prompt_template

    @staticmethod
    def _extract_variables(template_string: str) -> List[str]:
        variables = re.findall(r"{(\w+)}", template_string)
        return list(set(variables))

    @staticmethod
    def select_template_by_query_type(question: str, context_length: int = 0) -> str:
        q = question.lower()
        if any(k in q for k in ["code", "function", "api", "error", "algorithm", "class", "debug"]):
            return "technical"
        elif any(k in q for k in ["analyze", "compare", "impact", "trend", "evaluate", "assess"]):
            return "analysis"
        elif context_length > 3:
            return "synthesis"
        elif any(k in q for k in ["who", "what", "when", "where", "statistics", "facts", "source"]):
            return "source_attribution"
        else:
            return "base"

    @staticmethod
    def create_context_string(
        documents: List[Any], include_metadata: bool = True, max_length: int = 4000
    ) -> str:
        context_parts, current_length = [], 0

        for i, doc in enumerate(documents):
            metadata = dict(getattr(doc, "metadata", {}) or {})
            display_name = metadata.get("source_display_name") or metadata.get("source") or f"Document {i+1}"

            lines = [f"### Source: {display_name}"]
            if include_metadata:
                page = metadata.get("page_label") or (
                    f"Page {metadata['page_number']}" if isinstance(metadata.get("page_number"), int) else None
                )
                if page:
                    lines.append(f"Location: {page}")
                if metadata.get("section"):
                    lines.append(f"Section: {metadata['section']}")
            if metadata.get("snippet"):
                lines.append(f"Summary: {metadata['snippet']}")
            lines.append("Content:")
            lines.append(doc.page_content)

            doc_content = "\n".join(lines) + "\n\n"

            if tokenizer:
                token_count = len(tokenizer.encode(doc_content))
                if current_length + token_count > max_length:
                    remaining = max_length - current_length
                    truncated = tokenizer.decode(tokenizer.encode(doc_content)[:remaining]) + "...\n"
                    context_parts.append(truncated)
                    break
                current_length += token_count
            else:
                if current_length + len(doc_content) > max_length:
                    context_parts.append(doc_content[: max_length - current_length - 50] + "...\n")
                    break
                current_length += len(doc_content)

            context_parts.append(doc_content)

        return "".join(context_parts)

    @staticmethod
    def format_chat_history(chat_history: List[Dict[str, str]], max_exchanges: int = 5) -> str:
        if not chat_history:
            return "No previous conversation."

        history = chat_history[-max_exchanges:]
        formatted = []
        for exch in history:
            if "user" in exch and "assistant" in exch:
                formatted.append(f"User: {exch['user']}")
                formatted.append(f"Assistant: {exch['assistant']}")
        return "\n".join(formatted)


prompt_manager = PromptManager()


def get_enhanced_prompt(
    question: str,
    documents: List[Any],
    template_type: Optional[str] = None,
    chat_history: Optional[List[Dict[str, str]]] = None,
    **kwargs,
) -> str:
    if template_type is None:
        template_type = prompt_manager.select_template_by_query_type(question, len(documents))

    template = prompt_manager.get_prompt_template(template_type)
    context = prompt_manager.create_context_string(documents)

    template_vars = {"question": question, "context": context, **kwargs}

    if "chat_history" in template.input_variables:
        template_vars["chat_history"] = prompt_manager.format_chat_history(chat_history or [])

    if "num_sources" in template.input_variables:
        template_vars["num_sources"] = str(len(documents))

    try:
        formatted_prompt = template.format(**template_vars)
        logger.info(
            "Generated optimized prompt",
            template_type=template_type,
            question_length=len(question),
            context_docs=len(documents),
        )
        return formatted_prompt
    except (KeyError, Exception) as e:
        logger.error("Prompt formatting failed", error=str(e), template_type=template_type)
        fallback = prompt_manager.get_prompt_template("base")
        return fallback.format(question=question, context=context)