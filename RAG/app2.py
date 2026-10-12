import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore

# Load environment variables from RAG/.env or project root
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

app = FastAPI(title="RAG Backend API (Groq - openai/gpt-oss-120b)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    print("WARNING: GROQ_API_KEY not found in environment or .env file.")

llm_client = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    groq_api_key=groq_api_key
)

embedding_model = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

def get_vector_db():
    return QdrantVectorStore.from_existing_collection(
        url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        collection_name="learning_rag",
        embedding=embedding_model,
    )

class QueryRequest(BaseModel):
    query: str

@app.get("/")
def root():
    return {
        "message": "RAG Backend Server (Groq) is running",
        "model": "openai/gpt-oss-120b"
    }

@app.post("/chat")
@app.post("/api/chat")
async def chat(request: QueryRequest):
    user_query = request.query.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        vector_db = get_vector_db()
        search_results = vector_db.similarity_search(query=user_query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query Qdrant: {str(e)}")

    context = "\n\n\n".join([
        f"""
Page Content: {result.page_content}
Page Number: {result.metadata.get('page_label') or result.metadata.get('page', 'N/A')}
File Location: {result.metadata.get('source', 'N/A')}
"""
        for result in search_results
    ])

    sources = [
        {
            "filename": os.path.basename(res.metadata.get("source", "PDF Document")),
            "page": res.metadata.get("page_label") or res.metadata.get("page", 1),
            "snippet": res.page_content[:200] + "..."
        }
        for res in search_results
    ]

    SYSTEM_PROMPT = f"""
You are a helpful AI Assistant who answers user queries
based on the available context retrieved from a PDF file
about legal cases and Supreme Court verdicts.

Your task is to provide correct information based on the
retrieved context.

You should answer the user only using the following context.
If relevant, mention the page number so that the user can
open the correct page and read more.

Context:

{context}
"""

    try:
        response = llm_client.invoke([
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_query
            }
        ])
        
        reply = response.content if hasattr(response, "content") else str(response)

        return {
            "answer": reply,
            "sources": sources
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Groq execution failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Allow running from either MP root or RAG dir
    app_import = "app2:app" if os.path.basename(os.getcwd()) == "RAG" else "RAG.app2:app"
    uvicorn.run(app_import, host="0.0.0.0", port=8000, reload=True)
