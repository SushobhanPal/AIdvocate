import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

env_local = Path(__file__).resolve().parent / ".env"
env_rag = Path(__file__).resolve().parent.parent / "RAG" / ".env"
if env_local.exists():
    load_dotenv(dotenv_path=env_local)
elif env_rag.exists():
    load_dotenv(dotenv_path=env_rag)
else:
    load_dotenv()

from langchain_groq import ChatGroq
from OpenAI.ontology_schema import ParsedLegalQuery, DiscourseRole

SECTION_REGEX = re.compile(
    r"\b(Section\s+\d+[A-Z]*(?:\(\d+\))*|Article\s+\d+[A-Z]*|Rule\s+\d+[A-Z]*|Form\s+\d+[A-Z]*)\b",
    re.IGNORECASE
)

class LegalQueryParser:
    def __init__(self, model_name: str = None):
        groq_model = model_name or os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        groq_key = os.getenv("GROQ_API_KEY")
        try:
            groq_model = model_name or os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
            groq_key = os.getenv("GROQ_API_KEY")
            self.llm = ChatGroq(
                model=groq_model,
                temperature=0,
                groq_api_key=groq_key
            )
        except Exception as e:
            print(f"[LegalQueryParser] Warning: Groq LLM init failed: {e}. Falling back to heuristic parser.")
            self.llm = None
        try:
            if self.llm:
                self.structured_llm = self.llm.with_structured_output(ParsedLegalQuery)
            else:
                self.structured_llm = None
        except Exception:
            self.structured_llm = None

    def fast_heuristic_parse(self, query: str) -> ParsedLegalQuery:
        """Fast rule-based query parser."""
        sections = list(set(m.group(0).strip() for m in SECTION_REGEX.finditer(query)))
        lower = query.lower()

        preferred_roles = []
        if any(w in lower for w in ["hold", "held", "verdict", "rule", "decision", "permission", "can", "allowed", "dismissed"]):
            preferred_roles.append(DiscourseRole.COURT_HOLDING)

        statutes = []
        if "election" in lower:
            statutes.append("Conduct of Elections Rules")
            statutes.append("Representation of the People Act")
        if "constitution" in lower or "fundamental right" in lower or "article" in lower:
            statutes.append("Constitution of India")

        return ParsedLegalQuery(
            semantic_search_query=query,
            statute_filters=statutes,
            section_filters=sections,
            preferred_roles=preferred_roles
        )

    def parse_query(self, query: str) -> ParsedLegalQuery:
        """Parses a user legal query into semantic text + ontological filters."""
        if not self.structured_llm:
            return self.fast_heuristic_parse(query)

        prompt = f"""
You are an expert Indian Legal Ontologist.
Decompose the following user question into:
1. semantic_search_query: clean natural language query for vector search.
2. statute_filters: relevant Acts/Statutes/Rules targeted (e.g., 'Representation of the People Act', 'Conduct of Elections Rules', 'Constitution of India').
3. section_filters: specific sections, rules, articles, or forms mentioned (e.g., 'Form 6', 'Rule 26', 'Article 324').
4. preferred_roles: COURT_HOLDING if asking about the court's verdict, decision, or validity of an action; otherwise empty or relevant roles.

User Question: "{query}"
"""
        try:
            parsed = self.structured_llm.invoke(prompt)
            if isinstance(parsed, ParsedLegalQuery):
                return parsed
            return self.fast_heuristic_parse(query)
        except Exception:
            return self.fast_heuristic_parse(query)
