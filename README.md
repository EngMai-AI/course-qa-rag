# Course Q&A Assistant (RAG)

A Retrieval-Augmented Generation (RAG) system that answers student questions **using only the course materials** and shows exactly where each answer came from (course, file, and page).

Built with ChromaDB, multilingual sentence embeddings, Gemini, and Gradio.

## Screenshots

**Answer with sources**

<img width="800" alt="What is Docker" src="https://github.com/user-attachments/assets/8d366f3a-31be-4b76-91d6-5bfe3ddbbb1a" />

**Out-of-scope question refused**

<img width="800" alt="Where is Cairo" src="https://github.com/user-attachments/assets/239c47a8-e2d6-467b-98d8-ca8e7fe43d85" />

## Features

- Knowledge base for 3 courses in 4 file formats: **PDF, DOCX, TXT, CSV**
- Per-page text extraction, cleaning, and overlapping chunking
- Multilingual embeddings stored in a persistent ChromaDB collection
- Cosine-distance retriever with a relevance threshold, so unrelated questions are refused **before** the LLM is called
- Answers grounded in the retrieved context only
- Source attribution on every answer (course / file / page)
- Course filter: search one course or all of them
- Model fallback and request timeouts: if one Gemini model is busy or unavailable, the next one is tried

## How it works

```
Files (PDF / DOCX / TXT / CSV)
        |
        v
Extract text per page  ->  Clean  ->  Chunk (450 chars, 80 overlap)
        |
        v
Embed (paraphrase-multilingual-MiniLM-L12-v2)  ->  ChromaDB (cosine)
        |
        v
Question -> embed -> top 4 chunks (distance <= 0.65, optional course filter)
        |
        v
Gemini (answers from context only)  ->  Answer + sources  ->  Gradio UI
```

If no chunk passes the distance threshold, the app returns a "not found" message and never calls Gemini.

## Project structure

```
.
├── app.py             # Gradio interface
├── rag.py             # Retriever, prompt, Gemini call with fallback
├── ingest.py          # Extract, clean, chunk, embed, and index the data
├── make_txt_csv.py    # Converts PPTX slide decks to TXT and CSV
├── check_data.py      # Prints chunk counts per course and file type
├── test_models.py     # Checks that each configured Gemini model responds
├── test_rag.py        # Times retrieval and a Gemini call
├── requirements.txt
└── data/              # Your course files (not included, see below)
```

## Setup

### 1. Install

```bash
git clone https://github.com/EngMai-AI/course-qa-rag.git
cd course-qa-rag
pip install -r requirements.txt
```

### 2. Add your course materials

The course materials are **not included** in this repository. Create one folder per course and put your files inside:

```
data/
├── course1/   # .pdf, .docx, .txt, .csv, .pptx
├── course2/
└── course3/
```

Folder names become the course names in the dropdown.

If you have PowerPoint files, convert them to TXT and CSV first:

```bash
python make_txt_csv.py
```

### 3. Set your Gemini API key

Get a key from [Google AI Studio](https://aistudio.google.com/) and set it as an environment variable. Never commit it.

```bash
# macOS / Linux
export GEMINI_API_KEY="your_key"

# Windows (PowerShell)
$env:GEMINI_API_KEY="your_key"

# Windows (cmd)
set GEMINI_API_KEY=your_key
```

### 4. Build the index

```bash
python ingest.py
python check_data.py    # optional: verify chunk counts per course and file type
```

`ingest.py` rebuilds the `chroma_db/` folder from scratch each time it runs. Re-run it whenever you change the files in `data/`.

### 5. Run the app

```bash
python app.py
```

Open the local URL printed in the terminal (usually http://127.0.0.1:7860).

## Configuration

Settings live at the top of `rag.py` and `ingest.py`:

| Setting | Default | Where | Purpose |
|---|---|---|---|
| `EMBED_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | both | Embedding model (must be the same in both files) |
| `chunk_size` / `chunk_overlap` | `450` / `80` | `ingest.py` | Chunking |
| `TOP_K` | `4` | `rag.py` | Chunks sent to the LLM |
| `MAX_DISTANCE` | `0.65` | `rag.py` | Relevance threshold (lower = stricter) |
| `MODELS` | see file | `rag.py` | Gemini models, tried in order |

If you change `EMBED_MODEL` or the chunking settings, re-run `ingest.py`.

## Design notes

- **Chunk size matches the embedding model.** This model only reads about 128 tokens, so long chunks would have their ends ignored. 450 characters keeps each chunk inside that window.
- **Cleaning is file-type aware.** Collapsing all whitespace would merge CSV rows into one line, so line breaks are preserved.
- **The threshold is a hallucination guard.** Questions unrelated to the course content are refused without calling the LLM.

## Limitations

- Evaluated with manual questions only. There is no formal evaluation set, so no accuracy numbers are reported.
- `MAX_DISTANCE` was tuned by hand and may need adjusting for different materials.
- Scanned PDFs without a text layer are not supported (no OCR).
- Only plain text is extracted from DOCX and PPTX files, not tables or images.

## Next steps

- Corrective RAG: grade retrieved chunks and rewrite weak queries
- Hybrid search (keyword + vector)
- A proper evaluation set with retrieval and answer metrics

## Tech stack

Python, ChromaDB, sentence-transformers, Google Gemini (`google-genai`), Gradio, pypdf, python-docx, python-pptx, pandas, LangChain text splitters.

## Author

**Mai** · [GitHub](https://github.com/EngMai-AI)
