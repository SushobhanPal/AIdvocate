from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore



client = ChatOllama(
    model="qwen3:8b",
    temperature=0,
    base_url="http://localhost:11434"
)




embedding_model = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)




vector_db = QdrantVectorStore.from_existing_collection(
    url="http://localhost:6333",
    collection_name="learning_rag",
    embedding=embedding_model,
)




user_query = input("Ask something: ")





search_results = vector_db.similarity_search(
    query=user_query
)



context = "\n\n\n".join([
    f"""
Page Content: {result.page_content}
Page Number: {result.metadata['page_label']}
File Location: {result.metadata['source']}
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




print(f"🤖: {response.content}")