import os, glob, csv
from pptx import Presentation

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def slides(path):
    prs = Presentation(path)
    for i, slide in enumerate(prs.slides, 1):
        title = ""
        if slide.shapes.title is not None and slide.shapes.title.has_text_frame:
            title = slide.shapes.title.text.strip()
        parts = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                t = " ".join(p.text.strip() for p in shape.text_frame.paragraphs if p.text.strip())
                if t:
                    parts.append(t)
        text = " ".join(parts)
        if text:
            yield i, title, text

for pptx in glob.glob(os.path.join(DATA, "**", "*.pptx"), recursive=True):
    folder = os.path.dirname(pptx)
    base = os.path.splitext(os.path.basename(pptx))[0]
    rows = list(slides(pptx))

    with open(os.path.join(folder, f"{base}_notes.txt"), "w", encoding="utf-8") as f:
        for i, title, text in rows:
            f.write(f"Slide {i}: {title}\n{text}\n\n")

    with open(os.path.join(folder, f"{base}_slides.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["slide", "title", "text"])
        w.writerows(rows)

    print(f"{base}: {len(rows)} slides -> _notes.txt + _slides.csv in {folder}")