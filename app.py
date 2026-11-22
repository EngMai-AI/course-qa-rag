import chromadb, gradio as gr
from rag import answer, DB_DIR

courses = ["All"] + sorted({m["course"] for m in
           chromadb.PersistentClient(path=DB_DIR).get_collection("courses").get()["metadatas"]})

def ask(question, course):
    if not question.strip():
        return "Please enter a question.", ""
    text, sources = answer(question, course)
    src = "\n".join(f"- {c} / {f}" + (f" (page {p})" if p else "") for c, f, p in sources)
    return text, src or "—"

demo = gr.Interface(
    fn=ask,
    inputs=[gr.Textbox(label="Question", lines=2),
            gr.Dropdown(courses, value="All", label="Course")],
    outputs=[gr.Textbox(label="Answer"), gr.Textbox(label="Sources")],
    title="Course Q&A (RAG)",
    description="Answers come only from the course materials, with sources.")

if __name__ == "__main__":
    demo.launch()