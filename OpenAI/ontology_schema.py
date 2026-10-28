from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class DiscourseRole(str, Enum):
    """Classifies the legal discourse function of a text passage in a judgment."""
    COURT_HOLDING = "COURT_HOLDING"               # The binding decision / Ratio Decidendi
    PETITIONER_ARGUMENT = "PETITIONER_ARGUMENT"   # Contentions raised by the petitioner/appellant
    RESPONDENT_ARGUMENT = "RESPONDENT_ARGUMENT"   # Contentions raised by the respondent/state
    STATUTORY_TEXT = "STATUTORY_TEXT"             # Quoted acts, sections, articles, or rules
    CASE_FACTS = "CASE_FACTS"                     # Material facts of the case
    PROCEDURAL_HISTORY = "PROCEDURAL_HISTORY"     # Lower court orders, appeals history
    GENERAL = "GENERAL"                           # General discourse, preamble, citations

class LegalEntities(BaseModel):
    """Structured legal entities extracted from text."""
    statutes: List[str] = Field(
        default_factory=list,
        description="Names of statutory Acts or Constitution (e.g., 'Representation of the People Act, 1951', 'Constitution of India')"
    )
    sections: List[str] = Field(
        default_factory=list,
        description="Specific sections, rules, articles, or forms referenced (e.g., 'Section 123(3)', 'Article 324', 'Form 6', 'Rule 26')"
    )
    parties: List[str] = Field(
        default_factory=list,
        description="Key entities or parties mentioned (e.g., 'Election Commission of India', 'Chief Election Commissioner')"
    )
    bench: List[str] = Field(
        default_factory=list,
        description="Judges or bench names mentioned if any"
    )
    cited_cases: List[str] = Field(
        default_factory=list,
        description="Prior case precedents or landmark judgments cited"
    )

class ChunkOntology(BaseModel):
    """Complete ontology annotation for an indexed text chunk."""
    discourse_role: DiscourseRole = Field(
        default=DiscourseRole.GENERAL,
        description="Primary legal role of this chunk in the judgment"
    )
    entities: LegalEntities = Field(
        default_factory=LegalEntities,
        description="Extracted legal entities"
    )
    core_legal_principle: Optional[str] = Field(
        default=None,
        description="If this chunk is a COURT_HOLDING, concise statement of the rule or principle decided"
    )

class ParsedLegalQuery(BaseModel):
    """Ontology-guided decomposition of a user question."""
    semantic_search_query: str = Field(
        ...,
        description="Dense query text optimized for vector similarity search"
    )
    statute_filters: List[str] = Field(
        default_factory=list,
        description="Statutes explicitly targeted in the query to apply as filters/boosts"
    )
    section_filters: List[str] = Field(
        default_factory=list,
        description="Sections, articles, rules, or forms targeted in the query (e.g., 'Form 6', 'Article 324')"
    )
    preferred_roles: List[DiscourseRole] = Field(
        default_factory=list,
        description="Discourse roles preferred for this question (e.g., COURT_HOLDING for ruling questions)"
    )
