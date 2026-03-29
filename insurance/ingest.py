import os
import time
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv(override=True)

DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
BATCH_SIZE = 20

def embed_with_retry(vectorstore, embeddings, batch, is_first, max_retries=5):
    delay = 15
    for attempt in range(max_retries):
        try:
            if is_first:
                return Chroma.from_documents(batch, embedding=embeddings, persist_directory=CHROMA_DIR)
            else:
                vectorstore.add_documents(batch)
                return vectorstore
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                print(f"  Rate limited, waiting {delay}s...")
                time.sleep(delay)
                delay *= 2
            else:
                raise

def ingest():
    docs = []
    for fname in os.listdir(DOCS_DIR):
        if fname.endswith(".pdf") and not fname.endswith(".Identifier"):
            path = os.path.join(DOCS_DIR, fname)
            print(f"Loading {fname}...")
            loader = PyPDFLoader(path)
            docs.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(docs)
    total = len(chunks)
    total_batches = -(-total // BATCH_SIZE)
    print(f"Split into {total} chunks, {total_batches} batches")

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )

    vectorstore = None
    for i in range(0, total, BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"Batch {batch_num}/{total_batches} ({len(batch)} chunks)...")
        vectorstore = embed_with_retry(vectorstore, embeddings, batch, is_first=(i == 0))
        if i + BATCH_SIZE < total:
            time.sleep(10)  # 10s between batches to stay under RPM

    print(f"Done — {total} chunks in ChromaDB at {CHROMA_DIR}")

if __name__ == "__main__":
    ingest()
