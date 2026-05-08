"""Qdrant connector — stores endpoint selection text and searches by similarity.

Embeds ENDPOINT_SELECTION_TEXT from schema/endpoint_catalog.py.
Payload only stores {endpoint_name, category} — full schema details are
loaded separately from endpoint_schema.py at selection time.

Embeddings use `sentence-transformers` locally to avoid a local heavy
dependency. Change `EMBEDDING_MODEL` in the `.env` if you prefer another
encoder.
"""
import os
import hashlib

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
)

load_dotenv()

# Use sentence-transformers for embeddings (lazy init)
try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

_EMBED_MODEL = None
_EMBED_DIM = None

def _ensure_embed_model():
    global _EMBED_MODEL, _EMBED_DIM
    if _EMBED_MODEL is None:
        if SentenceTransformer is None:
            raise RuntimeError("sentence-transformers is required for embeddings. Install backend/requirements.txt")
        model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        _EMBED_MODEL = SentenceTransformer(model_name)
        try:
            _EMBED_DIM = _EMBED_MODEL.get_sentence_embedding_dimension()
        except Exception:
            _EMBED_DIM = 384


def _stable_id(name: str) -> int:
    """Stable point ID from endpoint name — survives reordering."""
    return int(hashlib.md5(name.encode()).hexdigest()[:15], 16)


class VectorDB:
    def __init__(self):
        self.client = QdrantClient(path=os.getenv("QDRANT_PATH", "./database/qdrant_data"))
        self.collection = "endpoints"
        _ensure_embed_model()
        self.vector_size = _EMBED_DIM or 384

    def _embed(self, text: str) -> list[float]:
        _ensure_embed_model()
        emb = _EMBED_MODEL.encode(text)
        try:
            return emb.tolist()
        except Exception:
            return list(emb)

    def initialize(self):
        existing = [c.name for c in self.client.get_collections().collections]
        if self.collection in existing:
            self.client.delete_collection(self.collection)
        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
        )

    def add_endpoint(self, endpoint_name: str, selection_text: str, category: str):
        embedding = self._embed(selection_text)
        self.client.upsert(
            collection_name=self.collection,
            points=[PointStruct(
                id=_stable_id(endpoint_name),
                vector=embedding,
                payload={"endpoint_name": endpoint_name, "category": category},
            )],
        )

    def search(self, query: str, category: str | None = None, limit: int = 5) -> list[dict]:
        """Return list of {endpoint_name, category, score}. Names only — no schema details."""
        embedding = self._embed(query)
        qf = None
        if category:
            qf = Filter(must=[FieldCondition(key="category", match=MatchValue(value=category))])
        results = self.client.query_points(
            collection_name=self.collection,
            query=embedding,
            query_filter=qf,
            limit=limit,
        )
        return [
            {
                "endpoint_name": pt.payload["endpoint_name"],
                "category": pt.payload.get("category"),
                "score": round(pt.score, 4),
            }
            for pt in results.points
        ]


vectordb = VectorDB()
