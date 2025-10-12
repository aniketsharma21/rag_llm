"""
Enhanced prompt templates for the RAG pipeline with better context management.
Provides specialized prompts for different types of queries and document types.
"""

from typing import List, Dict, Any, Optional
from langchain.prompts import PromptTemplate
import structlog

logger = structlog.get_logger(__name__)


SUPERSCRIPT_MAP = {
    "0": "\u2070",
    "1": "\u00B9",
    "2": "\u00B2",
    "3": "\u00B3",
    "4": "\u2074",
    "5": "\u2075",
    "6": "\u2076",
    "7": "\u2077",
    "8": "\u2078",
    "9": "\u2079",
}


class EnhancedPromptTemplates:
    """
    Collection of enhanced prompt templates for different RAG scenarios.
    """
    
    # Base RAG prompt with improved context handling
    BASE_RAG_TEMPLATE = """You are an AI assistant that answers questions using the supplied source extracts.
Use the context to answer the question. If the answer is not supported, explicitly state that it is unknown.

When responding:
1. Begin with a short **Summary** (1–2 sentences) focused solely on the question’s topic.
2. Follow with grouped bullet lists of key points, keeping each bullet concise and directly relevant to the question.
3. Explicitly discard any context that does not help answer the question (e.g., biographical details when asked about a concept).
4. Reference source names inline only when needed for clarity (e.g., [Source: <name>]) and only for facts used in the answer.
5. Do **not** include a dedicated section titled “Sources” or lists of source names in the answer; the interface already surfaces supporting documents.

Context Digest:
{context}

Question: {question}

Answer: """

    # Enhanced template with source attribution
    SOURCE_ATTRIBUTION_TEMPLATE = """You are an AI assistant that provides detailed answers with clear, readable source attribution.

Use the context to answer the question and follow these rules:
- Start with a concise **Summary** that addresses the question directly.
- Present key details in short bullet lists grouped by theme; exclude any information that does not advance the answer.
- When citing evidence, reference the source name inline only when it materially improves clarity and avoid reiterating full source lists.
- Do **not** append a separate section titled “Sources” or restate file names; the client application will render supporting documents.

Context Digest:
{context}

Question: {question}

Answer: """

    # Conversational template with history
    CONVERSATIONAL_TEMPLATE = """You are an AI assistant engaged in a conversation about documents. 
You have access to relevant context and the conversation history.

Previous conversation:
{chat_history}

Current context documents:
{context}

Current question: {question}

Provide a natural, conversational response that:
1. Acknowledges the conversation history when relevant
2. Uses the context documents to provide accurate information
3. Maintains consistency with previous responses
4. Asks clarifying questions if needed

Answer: """

    # Multi-document synthesis template
    SYNTHESIS_TEMPLATE = """You are an AI assistant that synthesizes information from multiple sources.

Context from {num_sources} sources is provided. Produce a reader-friendly response that:
1. Opens with a **Summary** paragraph (1–2 sentences) tightly focused on the question’s subject.
2. Organises insights into themed sections with bullet lists, including only statements that materially answer the question.
   - Group shared findings together and mention supporting source names in brackets when essential.
   - Call out unique insights or disagreements briefly.
3. Avoid adding any section titled “Sources” or restating document lists; the application surfaces supporting documents automatically.

Context Overview:
{context}

Question: {question}

Answer: """

    # Technical documentation template
    TECHNICAL_TEMPLATE = """You are an AI assistant specialized in technical documentation and code analysis.

Based on the provided technical context, answer the question with:
1. Technical accuracy and precision
2. Code examples when relevant
3. Best practices and recommendations
4. Potential pitfalls or considerations

Technical Context:
{context}

Question: {question}

Provide a technical response that includes:
- **Direct Answer**: [Clear, technical response]
- **Code Examples**: [If applicable, provide code snippets]
- **Best Practices**: [Relevant recommendations]
- **Considerations**: [Important notes, limitations, or warnings]

Answer: """

    # Summary and analysis template
    ANALYSIS_TEMPLATE = """You are an AI assistant that provides analytical insights from document content.

Analyze the provided context to answer the question. Focus on:
1. Key insights and patterns
2. Implications and consequences  
3. Relationships between concepts
4. Critical analysis and evaluation

Context for analysis:
{context}

Question: {question}

Provide an analytical response with:
- **Key Findings**: [Main insights from the context]
- **Analysis**: [Your interpretation and evaluation]
- **Implications**: [What this means or suggests]
- **Recommendations**: [If applicable, suggested actions or considerations]

Answer: """


class PromptManager:
    """
    Manages prompt selection and customization based on query type and context.
    """
    
    def __init__(self):
        self.templates = EnhancedPromptTemplates()
        self.template_cache = {}
        
    def get_prompt_template(
        self, 
        template_type: str = "base",
        custom_variables: Optional[Dict[str, Any]] = None
    ) -> PromptTemplate:
        """
        Get a prompt template based on the specified type.
        
        Args:
            template_type: Type of template to use
            custom_variables: Additional variables for template customization
            
        Returns:
            PromptTemplate instance
        """
        # Use frozenset(custom_variables.items()) to ensure consistent hashing
        cache_key = f"{template_type}_{hash(frozenset(custom_variables.items()) if custom_variables else frozenset())}"

        if cache_key in self.template_cache:
            return self.template_cache[cache_key]
        
        template_map = {
            "base": self.templates.BASE_RAG_TEMPLATE,
            "source_attribution": self.templates.SOURCE_ATTRIBUTION_TEMPLATE,
            "conversational": self.templates.CONVERSATIONAL_TEMPLATE,
            "synthesis": self.templates.SYNTHESIS_TEMPLATE,
            "technical": self.templates.TECHNICAL_TEMPLATE,
            "analysis": self.templates.ANALYSIS_TEMPLATE
        }
        
        if template_type not in template_map:
            logger.warning(f"Unknown template type: {template_type}, using base template")
            template_type = "base"
        
        template_string = template_map[template_type]
        
        # Extract input variables from template
        input_variables = self._extract_variables(template_string)
        
        # Add custom variables if provided
        if custom_variables:
            input_variables.extend(custom_variables.keys())
            input_variables = list(set(input_variables))  # Remove duplicates
        
        prompt_template = PromptTemplate(
            template=template_string,
            input_variables=input_variables
        )
        
        self.template_cache[cache_key] = prompt_template
        logger.info(f"Created prompt template", template_type=template_type, variables=input_variables)
        
        return prompt_template
    
    def _extract_variables(self, template_string: str) -> List[str]:
        """Extract variable names from template string."""
        import re
        variables = re.findall(r'\{(\w+)\}', template_string)
        return list(set(variables))
    
    def select_template_by_query_type(self, question: str, context_length: int = 0) -> str:
        """
        Automatically select the best template based on query characteristics.
        
        Args:
            question: The user's question
            context_length: Number of context documents
            
        Returns:
            Template type string
        """
        question_lower = question.lower()
        
        # Technical queries
        if any(keyword in question_lower for keyword in [
            'code', 'function', 'class', 'method', 'api', 'implementation',
            'algorithm', 'syntax', 'debug', 'error', 'exception'
        ]):
            return "technical"
        
        # Analysis queries
        elif any(keyword in question_lower for keyword in [
            'analyze', 'compare', 'evaluate', 'assess', 'implications',
            'impact', 'consequences', 'trends', 'patterns'
        ]):
            return "analysis"
        
        # Multi-source synthesis
        elif context_length > 3:
            return "synthesis"
        
        # Source attribution for factual queries
        elif any(keyword in question_lower for keyword in [
            'who', 'what', 'when', 'where', 'how many', 'statistics',
            'data', 'facts', 'evidence', 'source'
        ]):
            return "source_attribution"
        
        # Default to base template
        else:
            return "base"
    
    def create_context_string(
        self, 
        documents: List[Any], 
        include_metadata: bool = True,
        max_length: int = 4000
    ) -> str:
        """
        Create a formatted context string from documents.
        
        Args:
            documents: List of document objects
            include_metadata: Whether to include document metadata
            max_length: Maximum length of context string
            
        Returns:
            Formatted context string
        """
        context_parts = []
        current_length = 0
        
        for i, doc in enumerate(documents):
            # Format document content
            doc_number = i + 1
            metadata = dict(getattr(doc, 'metadata', {}) or {})
            display_name = metadata.get('source_display_name') or metadata.get('source') or f"Document {doc_number}"

            content_lines = [f"### Source: {display_name}"]

            if include_metadata:
                page_label = metadata.get('page_label')
                if not page_label and isinstance(metadata.get('page_number'), int):
                    page_label = f"Page {metadata['page_number']}"
                if page_label:
                    content_lines.append(f"Location: {page_label}")

                if metadata.get('section'):
                    content_lines.append(f"Section: {metadata['section']}")

            snippet = metadata.get('snippet')
            if snippet:
                content_lines.append(f"Summary: {snippet}")

            content_lines.append("Content:")
            content_lines.append(doc.page_content)
            content_lines.append("")

            doc_content = "\n".join(content_lines) + "\n"
            
            # Check length limit
            if current_length + len(doc_content) > max_length:
                # Truncate if necessary
                remaining_space = max_length - current_length
                if remaining_space > 100:  # Only add if there's meaningful space
                    truncated_content = doc_content[:remaining_space-50] + "...\n\n"
                    context_parts.append(truncated_content)
                break
            
            context_parts.append(doc_content)
            current_length += len(doc_content)
        
        return "".join(context_parts)
    
    def format_chat_history(self, chat_history: List[Dict[str, str]], max_exchanges: int = 5) -> str:
        """
        Format chat history for conversational prompts.
        
        Args:
            chat_history: List of chat exchanges
            max_exchanges: Maximum number of exchanges to include
            
        Returns:
            Formatted chat history string
        """
        if not chat_history:
            return "No previous conversation."
        
        # Take the most recent exchanges
        recent_history = chat_history[-max_exchanges:]
        
        formatted_history = []
        for exchange in recent_history:
            if 'user' in exchange and 'assistant' in exchange:
                formatted_history.append(f"User: {exchange['user']}")
                formatted_history.append(f"Assistant: {exchange['assistant']}")
        
        return "\n".join(formatted_history)


# Global prompt manager instance
prompt_manager = PromptManager()


def get_enhanced_prompt(
    question: str,
    documents: List[Any],
    template_type: Optional[str] = None,
    chat_history: Optional[List[Dict[str, str]]] = None,
    **kwargs
) -> str:
    """
    Convenience function to get a formatted prompt with context.
    
    Args:
        question: User's question
        documents: Retrieved documents
        template_type: Specific template type (auto-selected if None)
        chat_history: Previous conversation history
        **kwargs: Additional template variables
        
    Returns:
        Formatted prompt string
    """
    # Auto-select template if not specified
    if template_type is None:
        template_type = prompt_manager.select_template_by_query_type(
            question, len(documents)
        )
    
    # Get the appropriate template
    template = prompt_manager.get_prompt_template(template_type)
    
    # Prepare template variables
    template_vars = {
        "question": question,
        "context": prompt_manager.create_context_string(documents),
        **kwargs
    }
    
    # Add chat history if template supports it
    if "chat_history" in template.input_variables:
        template_vars["chat_history"] = prompt_manager.format_chat_history(chat_history or [])
    
    # Add number of sources for synthesis template
    if "num_sources" in template.input_variables:
        template_vars["num_sources"] = len(documents)
    
    try:
        formatted_prompt = template.format(**template_vars)
        logger.info(
            "Generated enhanced prompt",
            template_type=template_type,
            question_length=len(question),
            context_docs=len(documents)
        )
        return formatted_prompt
    except Exception as e:
        logger.error("Failed to format prompt", error=str(e), template_type=template_type)
        # Fallback to base template
        base_template = prompt_manager.get_prompt_template("base")
        return base_template.format(question=question, context=template_vars["context"])
