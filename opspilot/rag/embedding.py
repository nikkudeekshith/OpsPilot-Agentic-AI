from __future__ import annotations
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
except Exception:
    _MODEL = None


def embed_text(text: str) -> list[float]:
    if _MODEL is not None:
        return _MODEL.encode(text).tolist()
    return [0.0] * 384


def embed_texts(texts: list[str]) -> list[list[float]]:
    if _MODEL is not None:
        return _MODEL.encode(texts).tolist()
    return [[0.0] * 384 for _ in texts]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    arr_a = np.array(a)
    arr_b = np.array(b)
    norm_a = np.linalg.norm(arr_a)
    norm_b = np.linalg.norm(arr_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(arr_a, arr_b) / (norm_a * norm_b))
