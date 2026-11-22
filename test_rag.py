import time

t = time.time()
from rag import retrieve, _client, MODELS
print(f"import + warmup: {time.time() - t:.1f}s")

t = time.time()
hits = retrieve("Bubble sort")
print(f"retrieve: {time.time() - t:.1f}s, hits={len(hits)}")

t = time.time()
r = _client.models.generate_content(model=MODELS[0], contents="Say hi")
print(f"gemini: {time.time() - t:.1f}s -> {r.text}")