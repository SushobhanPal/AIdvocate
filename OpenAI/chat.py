import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables (check OpenAI/.env, RAG/.env, or parent)
env_local = Path(__file__).resolve().parent / ".env"
env_rag = Path(__file__).resolve().parent.parent / "RAG" / ".env"
if env_local.exists():
    load_dotenv(dotenv_path=env_local)
elif env_rag.exists():
    load_dotenv(dotenv_path=env_rag)
else:
    load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore

openai_api_key = os.getenv("OPENAI_API_KEY")
model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

client = ChatOpenAI(
    model=model_name,
    temperature=0,
    api_key=openai_api_key
)

embedding_model = HuggingFaceEmbeddings(
    model_name=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
)

vector_db = QdrantVectorStore.from_existing_collection(
    url=os.getenv("QDRANT_URL", "http://localhost:6333"),
    collection_name=os.getenv("COLLECTION_NAME", "learning_rag"),
    embedding=embedding_model,
)

if __name__ == "__main__":
    user_query = input("Ask something: ")
    if not user_query.strip():
        print("Query cannot be empty.")
        exit(0)

    print(f"Querying Qdrant and generating response with OpenAI ({model_name})...")
    search_results = vector_db.similarity_search(query=user_query)

    context = "\n\n\n".join([
        f"""
Page Content: {result.page_content}
Page Number: {result.metadata.get('page_label') or result.metadata.get('page', 'N/A')}
File Location: {result.metadata.get('source', 'N/A')}
"""
        for result in search_results
    ])

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

    response = client.invoke([
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": user_query
        }
    ])

    print(f"\n🤖: {response.content}")
