"""Remove only the local Chroma store created by ``chroma_demo.py``.

Run this script before class when you want students to see first-time ingestion.
It never contacts a cloud service and never deletes anything outside this folder.
"""

import shutil
from pathlib import Path

STORE_PATH = Path(__file__).parent / "stores" / "chroma"


def main() -> None:
    """Delete the demo's local persistent store when it exists."""
    if STORE_PATH.exists():
        shutil.rmtree(STORE_PATH)
        print(f"Removed local Chroma store: {STORE_PATH}")
    else:
        print("No local Chroma store exists; nothing to remove.")


if __name__ == "__main__":
    main()
