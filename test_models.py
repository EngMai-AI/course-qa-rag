import time
from rag import _client, MODELS

for name in MODELS:
    t = time.time()
    try:
        r = _client.models.generate_content(model=name, contents="Say hi")
        print(f"OK   {name}: {time.time() - t:.1f}s -> {r.text.strip()[:40]}")
    except Exception as e:
        print(f"FAIL {name}: {time.time() - t:.1f}s -> {str(e)[:100]}")