import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parents[1])
)

from app.db.database import SessionLocal
from app.rag.retriever import retrieve_chunks


db = SessionLocal()

try:
    query = "How can I improve product activation?"

    results = retrieve_chunks(
        db,
        query,
        top_k=5
    )

    print(f"\nRetrieved {len(results)} chunks:\n")

    for i, result in enumerate(results, start=1):
        print("=" * 80)
        print(f"RESULT {i}")
        print(f"Episode: {result.episode_title}")
        print(f"Source ID: {result.source_id}")
        print(f"Chunk: {result.chunk_index}")
        print()
        print(result.content[:1000])
        print()

finally:
    db.close()