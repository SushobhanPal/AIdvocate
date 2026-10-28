import os
import glob
import sys
from pathlib import Path
from dotenv import load_dotenv

root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

env_local = Path(__file__).resolve().parent / ".env"
env_rag = Path(__file__).resolve().parent.parent / "RAG" / ".env"
if env_local.exists():
    load_dotenv(dotenv_path=env_local)
elif env_rag.exists():
    load_dotenv(dotenv_path=env_rag)
else:
    load_dotenv()

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models

from OpenAI.ontology_extractor import OntologyExtractor

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333/")
OKF_COLLECTION_NAME = os.getenv("OKF_COLLECTION_NAME", "okf_legal_rag")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

_embedding_instance = None

def get_embedding_model():
    global _embedding_instance
    if _embedding_instance is None:
        _embedding_instance = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    return _embedding_instance

def ensure_payload_indexes(client: QdrantClient, collection_name: str):
    """Creates payload indexes in Qdrant for high-speed metadata filtering."""
    try:
        client.create_payload_index(
            collection_name=collection_name,
            field_name="metadata.discourse_role",
            field_schema=models.PayloadSchemaType.KEYWORD
        )
        client.create_payload_index(
            collection_name=collection_name,
            field_name="metadata.sections",
            field_schema=models.PayloadSchemaType.KEYWORD
        )
        client.create_payload_index(
            collection_name=collection_name,
            field_name="metadata.statutes",
            field_schema=models.PayloadSchemaType.KEYWORD
        )
    except Exception as e:
        # Index might already exist
        pass

def index_pdf_with_okf(file_path: str, max_chunks: int = None, use_llm_extractor: bool = False):
    """Indexes a single PDF with Ontology Knowledge Framework enrichment."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    print(f"\n[OKF Indexer] Loading PDF: {file_path}")
    loader = PyPDFLoader(file_path=file_path)
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(documents=docs)
    if max_chunks:
        chunks = chunks[:max_chunks]

    print(f"[OKF Indexer] Created {len(chunks)} chunks. Extracting ontological metadata...")
    extractor = OntologyExtractor()

    enriched_docs = []
    for i, chunk in enumerate(chunks):
        if use_llm_extractor and i < 15:  # Deep LLM extract for first key pages
            ont = extractor.extract_with_llm(chunk.page_content)
        else:
            ont = extractor.fast_heuristic_extract(chunk.page_content)

        # Attach ontology attributes to LangChain document metadata
        chunk.metadata["discourse_role"] = ont.discourse_role.value
        chunk.metadata["statutes"] = ont.entities.statutes
        chunk.metadata["sections"] = ont.entities.sections
        chunk.metadata["core_principle"] = ont.core_legal_principle or ""

        enriched_docs.append(chunk)

    embedding_model = get_embedding_model()
    client = QdrantClient(url=QDRANT_URL)

    try:
        vector_store = QdrantVectorStore.from_existing_collection(
            url=QDRANT_URL,
            collection_name=OKF_COLLECTION_NAME,
            embedding=embedding_model,
        )
        vector_store.add_documents(enriched_docs)
    except Exception:
        vector_store = QdrantVectorStore.from_documents(
            documents=enriched_docs,
            embedding=embedding_model,
            url=QDRANT_URL,
            collection_name=OKF_COLLECTION_NAME
        )

    ensure_payload_indexes(client, OKF_COLLECTION_NAME)
    print(f"[OKF Indexer] Successfully indexed {len(enriched_docs)} chunks into collection '{OKF_COLLECTION_NAME}'")
    return len(enriched_docs)

def index_all_pdfs_with_okf(pdf_dir: str = "pdf", use_llm_extractor: bool = False):
    """Indexes all PDFs in directory with OKF metadata."""
    abs_pdf_dir = os.path.abspath(pdf_dir)
    pdf_files = glob.glob(os.path.join(abs_pdf_dir, "*.pdf"))

    if not pdf_files:
        print(f"[OKF Indexer] No PDFs found in {abs_pdf_dir}")
        return 0

    print(f"[OKF Indexer] Found {len(pdf_files)} PDFs in {abs_pdf_dir}")
    total = 0
    for pdf_path in pdf_files:
        try:
            total += index_pdf_with_okf(pdf_path, use_llm_extractor=use_llm_extractor)
        except Exception as e:
            print(f"[OKF Indexer] Error processing {pdf_path}: {e}")

    print(f"[OKF Indexer] Finished! Total chunks indexed with ontology: {total}")
    return total

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    pdf_dir = os.path.join(project_root, "pdf")
    index_all_pdfs_with_okf(pdf_dir)
