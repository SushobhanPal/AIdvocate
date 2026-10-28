import os
import sys
import asyncio
from pathlib import Path

root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from OpenAI.app import chat, QueryRequest

async def run_benchmark():
    test_queries = [
        "Can the changes to Form 6 be made by the Chief Election Commissioner without permission of the Supreme Court?",
        "What was held by the Supreme Court regarding voter registration rules and election guidelines?",
        "What are the main provisions under Article 324 discussed in the judgments?"
    ]

    print("=" * 80)
    print("AIdvocate: Ontology Knowledge Framework (OKF) Benchmark Test")
    print("=" * 80)

    for i, q in enumerate(test_queries, 1):
        print(f"\n[Test Query {i}]: \"{q}\"")
        req = QueryRequest(query=q, use_okf=True)
        try:
            res = await chat(req)
            print("\n--- [OKF Insights] ---")
            print(f"Detected Sections: {res.get('ontology_insights', {}).get('detected_sections')}")
            print(f"Detected Statutes: {res.get('ontology_insights', {}).get('detected_statutes')}")
            print(f"Preferred Discourse Roles: {res.get('ontology_insights', {}).get('preferred_roles')}")

            print("\n--- [Retrieved Sources & Discourse Roles] ---")
            for src in res.get("sources", []):
                print(f"• File: {src.get('filename')} | Page: {src.get('page')} | Role: {src.get('discourse_role')} | Sections: {src.get('sections')}")

            print("\n--- [Synthesized Legal Answer] ---")
            print(res.get("answer")[:400] + ("..." if len(res.get("answer")) > 400 else ""))
            print("-" * 80)
        except Exception as e:
            print(f"Error executing query: {e}")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
