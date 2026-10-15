"""Run fast offline checks for the Vector DB Landscape code.

The check uses temporary storage and fixed vectors, so it does not call OpenAI
or alter the classroom Chroma database.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import utils
from utils import load_records, open_collection


def main() -> None:
    """Verify corpus loading, Chroma persistence, search, and filtering."""
    data_path = Path(__file__).parent / "data" / "mini_knowledge_base.jsonl"
    records = load_records(data_path)
    assert len(records) >= 20

    with TemporaryDirectory() as temporary_directory:
        store_path = Path(temporary_directory) / "chroma"
        client, collection = open_collection(store_path, collection_name="offline_test")
        collection.add(
            ids=["public_record", "internal_record"],
            documents=["public career guidance", "internal partner notes"],
            metadatas=[{"access_level": "public"}, {"access_level": "internal"}],
            embeddings=[[1.0, 0.0], [0.0, 1.0]],
        )

        utils.create_embeddings = lambda texts: [[0.0, 1.0] for _ in texts]
        filtered = utils.search_collection(
            collection,
            query="career information",
            top_k=2,
            where={"access_level": "public"},
        )
        assert [row["id"] for row in filtered] == ["public_record"]

        client.close()
        reloaded_client, reloaded = open_collection(
            store_path, collection_name="offline_test"
        )
        assert reloaded.count() == 2
        reloaded_client.close()

    print("All Vector DB Landscape offline checks passed.")


if __name__ == "__main__":
    main()
