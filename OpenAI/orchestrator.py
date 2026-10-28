"""
Orchestrator – Coordinates the full agentic legal RAG pipeline.

Flow:
1. Parse query using OKF Query Parser (Groq – lightweight)
2. Retrieve chunks from Qdrant with ontology re-ranking
3. Judge Agent evaluates context sufficiency (OpenAI – heavyweight)
4. If insufficient → Web Search Agent finds external cases (Groq – lightweight)
5. Judge Agent synthesizes final answer from all evidence (OpenAI – heavyweight)

Cost Model:
  • Groq  → Query parsing, search refinement, result summarization (fast, cheap)
  • OpenAI → Context evaluation, final legal synthesis (accurate, authoritative)
"""

import os
import sys
from pathlib import Path
from typing import List, Optional

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

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from OpenAI.query_parser import LegalQueryParser
from OpenAI.ontology_schema import DiscourseRole
from OpenAI.judge_agent import JudgeAgent
from OpenAI.websearch_agent import WebSearchAgent


class LegalOrchestrator:
    """Coordinates Judge Agent, Web Search Agent, and Qdrant retrieval."""

    def __init__(self):
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.okf_collection = os.getenv("OKF_COLLECTION_NAME", "okf_legal_rag")
        self.raw_collection = os.getenv("COLLECTION_NAME", "learning_rag")

        self.embedding_model = HuggingFaceEmbeddings(
            model_name=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        )
        self.qdrant_client = QdrantClient(url=self.qdrant_url)

        # Agents
        self.query_parser = LegalQueryParser()   # Uses Groq (lightweight)
        self.judge_agent = JudgeAgent()          # Uses OpenAI (heavyweight)
        # WebSearchAgent may fail if Groq endpoint or DuckDuckGo is unreachable.
        try:
            self.web_agent = WebSearchAgent()        # Uses Groq (lightweight)
        except Exception as e:
            # Log the issue and continue without web search capability.
            print(f"[Orchestrator] Warning: WebSearchAgent could not be initialized: {e}")
            self.web_agent = None

    def _get_active_collection(self) -> str:
        try:
            collections = [c.name for c in self.qdrant_client.get_collections().collections]
            if self.okf_collection in collections:
                return self.okf_collection
            return self.raw_collection
        except Exception:
            return self.raw_collection

    def _get_vector_db(self, collection_name: str):
        return QdrantVectorStore.from_existing_collection(
            url=self.qdrant_url,
            collection_name=collection_name,
            embedding=self.embedding_model,
        )

    def _ontology_rerank(self, results, parsed_query) -> list:
        """Re-ranks retrieved chunks using ontological scoring."""
        def score_chunk(doc):
            score = 0
            meta = doc.metadata or {}
            role = meta.get("discourse_role", "")
            sections = [s.lower() for s in meta.get("sections", [])]
            content_lower = doc.page_content.lower()

            for target_sec in parsed_query.section_filters:
                if target_sec.lower() in sections or target_sec.lower() in content_lower:
                    score += 5

            if DiscourseRole.COURT_HOLDING.value in [r.value for r in parsed_query.preferred_roles]:
                if role == DiscourseRole.COURT_HOLDING.value:
                    score += 4
                elif role in [DiscourseRole.PETITIONER_ARGUMENT.value, DiscourseRole.RESPONDENT_ARGUMENT.value]:
                    score -= 1

            return score

        ranked = sorted(results, key=score_chunk, reverse=True)
        return ranked[:5]

    def _format_context_blocks(self, results) -> List[str]:
        """Formats retrieved documents into structured context blocks."""
        blocks = []
        for res in results:
            meta = res.metadata or {}
            role = meta.get("discourse_role", "GENERAL")
            page = meta.get("page_label") or meta.get("page", "N/A")
            sections = ", ".join(meta.get("sections", [])) or "None"
            statutes = ", ".join(meta.get("statutes", [])) or "None"

            blocks.append(
                f"[DISCOURSE: {role} | PAGE: {page} | STATUTES: {statutes} | SECTIONS: {sections}]\n"
                f"{res.page_content}"
            )
        return blocks

    def _format_sources(self, results, web_results=None) -> list:
        """Formats source citations for the API response."""
        sources = [
            {
                "filename": os.path.basename(res.metadata.get("source", "PDF Document")),
                "page": res.metadata.get("page_label") or res.metadata.get("page", 1),
                "discourse_role": res.metadata.get("discourse_role", "GENERAL"),
                "sections": res.metadata.get("sections", []),
                "snippet": res.page_content[:200] + "...",
                "source_type": "database"
            }
            for res in results
        ]

        if web_results:
            for wr in web_results.get("raw_results", [])[:3]:
                sources.append({
                    "filename": wr.get("title", "Web Source")[:80],
                    "page": "web",
                    "discourse_role": "WEB_SEARCH",
                    "sections": [],
                    "snippet": wr.get("snippet", "")[:200] + "...",
                    "link": wr.get("link", ""),
                    "source_type": "web_search"
                })

        return sources

    async def process_query(self, user_query: str, use_okf: bool = True) -> dict:
        """
        Full orchestrated pipeline:
        1. Parse query (Groq)
        2. Retrieve from Qdrant + rerank
        3. Judge evaluates sufficiency (OpenAI)
        4. If needed, Web Search Agent fills gaps (Groq)
        5. Judge synthesizes final answer (OpenAI)
        """
        # ── Step 1: Ontology Query Parsing (Groq – lightweight) ──
        parsed_query = self.query_parser.parse_query(user_query) if use_okf else None
        search_text = parsed_query.semantic_search_query if parsed_query else user_query

        ontology_insights = {
            "detected_sections": parsed_query.section_filters if parsed_query else [],
            "detected_statutes": parsed_query.statute_filters if parsed_query else [],
            "preferred_roles": [r.value for r in parsed_query.preferred_roles] if parsed_query else []
        }

        # ── Step 2: Qdrant Retrieval + Ontology Re-ranking ──
        collection_name = self._get_active_collection()
        vector_db = self._get_vector_db(collection_name)

        try:
            candidate_results = vector_db.similarity_search(query=search_text, k=8)
        except Exception as e:
            return {
                "answer": f"Failed to query vector database: {str(e)}",
                "sources": [],
                "agent_trace": {"error": str(e)},
                "ontology_insights": ontology_insights
            }

        if parsed_query and use_okf:
            selected_results = self._ontology_rerank(candidate_results, parsed_query)
        else:
            selected_results = candidate_results[:5]

        context_blocks = self._format_context_blocks(selected_results)

        # ── Step 3: Judge Agent Evaluates Context (OpenAI – heavyweight) ──
        judge_verdict = self.judge_agent.evaluate_context(user_query, context_blocks)

        web_results = None
        web_context = None
        agent_trace = {
            "step_1_query_parsing": {
                "engine": "Groq",
                "parsed_sections": ontology_insights["detected_sections"],
                "parsed_statutes": ontology_insights["detected_statutes"],
            },
            "step_2_qdrant_retrieval": {
                "collection": collection_name,
                "chunks_retrieved": len(candidate_results),
                "chunks_after_rerank": len(selected_results),
            },
            "step_3_judge_evaluation": {
                "engine": "OpenAI",
                "is_sufficient": judge_verdict.is_sufficient,
                "confidence": judge_verdict.confidence_score,
                "reasoning": judge_verdict.reasoning,
                "missing_aspects": judge_verdict.missing_aspects,
            },
        }

        # ── Step 4: Web Search if Judge says context is insufficient (Groq) ──
        if not judge_verdict.is_sufficient and judge_verdict.web_search_queries:
            web_results = self.web_agent.execute_full_search(
                search_queries=judge_verdict.web_search_queries,
                user_query=user_query
            )
            web_context = web_results.get("summary", "")

            agent_trace["step_4_web_search"] = {
                "engine": "Groq + DuckDuckGo",
                "triggered": True,
                "refined_queries": web_results.get("refined_queries", []),
                "results_count": len(web_results.get("raw_results", [])),
            }
        else:
            agent_trace["step_4_web_search"] = {
                "triggered": False,
                "reason": "Judge determined context is sufficient"
            }

        # ── Step 5: Judge Synthesizes Final Answer (OpenAI – heavyweight) ──
        rag_context = "\n\n".join(context_blocks)
        final_answer = self.judge_agent.synthesize_answer(
            user_query=user_query,
            rag_context=rag_context,
            web_context=web_context,
            ontology_insights=ontology_insights
        )

        agent_trace["step_5_synthesis"] = {
            "engine": "OpenAI",
            "used_web_context": web_context is not None and len(web_context) > 0,
        }

        sources = self._format_sources(selected_results, web_results)

        return {
            "answer": final_answer,
            "sources": sources,
            "agent_trace": agent_trace,
            "ontology_insights": ontology_insights
        }
