import os
import glob
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_openai import OpenAIEmbeddings  # For future text-embedding-3-small

# Load environment variables
env_local = Path(__file__).resolve().parent / ".env"
env_rag = Path(__file__).resolve().parent.parent / "RAG" / ".env"
if env_local.exists():
    load_dotenv(dotenv_path=env_local)
elif env_rag.exists():
    load_dotenv(dotenv_path=env_rag)
else:
    load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333/")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "learning_rag")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

_embedding_instance = None

def get_embedding_model():
    """Returns the current embedding model. 
    Can be switched to OpenAIEmbeddings(model='text-embedding-3-small') in the future.
    """
    global _embedding_instance
    if _embedding_instance is None:
        _embedding_instance = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    return _embedding_instance

def index_single_pdf(file_path: str):
    """Loads, splits, and indexes a single PDF file into Qdrant."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    print(f"Loading document: {file_path}")
    loader = PyPDFLoader(file_path=file_path)
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(documents=docs)
    print(f"Created {len(chunks)} chunks for {file_path}")

    embedding_model = get_embedding_model()
    
    try:
        vector_store = QdrantVectorStore.from_existing_collection(
            url=QDRANT_URL,
            collection_name=COLLECTION_NAME,
            embedding=embedding_model,
        )
        vector_store.add_documents(chunks)
    except Exception:
        vector_store = QdrantVectorStore.from_documents(
            documents=chunks,
            embedding=embedding_model,
            url=QDRANT_URL,
            collection_name=COLLECTION_NAME
        )
    print(f"Successfully indexed {file_path}")
    return len(chunks)

def index_all_pdfs(pdf_dir: str = "pdf"):
    """Scans and indexes all PDF files in the target directory."""
    abs_pdf_dir = os.path.abspath(pdf_dir)
    pdf_files = glob.glob(os.path.join(abs_pdf_dir, "*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {abs_pdf_dir}")
        return 0

    print(f"Found {len(pdf_files)} PDF files in {pdf_dir}: {[os.path.basename(f) for f in pdf_files]}")

    all_chunks = []
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    for pdf_path in pdf_files:
        try:
            print(f"Processing: {os.path.basename(pdf_path)}")
            loader = PyPDFLoader(file_path=pdf_path)
            docs = loader.load()
            chunks = text_splitter.split_documents(documents=docs)
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"Error processing {pdf_path}: {e}")

    if not all_chunks:
        print("No document chunks created.")
        return 0

    embedding_model = get_embedding_model()
    print(f"Uploading {len(all_chunks)} chunks from {len(pdf_files)} PDFs to Qdrant collection '{COLLECTION_NAME}'...")

    vector_store = QdrantVectorStore.from_documents(
        documents=all_chunks,
        embedding=embedding_model,
        url=QDRANT_URL,
        collection_name=COLLECTION_NAME
    )

    print("Indexing of all documents done....")
    return len(all_chunks)

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    
    # Example: index folder
    folder_path = os.path.join(project_root, "pdf")
    index_all_pdfs(folder_path)
