from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))

from fastembed import TextEmbedding
from sqlalchemy.orm import Session

from app.db.models import TranscriptChunk


MODEL_NAME = "BAAI/bge-small-en-v1.5"

embedding_model = TextEmbedding(model_name=MODEL_NAME)


def retrieve_chunks(
    db: Session,
    query: str,
    top_k: int = 5,
) -> list[TranscriptChunk]:

    query_embedding = list(
        embedding_model.embed([query])
    )[0]

    results = (
        db.query(TranscriptChunk)
        .order_by(
            TranscriptChunk.embedding.cosine_distance(
                query_embedding.tolist()
            )
        )
        .limit(top_k)
        .all()
    )

    return results