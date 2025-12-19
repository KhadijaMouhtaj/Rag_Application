# debug_rag.py
import requests

# Vérifier les sources
sources = requests.get("http://localhost:5000/list_sources").json()
print(f"📚 Sources: {len(sources)}")
for s in sources:
    print(f"  - {s['name']}: {s['chunks']} chunks")

# Tester une question
if sources:
    payload = {
        "question": "Test question",
        "selected_ids": [s["id"] for s in sources]
    }
    res = requests.post("http://localhost:5000/ask", json=payload).json()
    print(f"\n🔍 Chunks retournés: {len(res.get('chunks', []))}")
    if res.get('chunks'):
        print(f"Premier chunk: {res['chunks'][0][:200]}...")