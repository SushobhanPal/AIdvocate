"""
Judge Agent – Evaluates whether retrieved Qdrant context is sufficient
to answer the user's legal question. Uses OpenAI (gpt-4o-mini) for
high-quality reasoning about legal sufficiency.

Responsibilities:
1. Score the relevance of retrieved chunks against the query.
2. Determine if a web search is needed.
3. Synthesize the final legal answer once all evidence is gathered.
"""

import os
import sys
from pathlib import Path

root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from dotenv import load_dotenv
env_local = Path(__file__).resolve().parent / ".env"
env_rag = Path(__file__).resolve().parent.parent / "RAG" / ".env"
if env_local.exists():
    load_dotenv(dotenv_path=env_local)
elif env_rag.exists():
    load_dotenv(dotenv_path=env_rag)
else:
    load_dotenv()

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List, Optional


class JudgeVerdict(BaseModel):
    """Structured output from the Judge Agent's evaluation."""
    is_sufficient: bool = Field(
        description="True if the retrieved context contains enough information to answer the query accurately"
    )
    confidence_score: float = Field(
        default=0.0,
        description="Confidence in the retrieved context's relevance (0.0 to 1.0)"
    )
    missing_aspects: List[str] = Field(
        default_factory=list,
        description="Specific legal aspects the context fails to address"
    )
    web_search_queries: List[str] = Field(
        default_factory=list,
        description="Suggested search queries to fill gaps, if context is insufficient"
    )
    reasoning: str = Field(
        default="",
        description="Brief explanation of why the context is or isn't sufficient"
    )


class JudgeAgent:
    """Uses OpenAI (heavyweight) to evaluate legal context quality and synthesize final answers."""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        try:
            self.structured_llm = self.llm.with_structured_output(JudgeVerdict)
        except Exception:
            self.structured_llm = None

    def evaluate_context(self, user_query: str, context_blocks: List[str]) -> JudgeVerdict:
        """Evaluates whether the retrieved context is sufficient to answer the query."""
        context_text = "\n\n".join(context_blocks) if context_blocks else "(No context retrieved)"

        eval_prompt = f"""
You are a Senior Legal Research Judge evaluating whether retrieved Supreme Court
case excerpts are sufficient to answer a user's legal question.

USER QUESTION:
"{user_query}"

RETRIEVED CONTEXT:
{context_text}

Evaluate:
1. Does the context directly address the legal question?
2. Are there specific statutes, sections, or holdings that answer the query?
3. What is your confidence that this context alone can produce an accurate legal answer?
4. If the context is insufficient, what specific aspects are missing?
5. If missing, suggest 1-3 concise web search queries to find relevant Indian legal cases or statutes.

Set is_sufficient=true ONLY if confidence >= 0.6.
"""
        if self.structured_llm:
            try:
                result = self.structured_llm.invoke(eval_prompt)
                if isinstance(result, JudgeVerdict):
                    return result
            except Exception:
                pass

        # Fallback: heuristic evaluation
        has_content = len(context_blocks) > 0
        has_substance = any(len(block) > 200 for block in context_blocks) if context_blocks else False
        return JudgeVerdict(
            is_sufficient=has_content and has_substance,
            confidence_score=0.5 if has_substance else 0.2,
            missing_aspects=["Unable to perform deep evaluation (fallback mode)"],
            web_search_queries=[f"Indian Supreme Court {user_query}"] if not has_substance else [],
            reasoning="Heuristic fallback: context volume assessment only."
        )

    def synthesize_answer(
        self,
        user_query: str,
        rag_context: str,
        web_context: Optional[str] = None,
        ontology_insights: Optional[dict] = None
    ) -> str:
        """Produces the final, authoritative legal answer using OpenAI."""
        combined_context = f"""
=== RETRIEVED FROM SUPREME COURT DATABASE (Primary Source) ===
{rag_context}
"""
        if web_context:
            combined_context += f"""
=== ADDITIONAL CONTEXT FROM WEB SEARCH (Supplementary) ===
{web_context}
"""
        sections_info = ""
        if ontology_insights:
            detected = ontology_insights.get("detected_sections", [])
            statutes = ontology_insights.get("detected_statutes", [])
            if detected or statutes:
                sections_info = f"\nDetected Legal Anchors: Sections={detected}, Statutes={statutes}"

        synthesis_prompt = f"""
You are AIdvocate, an expert Supreme Court AI Assistant.
Answer the user's legal question using ALL provided context.
{sections_info}

CRITICAL INSTRUCTIONS:
1. Prioritize the Supreme Court Database context as the PRIMARY source of truth.
2. Use Web Search context ONLY to supplement or provide additional case references.
3. Clearly distinguish between COURT_HOLDING (binding rulings) and mere lawyer arguments.
4. Cite specific Sections, Articles, Rules, page numbers, and case names when available.
5. If web results provide relevant precedents not in the database, cite them with proper attribution.
6. If neither source answers the question, state clearly that the information is not available.

Context:
{combined_context}
"""
        try:
            response = self.llm.invoke([
                {"role": "system", "content": synthesis_prompt},
                {"role": "user", "content": user_query}
            ])
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            return f"Error generating legal analysis: {str(e)}"
