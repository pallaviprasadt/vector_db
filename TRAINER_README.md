# Trainer Runbook - Vector DB Landscape

## The script to teach

Run:

```powershell
.venv\Scripts\python.exe chroma_demo.py
```

Run it twice. The first execution should say that the corpus was embedded and stored. The second should say that the existing collection was reused.

## Rehearsal checklist

```powershell
.venv\Scripts\python.exe test_code.py
.venv\Scripts\python.exe reset_local_db.py
.venv\Scripts\python.exe chroma_demo.py
.venv\Scripts\python.exe chroma_demo.py
```

Confirm that the test passes offline, the first demo creates 32 records, the second reuses them, the public-only search excludes `internal` records, and the reloaded count remains 32.

## Recommended live flow (75-90 minutes)

1. Slides 1-7: connect FAISS to the record lifecycle. Open one JSONL line and identify ID, text, embedding (generated later), and metadata.
2. Slides 8-14: compare Chroma, Pinecone, and Weaviate. Explain why the practical uses Chroma: no additional account is required.
3. Slides 15-18: run the unfiltered and filtered searches. Ask why an internal career note must not reach a public answer.
4. Slides 19-21: explain hybrid search and reranking conceptually. They are intentionally not hidden inside this beginner script.
5. Slides 23-24: run the script a second time and connect collection reuse to cost and operations.
6. Slides 25-27: reopen the collection and bridge toward the full RAG pipeline.

## Code call path

```text
main
├─ load_records
├─ open_collection
├─ add_records -> create_embeddings (first run only)
├─ search_collection -> create_embeddings (query)
└─ open_collection again to prove persistence
```

## Questions to ask students

- What information exists around the vector in each record?
- Why is a stable ID necessary for updates?
- Why should access filtering occur before generation?
- What cost is avoided on the second execution?
- When would managed Pinecone be preferable to this local Chroma directory?
- When do exact terms make hybrid retrieval valuable?

## If time is short

Show one JSONL record, run `chroma_demo.py` twice, and focus on persistence plus the public access filter. Keep the vendor comparison to one sentence per tool.

## Reset and safety

`reset_local_db.py` removes only `code/stores/chroma`. It does not contact or delete any cloud database. Run it before class if you want the first-ingestion message. Never display `.env` on screen.
