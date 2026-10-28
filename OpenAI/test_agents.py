"""
End-to-end test for the Multi-Agent Orchestrated Legal RAG system.
Tests both database-sufficient and web-search-triggered scenarios.
"""

import os
import sys
import asyncio
import json
from pathlib import Path

root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from OpenAI.app import chat, QueryRequest


async def run_tests():
    print("=" * 80)
    print("AIdvocate: Multi-Agent Orchestrator Test Suite")
    print("  Judge Agent   → OpenAI (gpt-4o-mini)")
    print("  Web Search    → Groq (openai/gpt-oss-120b) + DuckDuckGo")
    print("  Query Parser  → Groq (openai/gpt-oss-120b)")
    print("=" * 80)

    test_cases = [
        {
            "name": "DB-Sufficient: Section 138 NI Act",
            "query": "What was held regarding Section 138 and Section 142 of the Negotiable Instruments Act?",
            "expect_web": False
        },
        {
            "name": "DB-Insufficient: Kesavananda Bharati Case",
            "query": "What was the ratio decidendi in the Kesavananda Bharati vs State of Kerala case regarding basic structure doctrine?",
            "expect_web": True
        },
    ]

    for i, tc in enumerate(test_cases, 1):
        print(f"\n{'─' * 80}")
        print(f"TEST {i}: {tc['name']}")
        print(f"Query: \"{tc['query']}\"")
        print(f"Expected Web Search: {'Yes' if tc['expect_web'] else 'No'}")
        print(f"{'─' * 80}")

        req = QueryRequest(query=tc["query"], use_okf=True)
        try:
            result = await chat(req)

            # Agent Trace
            trace = result.get("agent_trace", {})
            print("\n📋 AGENT TRACE:")
            print(f"  Step 1 (Query Parsing / Groq):")
            s1 = trace.get("step_1_query_parsing", {})
            print(f"    Sections: {s1.get('parsed_sections')}")
            print(f"    Statutes: {s1.get('parsed_statutes')}")

            print(f"  Step 2 (Qdrant Retrieval):")
            s2 = trace.get("step_2_qdrant_retrieval", {})
            print(f"    Collection: {s2.get('collection')}")
            print(f"    Chunks retrieved: {s2.get('chunks_retrieved')} → after rerank: {s2.get('chunks_after_rerank')}")

            print(f"  Step 3 (Judge Evaluation / OpenAI):")
            s3 = trace.get("step_3_judge_evaluation", {})
            print(f"    Sufficient: {s3.get('is_sufficient')}")
            print(f"    Confidence: {s3.get('confidence')}")
            print(f"    Reasoning: {s3.get('reasoning', '')[:150]}")
            if s3.get("missing_aspects"):
                print(f"    Missing: {s3.get('missing_aspects')}")

            print(f"  Step 4 (Web Search / Groq + DDG):")
            s4 = trace.get("step_4_web_search", {})
            print(f"    Triggered: {s4.get('triggered')}")
            if s4.get("triggered"):
                print(f"    Queries: {s4.get('refined_queries')}")
                print(f"    Results: {s4.get('results_count')}")
            else:
                print(f"    Reason: {s4.get('reason')}")

            print(f"  Step 5 (Final Synthesis / OpenAI):")
            s5 = trace.get("step_5_synthesis", {})
            print(f"    Used web context: {s5.get('used_web_context')}")

            # Sources
            sources = result.get("sources", [])
            db_sources = [s for s in sources if s.get("source_type") == "database"]
            web_sources = [s for s in sources if s.get("source_type") == "web_search"]
            print(f"\n📚 SOURCES: {len(db_sources)} database, {len(web_sources)} web")
            for src in db_sources[:2]:
                print(f"  DB: {src.get('filename')} p.{src.get('page')} [{src.get('discourse_role')}]")
            for src in web_sources[:2]:
                print(f"  Web: {src.get('filename')[:60]}")

            # Answer
            answer = result.get("answer", "")
            print(f"\n⚖️  ANSWER ({len(answer)} chars):")
            print(f"  {answer[:400]}{'...' if len(answer) > 400 else ''}")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")

    print(f"\n{'=' * 80}")
    print("Test suite complete.")


if __name__ == "__main__":
    asyncio.run(run_tests())
