from __future__ import annotations
from opspilot.rag.embedding import embed_text, cosine_similarity
from opspilot.rag.knowledge_base import get_all_chunks


class VectorRetriever:
    def __init__(self):
        self.chunks = get_all_chunks()
        self.embeddings = [embed_text(c["content"]) for c in self.chunks]

    def retrieve(self, query: str, top_k: int = 3, min_score: float = 0.2) -> list[dict]:
        query_emb = embed_text(query)
        scored = []
        for i, chunk in enumerate(self.chunks):
            score = cosine_similarity(query_emb, self.embeddings[i])
            if score >= min_score:
                scored.append((score, chunk))
        def _keyword_score(chunk: dict) -> int:
            qw = set(query.lower().split())
            cw = set(chunk["content"].lower().split())
            return len(qw & cw)
        if not scored:
            scored = [(0.0, c) for c in self.chunks]
            scored.sort(key=lambda x: _keyword_score(x[1]), reverse=True)
            scored = [(max(s, 0.1), c) for s, c in scored if _keyword_score(c) > 0]
        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, chunk in scored[:top_k]:
            results.append({
                "id": chunk["id"],
                "title": chunk["title"],
                "content": chunk["content"],
                "score": round(score, 4),
            })
        return results


class AgenticRetriever:
    def __init__(self, retriever: VectorRetriever):
        self.retriever = retriever
        self.query_history: list[str] = []

    def retrieve(self, query: str, top_k: int = 3, reformulate: bool = True) -> list[dict]:
        self.query_history.append(query)
        results = self.retriever.retrieve(query, top_k=top_k)
        if reformulate and len(results) < 2 and len(self.query_history) < 3:
            reformulated = self._reformulate(query)
            additional = self.retriever.retrieve(reformulated, top_k=top_k)
            seen_ids = {r["id"] for r in results}
            for r in additional:
                if r["id"] not in seen_ids:
                    results.append(r)
        return results

    def _reformulate(self, query: str) -> str:
        reformulations = {
            "latency": "slow response time performance degradation",
            "timeout": "connection timeout database slow query",
            "deployment": "release version change deploy rollback",
            "error": "failure exception fault mistake",
            "database": "postgresql connection pool query performance",
            "memory": "memory leak high utilization OOM",
            "cpu": "high cpu utilization processing bottleneck",
        }
        query_lower = query.lower()
        for kw, replacement in reformulations.items():
            if kw in query_lower:
                return replacement
        return f"{query} investigation troubleshooting root cause"
