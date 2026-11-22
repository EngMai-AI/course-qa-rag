import os, collections, chromadb

col = chromadb.PersistentClient(path="chroma_db").get_collection("courses")
counts = collections.Counter(
    (m["course"], os.path.splitext(m["source"])[1].lower()) for m in col.get()["metadatas"])
for key in sorted(counts):
    print(key, counts[key])