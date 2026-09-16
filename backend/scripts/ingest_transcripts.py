import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy.orm import Session
from fastembed import TextEmbedding

from app.db.database import SessionLocal
from app.db.models import TranscriptChunk


TRANSCRIPTS_DIR = Path("../data/transcripts/episodes")

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
BATCH_SIZE = 64

# 384-dimensional model — we'll change the DB back to 384.
MODEL_NAME = "BAAI/bge-small-en-v1.5"


def chunk_text(text: str) -> list[str]:
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = min(start + CHUNK_SIZE, len(words))
        chunk = " ".join(words[start:end]).strip()

        if chunk:
            chunks.append(chunk)

        if end == len(words):
            break

        start = end - CHUNK_OVERLAP

    return chunks


def main():
    transcript_files = sorted(
        TRANSCRIPTS_DIR.glob("*/transcript.md")
    )

    print(f"Found {len(transcript_files)} transcript files.")

    if not transcript_files:
        return

    print("Loading embedding model...")
    embedding_model = TextEmbedding(model_name=MODEL_NAME)

    db: Session = SessionLocal()

    try:
        # Remove any partially ingested data.
        db.query(TranscriptChunk).delete()
        db.commit()

        total_chunks = 0

        for episode_number, file_path in enumerate(
            transcript_files, start=1
        ):
            source_id = file_path.parent.name

            text = file_path.read_text(encoding="utf-8")
            chunks = chunk_text(text)

            print(
                f"[{episode_number}/{len(transcript_files)}] "
                f"{source_id}: {len(chunks)} chunks"
            )

            for start in range(0, len(chunks), BATCH_SIZE):
                batch = chunks[start:start + BATCH_SIZE]

                embeddings = list(
                    embedding_model.embed(batch)
                )

                for index, (chunk, embedding) in enumerate(
                    zip(batch, embeddings),
                    start=start
                ):
                    record = TranscriptChunk(
                        source_id=source_id,
                        episode_title=source_id,
                        guest_name=None,
                        source_url=None,
                        content=chunk,
                        chunk_index=index,
                        embedding=embedding.tolist(),
                    )

                    db.add(record)

                db.commit()
                total_chunks += len(batch)

            print(f"    ✓ stored {len(chunks)} chunks")

        print()
        print(
            f"Finished ingestion. "
            f"Inserted {total_chunks} chunks."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()