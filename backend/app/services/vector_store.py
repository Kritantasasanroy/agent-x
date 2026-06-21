"""ChromaDB-backed vector store for jobs, with an in-memory fallback."""

from __future__ import annotations

from app.core.config import settings
from app.core.logging import get_logger
from app.services.embeddings import cosine, embed

log = get_logger("vector_store")


class _MemoryStore:
    """Tiny cosine-similarity store used when Chroma is unavailable."""

    def __init__(self) -> None:
        self._docs: dict[str, tuple[list[float], str, dict]] = {}

    def upsert(self, id_: str, text: str, metadata: dict) -> None:
        self._docs[id_] = (embed(text), text, metadata)

    def query(self, text: str, k: int = 5) -> list[dict]:
        q = embed(text)
        scored = [
            {"id": i, "score": cosine(q, v), "document": d, "metadata": m}
            for i, (v, d, m) in self._docs.items()
        ]
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:k]


class VectorStore:
    def __init__(self) -> None:
        self._backend: object
        try:
            import chromadb

            client = chromadb.PersistentClient(path=settings.chroma_dir)
            self._collection = client.get_or_create_collection("jobs")
            self._backend = "chroma"
        except Exception as exc:  # noqa: BLE001
            log.warning("chroma_unavailable_using_memory", error=str(exc))
            self._mem = _MemoryStore()
            self._backend = "memory"

    def upsert(self, id_: str, text: str, metadata: dict | None = None) -> None:
        metadata = metadata or {}
        if self._backend == "chroma":
            self._collection.upsert(
                ids=[id_], documents=[text], embeddings=[embed(text)], metadatas=[metadata]
            )
        else:
            self._mem.upsert(id_, text, metadata)

    def query(self, text: str, k: int = 5) -> list[dict]:
        if self._backend == "chroma":
            res = self._collection.query(query_embeddings=[embed(text)], n_results=k)
            out = []
            ids = res.get("ids", [[]])[0]
            dists = res.get("distances", [[]])[0]
            docs = res.get("documents", [[]])[0]
            metas = res.get("metadatas", [[]])[0]
            for i, idx in enumerate(ids):
                out.append(
                    {
                        "id": idx,
                        "score": 1 - (dists[i] if i < len(dists) else 0),
                        "document": docs[i] if i < len(docs) else "",
                        "metadata": metas[i] if i < len(metas) else {},
                    }
                )
            return out
        return self._mem.query(text, k)


_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
