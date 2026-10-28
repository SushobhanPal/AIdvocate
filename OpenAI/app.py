"""
AIdvocate – Agentic Legal RAG Backend (OpenAI + Groq + OKF)

This FastAPI server orchestrates:
  • Qdrant vector retrieval with Ontology Knowledge Framework
  • Judge Agent (OpenAI) for context evaluation & answer synthesis
  • Web Search Agent (Groq + DuckDuckGo) for external case discovery
  • Orchestrator coordinating the full pipeline
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load environment
env_local = Path(__file__).resolve().parent / ".env"
env_rag = Path(__file__).resolve().parent.parent / "RAG" / ".env"
if env_local.exists():
    load_dotenv(dotenv_path=env_local)
elif env_rag.exists():
    load_dotenv(dotenv_path=env_rag)
else:
    load_dotenv()

from OpenAI.orchestrator import LegalOrchestrator

app = FastAPI(title="AIdvocate – Agentic Legal RAG (OpenAI + Groq + OKF)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Orchestrator (creates Judge + WebSearch agents internally)
orchestrator = LegalOrchestrator()


class QueryRequest(BaseModel):
    query: str
    use_okf: bool = True


@app.get("/")
def root():
    return {
        "message": "AIdvocate Agentic Legal RAG Server is running",
        "agents": {
            "judge": "OpenAI (gpt-4o-mini) – Context evaluation & answer synthesis",
            "web_search": "Groq (openai/gpt-oss-120b) – Query refinement & result summarization",
            "query_parser": "Groq – Ontology-guided query decomposition"
        },
        "framework": "Ontology Knowledge Framework (OKF) + Multi-Agent Orchestrator"
    }


@app.post("/chat")
@app.post("/api/chat")
async def chat(request: QueryRequest):
    user_query = request.query.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        result = await orchestrator.process_query(
            user_query=user_query,
            use_okf=request.use_okf
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Orchestrator error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    app_import = "app:app" if os.path.basename(os.getcwd()) == "OpenAI" else "OpenAI.app:app"
    uvicorn.run(app_import, host="0.0.0.0", port=8000, reload=True)
