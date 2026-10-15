"""Small, reusable helpers for the Vector DB Landscape classroom demo.

The module handles only four jobs: load records, create OpenAI embeddings,
open a persistent Chroma collection, and format query results.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable

from dotenv import load_dotenv


def load_records(jsonl_path: Path) -> list[dict[str, Any]]:
    """Load vector-database records from a JSON Lines file.

    Args:
        jsonl_path: File containing one JSON object per line.

    Returns:
        Records containing ``id``, ``text``, and ``metadata`` fields.
    """
    records = []
    with jsonl_path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            missing = {"id", "text", "metadata"} - record.keys()
            if missing:
                raise ValueError(f"Line {line_number} is missing fields: {sorted(missing)}")
            records.append(record)
    return records


def create_embeddings(texts: Iterable[str]) -> list[list[float]]:
    """Create OpenAI embeddings in one batched request.

    The function reads ``OPENAI_API_KEY`` from this folder's ``.env`` file.
    ``OPENAI_EMBEDDING_MODEL`` is optional and defaults to
    ``text-embedding-3-small``.

    Args:
        texts: Document or query strings to embed.

    Returns:
        Embedding vectors in the same order as the input strings.
    """
    from openai import OpenAI

    text_list = [str(text) for text in texts]
    if not text_list:
        raise ValueError("At least one text is required.")

    load_dotenv(Path(__file__).with_name(".env"))
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Add OPENAI_API_KEY to the .env file before running the demo.")

    model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    response = OpenAI(api_key=api_key).embeddings.create(model=model, input=text_list)
    return [item.embedding for item in response.data]


def open_collection(store_path: Path, collection_name: str = "course_knowledge"):
    """Open or create a Chroma collection stored on disk.

    Args:
        store_path: Directory where Chroma persists its database files.
        collection_name: Stable name for this teaching collection.

    Returns:
        A ``(client, collection)`` pair. The caller closes the client when done.
    """
    import chromadb

    client = chromadb.PersistentClient(path=str(store_path))
    collection = client.get_or_create_collection(name=collection_name)
    return client, collection


def add_records(collection: Any, records: list[dict[str, Any]]) -> bool:
    """Embed and add records only when the collection is empty.

    Args:
        collection: Chroma collection returned by :func:`open_collection`.
        records: Corpus records returned by :func:`load_records`.

    Returns:
        ``True`` when records were embedded and added; ``False`` when the
        existing persistent collection was reused.
    """
    if collection.count() > 0:
        return False

    embeddings = create_embeddings(record["text"] for record in records)
    collection.add(
        ids=[record["id"] for record in records],
        documents=[record["text"] for record in records],
        metadatas=[record["metadata"] for record in records],
        embeddings=embeddings,
    )
    return True


def search_collection(
    collection: Any,
    query: str,
    top_k: int = 3,
    where: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Embed a query and search Chroma, optionally using metadata filters.

    Args:
        collection: Populated Chroma collection.
        query: Natural-language search query.
        top_k: Maximum number of matches to return.
        where: Optional Chroma metadata filter.

    Returns:
        Ranked result dictionaries containing ID, distance, text, and metadata.
    """
    query_embedding = create_embeddings([query])[0]
    raw_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    results = []
    for rank, (record_id, document, metadata, distance) in enumerate(
        zip(
            raw_results["ids"][0],
            raw_results["documents"][0],
            raw_results["metadatas"][0],
            raw_results["distances"][0],
        ),
        start=1,
    ):
        results.append(
            {
                "rank": rank,
                "id": record_id,
                "distance": float(distance),
                "text": document,
                "metadata": metadata,
            }
        )
    return results


def print_results(title: str, results: list[dict[str, Any]]) -> None:
    """Print Chroma results in a compact classroom-friendly format.

    Args:
        title: Heading printed above the matches.
        results: Rows returned by :func:`search_collection`.
    """
    print(f"\n{title}")
    print("-" * len(title))
    for result in results:
        metadata = result["metadata"]
        print(
            f"{result['rank']}. {result['id']} | distance={result['distance']:.3f} | "
            f"department={metadata['department']} | access={metadata['access_level']}"
        )
        print(f"   {result['text']}")
