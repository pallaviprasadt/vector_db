# Vector DB Landscape - Detailed Student Walkthrough

## 1. What you are building

This class turns the in-memory retrieval idea from Vector Search 101 into a small persistent retrieval system. The project stores vectors, document text, stable IDs, and metadata in Chroma.

The system can restart and reconnect to the same collection:

```text
JSONL corpus -> OpenAI embeddings -> Chroma collection -> local disk
                                          ^
                                          |
question -> OpenAI embedding -> optional metadata filter -> top-k records
```

This project is still retrieval-only. It does not send retrieved text to a generation model.

## 2. Overall design

The project has four layers:

1. **Record layer** - the JSONL corpus stores one complete retrieval record per line.
2. **Database layer** - Chroma persists vectors, text, IDs, and metadata.
3. **Demo layer** - `chroma_demo.py` demonstrates ingestion, search, filtering, and reload.
4. **Test layer** - `test_code.py` verifies the design with temporary storage and fixed vectors.

Each record contains:

```text
id        -> stable identity used for updates and deletes
text      -> content that may later be given to an LLM
embedding -> numeric representation used for similarity search
metadata  -> fields used for filtering, traceability, and access control
```

## 3. Why this class uses Chroma

The slides compare Chroma, Pinecone, and Weaviate. The runnable code uses Chroma because it demonstrates the essential vector-database ideas locally without requiring every student to create another cloud account.

- Chroma is used for the practical.
- Pinecone is discussed as a managed production option.
- Weaviate is discussed as a hybrid-search and deployment-flexibility option.

The purpose is to learn the decision criteria, not to declare one database universally best.

## 4. How to run it

From the `code` folder:

```powershell
.venv\Scripts\python.exe test_code.py
.venv\Scripts\python.exe reset_local_db.py
.venv\Scripts\python.exe chroma_demo.py
.venv\Scripts\python.exe chroma_demo.py
```

Run the demo twice:

- First run: the corpus is embedded and stored.
- Second run: the saved collection is reused without embedding the corpus again.

The demo requires `OPENAI_API_KEY` in `.env`. The test is offline and does not use that key.

## 5. Explanation of every file

### `chroma_demo.py`

This is the main classroom script. It loads structured records, opens persistent storage, ingests only when needed, runs unfiltered and public-only searches, closes and reopens the database, and verifies that records remain on disk.

### `utils.py`

This contains the reusable implementation details: JSONL loading, OpenAI embeddings, Chroma connection, ingestion, querying, and result formatting.

### `reset_local_db.py`

This removes only `stores/chroma`, the local database created by this lesson. Trainers use it before class when students should observe first-time ingestion.

### `test_code.py`

This tests Chroma with two tiny fixed vectors inside a temporary directory. It verifies metadata filtering and persistence without OpenAI and without changing the classroom database.

### `data/mini_knowledge_base.jsonl`

This is the corpus. JSONL means JSON Lines: each line is a separate JSON object. Metadata includes source, department, year, access level, and document type.

### Supporting files

- `requirements.txt` pins Chroma, the OpenAI SDK, and python-dotenv.
- `.env` holds the real secret locally and must remain private.
- `.env.sample` shows safe placeholder configuration.
- `README.md` is the short setup and reference guide.
- `TRAINER_README.md` contains instructor slide mapping, talking points, and reset instructions.

## 6. `chroma_demo.py` walkthrough

### Module constants

- `BASE_DIR` identifies the folder containing the script.
- `DATA_PATH` points to the JSONL corpus.
- `STORE_PATH` points to `stores/chroma`, where the persistent database is created.

### `main()`

`main()` coordinates the database lesson:

1. Calls `load_records()` to read the corpus.
2. Calls `open_collection()` to connect to persistent Chroma storage.
3. Calls `add_records()`. An empty collection is embedded and populated; an existing collection is reused.
4. Calls `search_collection()` without a filter.
5. Calls it again with `{"access_level": "public"}`.
6. Closes the first Chroma client so Windows releases its database files.
7. Reopens the same collection from the same path.
8. Prints its count to prove persistence.
9. Closes the reloaded client cleanly.

The final `if __name__ == "__main__"` block runs `main()` only when the script is executed directly.

## 7. Every function in `utils.py`

### `load_records(jsonl_path)`

Reads JSONL line by line, ignores blank lines, parses JSON, and checks that each record has `id`, `text`, and `metadata`. The line number is reported when input is malformed.

### `create_embeddings(texts)`

Converts input to a list, loads `.env`, verifies `OPENAI_API_KEY`, chooses the configured embedding model or the default, and sends one batched request. Output order matches input order, which keeps vectors aligned with IDs.

### `open_collection(store_path, collection_name='course_knowledge')`

Creates a Chroma `PersistentClient` at the supplied disk path and gets or creates a named collection. It returns the client, so it can be closed cleanly, and the collection, which provides data operations.

### `add_records(collection, records)`

Checks `collection.count()` first. If records exist, it returns `False` and avoids re-embedding. If empty, it embeds the text, extracts aligned ID/document/metadata lists, adds everything to Chroma, and returns `True`.

The Boolean result lets the demo say whether ingestion happened or persisted data was reused.

### `search_collection(collection, query, top_k=3, where=None)`

Embeds the question, queries Chroma, optionally applies a metadata `where` filter, and requests IDs, documents, metadata, and distances. It converts Chroma's nested response into simple result dictionaries.

With `where={"access_level": "public"}`, internal records are not eligible for the result list.

### `print_results(title, results)`

Prints rank, stable ID, distance, department, access level, and text. Lower Chroma distance means a vector is closer to the query.

## 8. `reset_local_db.py` walkthrough

### `STORE_PATH`

The path is built from the script location, limiting deletion to this lesson's known `stores/chroma` directory.

### `main()`

Checks whether the store exists. If it does, `shutil.rmtree()` removes it. Otherwise, the script says there is nothing to remove. It never contacts or deletes a cloud database.

Close any running Chroma script before resetting because Windows cannot delete open database files.

## 9. `test_code.py` walkthrough

### `main()`

The offline test:

1. Loads the real JSONL file and checks the corpus size.
2. Creates a temporary database directory.
3. Opens a separate collection named `offline_test`.
4. Adds one public and one internal record with simple two-dimensional vectors.
5. Temporarily replaces API embedding with a fixed query vector.
6. Calls the real `search_collection()` using a public-only filter.
7. Verifies that only the public ID is returned.
8. Closes and reopens Chroma.
9. Verifies that both stored records persisted.
10. Closes the client so Windows can remove the temporary files.

## 10. What to notice

- The first run embeds and stores the corpus.
- The second run reuses the existing collection.
- Unfiltered search may return semantically relevant internal records.
- Public-only search removes internal records before generation could occur.
- The reloaded collection count proves persistence across processes.

## 11. Metadata filtering versus rule-based ranking

The public access filter is a database eligibility constraint, not a hand-written scoring rule. It determines which records are allowed to compete. Semantic similarity then ranks only eligible records.

This differs from adding arbitrary score bonuses or `if` statements to force documents higher in the ranking.

## 12. Common student mistakes

- Treating a vector database as vectors without stable IDs or metadata.
- Using unstable IDs and creating duplicate records during updates.
- Embedding the entire corpus every time the application starts.
- Applying access control after context has already reached an LLM.
- Changing the embedding model without rebuilding stored vectors.
- Deleting the local store while a Chroma client still has files open.
