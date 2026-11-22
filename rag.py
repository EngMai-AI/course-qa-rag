import os
import time
import chromadb
from sentence_transformers import SentenceTransformer
from google import genai
from google.genai import types

BASE = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE, "chroma_db")
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
MODELS = ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite"]   # tried in order
TOP_K = 4
MAX_DISTANCE = 0.65              # above this, the content is not related to the question

_embedder = SentenceTransformer(EMBED_MODEL)
_embedder.encode(["warm up"])    # so the first question is not slow
_col = chromadb.PersistentClient(path=DB_DIR).get_collection("courses")
_client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"],
    http_options=types.HttpOptions(
        timeout=20000,   # 20 seconds per attempt
        retry_options=types.HttpRetryOptions(attempts=1),
    ),
)

NOT_FOUND = ("I don't have the full background on this topic in the available course materials. "
             "Try rephrasing your question or selecting a specific course.")
BUSY = "The answer service is busy right now. Please try again in a moment."

PROMPT = """You are a course assistant. Answer the question using ONLY the context below.
If the context does not contain the answer, reply exactly: {not_found}
Answer in English. Start with a direct answer, then add one short sentence explaining why,
based on the context. Be concise and accurate.

Context:
{context}

Question: {question}
Answer:"""

def retrieve(question, course=None, k=TOP_K):
    q = _embedder.encode([question]).tolist()
    where = {"course": course} if course and course != "All" else None
    res = _col.query(query_embeddings=q, n_results=k, where=where)
    hits = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        if dist <= MAX_DISTANCE:
            hits.append({"text": doc, "meta": meta, "dist": dist})
    return hits

def generate(prompt):
    """Try each model in order; move on if it is busy or unavailable."""
    for name in MODELS:
        for attempt in range(1):
            t = time.time()
            try:
                resp = _client.models.generate_content(model=name, contents=prompt)
                print(f"[gemini] {name} ok in {time.time() - t:.1f}s")
                return (resp.text or "").strip()
            except Exception as e:
                msg = str(e)
                print(f"[gemini] {name} attempt {attempt + 1} failed after {time.time() - t:.1f}s: {msg[:120]}")
                if "404" in msg or "NOT_FOUND" in msg:
                    break                      # model not available, go to the next one
                time.sleep(1.0)                # busy (503/429/timeout): short pause
    return None

def answer(question, course=None):
    t0 = time.time()
    hits = retrieve(question, course)
    print(f"[timing] retrieve={time.time() - t0:.2f}s")
    if not hits:
        return NOT_FOUND, []
    context = "\n\n".join(
        f"[{h['meta']['course']} | {h['meta']['source']} | p.{h['meta']['page']}]\n{h['text']}"
        for h in hits)
    text = generate(PROMPT.format(not_found=NOT_FOUND, context=context, question=question))
    if text is None:
        return BUSY, []
    sources = sorted({(h["meta"]["course"], h["meta"]["source"], h["meta"]["page"]) for h in hits})
    if NOT_FOUND[:40] in text:
        return NOT_FOUND, []
    return text, sources