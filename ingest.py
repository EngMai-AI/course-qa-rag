import os, re, glob
import pandas as pd
from pypdf import PdfReader
from docx import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb

DATA_DIR = "data"
DB_DIR = "chroma_db"
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

def clean(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def load_file(path):
    """Return list of (text, page_or_none)."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        reader = PdfReader(path)
        return [(p.extract_text() or "", i + 1) for i, p in enumerate(reader.pages)]
    if ext == ".docx":
        doc = Document(path)
        return [("\n".join(p.text for p in doc.paragraphs), None)]
    if ext == ".txt":
        with open(path, encoding="utf-8", errors="ignore") as f:
            return [(f.read(), None)]
    if ext == ".csv":
        df = pd.read_csv(path)
        rows = [", ".join(f"{c}: {v}" for c, v in r.items()) for _, r in df.iterrows()]
        return [("\n".join(rows), None)]
    return []

def build_index():
    splitter = RecursiveCharacterTextSplitter(chunk_size=450, chunk_overlap=80)
    model = SentenceTransformer(EMBED_MODEL)
    client = chromadb.PersistentClient(path=DB_DIR)
    try:
        client.delete_collection("courses")
    except Exception:
        pass
    col = client.create_collection("courses", metadata={"hnsw:space": "cosine"})

    ids, docs, metas = [], [], []
    for course in sorted(os.listdir(DATA_DIR)):
        for path in glob.glob(f"{DATA_DIR}/{course}/*"):
            for text, page in load_file(path):
                for j, chunk in enumerate(splitter.split_text(clean(text))):
                    ids.append(f"{course}-{os.path.basename(path)}-{page}-{j}")
                    docs.append(chunk)
                    metas.append({"course": course,
                                  "source": os.path.basename(path),
                                  "page": page or 0})
    embeds = model.encode(docs, show_progress_bar=True).tolist()
    col.add(ids=ids, documents=docs, metadatas=metas, embeddings=embeds)
    print(f"Indexed {len(docs)} chunks from {DATA_DIR}")

if __name__ == "__main__":
    build_index()