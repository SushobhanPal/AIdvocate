import os
import re
import sys
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Load environment
env_local = Path(__file__).resolve().parent / ".env"
env_rag = Path(__file__).resolve().parent.parent / "RAG" / ".env"
if env_local.exists():
    load_dotenv(dotenv_path=env_local)
elif env_rag.exists():
    load_dotenv(dotenv_path=env_rag)
else:
    load_dotenv()

from langchain_openai import ChatOpenAI
from OpenAI.ontology_schema import ChunkOntology, DiscourseRole, LegalEntities

# Fast heuristic regex patterns for common Indian legal terminology
STATUTE_PATTERN = re.compile(
    r"\b((?:[A-Z][a-z]+\s+)+Act(?:,\s*\d{4})?|Constitution\s+of\s+India|IPC|CrPC|CPC|Conduct\s+of\s+Elections?\s+Rules(?:,\s*\d{4})?)\b",
    re.IGNORECASE
)
SECTION_PATTERN = re.compile(
    r"\b(Section\s+\d+[A-Z]*(?:\(\d+\))*|Article\s+\d+[A-Z]*|Rule\s+\d+[A-Z]*|Form\s+\d+[A-Z]*|Order\s+[IVXLCDM]+\s+Rule\s+\d+)\b",
    re.IGNORECASE
)

class OntologyExtractor:
    def __init__(self, model_name: str = "gpt-4o-mini"):
        api_key = os.getenv("OPENAI_API_KEY")
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0,
            api_key=api_key
        )
        # Use LangChain structured output with ChunkOntology schema
        try:
            self.structured_llm = self.llm.with_structured_output(ChunkOntology)
        except Exception:
            self.structured_llm = None

    def fast_heuristic_extract(self, text: str) -> ChunkOntology:
        """Lightweight regex and keyword rule-based extractor."""
        statutes = list(set(m.group(0).strip() for m in STATUTE_PATTERN.finditer(text)))
        sections = list(set(m.group(0).strip() for m in SECTION_PATTERN.finditer(text)))

        lower = text.lower()
        role = DiscourseRole.GENERAL
        principle = None

        if any(w in lower for w in ["we hold that", "in our considered view", "the question is answered", "we conclude that", "ratio decidendi", "appeal is allowed", "appeal is dismissed"]):
            role = DiscourseRole.COURT_HOLDING
        elif any(w in lower for w in ["learned counsel for the appellant", "petitioner submitted", "contended by the petitioner", "learned senior counsel appearing for the appellant"]):
            role = DiscourseRole.PETITIONER_ARGUMENT
        elif any(w in lower for w in ["learned counsel for the respondent", "respondent submitted", "state contended", "on behalf of the respondent"]):
            role = DiscourseRole.RESPONDENT_ARGUMENT
        elif any(w in lower for w in ["section reads as follows", "sub-section (", "article reads as under"]):
            role = DiscourseRole.STATUTORY_TEXT

        return ChunkOntology(
            discourse_role=role,
            entities=LegalEntities(
                statutes=statutes[:5],
                sections=sections[:10]
            ),
            core_legal_principle=principle
        )

    def extract_with_llm(self, text: str) -> ChunkOntology:
        """Extracts complete legal ontology and discourse role using OpenAI structured output."""
        if not self.structured_llm:
            return self.fast_heuristic_extract(text)

        prompt = f"""
You are an expert Legal Ontologist analyzing Indian Supreme Court verdicts.
Extract the legal entities and classify the discourse role for the following text passage:

Passage:
\"\"\"
{text[:2000]}
\"\"\"

Classify discourse_role as one of:
- COURT_HOLDING (Final binding ruling / Ratio Decidendi by the Court)
- PETITIONER_ARGUMENT (Arguments/submissions by the appellant/petitioner)
- RESPONDENT_ARGUMENT (Arguments/submissions by the respondent/state)
- STATUTORY_TEXT (Quoting or verbatim reading of Acts/Sections/Rules)
- CASE_FACTS (Recounting facts of what happened)
- GENERAL (Procedural, citations, introductory)

Extract specific statutes (Acts) and sections (Section X, Article Y, Rule Z, Form N).
"""
        try:
            result = self.structured_llm.invoke(prompt)
            if isinstance(result, ChunkOntology):
                return result
            return self.fast_heuristic_extract(text)
        except Exception as e:
            # Fall back to fast heuristic if API or network fails
            return self.fast_heuristic_extract(text)
