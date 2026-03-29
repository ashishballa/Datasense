import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.documents import Document

load_dotenv(override=True)

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")

_vectorstore = None
_ensemble_retriever = None
_llm = None

def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.2,
        )
    return _llm

_bm25: BM25Retriever | None = None
_vector_retriever = None

def get_retriever():
    global _vectorstore, _bm25, _vector_retriever
    if _bm25 is None:
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
        )
        _vectorstore = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)

        all_docs = _vectorstore.get()
        docs = [
            Document(page_content=text, metadata=meta)
            for text, meta in zip(all_docs["documents"], all_docs["metadatas"])
        ]
        _bm25 = BM25Retriever.from_documents(docs, k=4)
        _vector_retriever = _vectorstore.as_retriever(
            search_type="mmr", search_kwargs={"k": 4, "fetch_k": 20}
        )
    return _bm25, _vector_retriever

def hybrid_search(question: str) -> list[Document]:
    bm25, vector = get_retriever()
    bm25_docs = bm25.invoke(question)
    vector_docs = vector.invoke(question)
    # merge, deduplicate by content, keep up to 6 unique chunks
    seen, merged = set(), []
    for doc in bm25_docs + vector_docs:
        key = doc.page_content[:120]
        if key not in seen:
            seen.add(key)
            merged.append(doc)
        if len(merged) == 6:
            break
    return merged

from .store import save_message, load_messages, touch_session

# In-memory cache to avoid re-querying DB on every token during streaming
_session_cache: dict[str, list[dict]] = {}

def get_history(session_id: str) -> list[dict]:
    if session_id not in _session_cache:
        _session_cache[session_id] = load_messages(session_id)
    return _session_cache[session_id]

def chat(question: str, session_id: str) -> dict:
    history = get_history(session_id)
    docs = hybrid_search(question)
    context = "\n\n".join(d.page_content for d in docs)

    messages = [
        SystemMessage(content=(
            "You are a helpful home insurance assistant. "
            "Use the policy documents below when relevant, but also draw on your general knowledge "
            "to answer home ownership, real estate, and insurance questions. "
            "Be concise and factual. Use plain text — no markdown asterisks.\n\n"
            f"Relevant policy context:\n{context}"
        ))
    ]
    for turn in history[-6:]:
        if turn["role"] == "user":
            messages.append(HumanMessage(content=turn["content"]))
        else:
            messages.append(AIMessage(content=turn["content"]))
    messages.append(HumanMessage(content=question))

    response = get_llm().invoke(messages)
    answer = response.content

    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer})
    save_message(session_id, "user", question)
    save_message(session_id, "assistant", answer)
    touch_session(session_id)

    return {"answer": answer, "session_id": session_id}

def chat_stream(question: str, session_id: str):
    """Yields answer tokens as a server-sent event stream."""
    history = get_history(session_id)
    docs = hybrid_search(question)
    context = "\n\n".join(d.page_content for d in docs)

    messages = [
        SystemMessage(content=(
            "You are a helpful home insurance assistant. "
            "Use the policy documents below when relevant, but also draw on your general knowledge "
            "to answer home ownership, real estate, and insurance questions. "
            "Be concise and factual. Use plain text — no markdown asterisks.\n\n"
            f"Relevant policy context:\n{context}"
        ))
    ]
    for turn in history[-6:]:
        if turn["role"] == "user":
            messages.append(HumanMessage(content=turn["content"]))
        else:
            messages.append(AIMessage(content=turn["content"]))
    messages.append(HumanMessage(content=question))

    full_answer = []
    for chunk in get_llm().stream(messages):
        token = chunk.content
        if token:
            full_answer.append(token)
            yield token

    answer = "".join(full_answer)
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer})
    save_message(session_id, "user", question)
    save_message(session_id, "assistant", answer)
    touch_session(session_id)

def clear_session(session_id: str):
    _session_cache.pop(session_id, None)
