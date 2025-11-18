from __future__ import annotations

"""Retrieval-Augmented Generation (RAG) service."""

import logging
from typing import List, Optional

from backend.utils.embedding_utils import embed_text, rank_by_similarity
from backend.utils.neo4j_client import Neo4jClient


logger = logging.getLogger(__name__)


class RAGService:
    """Service that retrieves and ranks context from Neo4j for a query."""

    def __init__(self, neo4j_client: Optional[Neo4jClient]) -> None:
        self._neo4j_client = neo4j_client

    async def build_context(self, query: str, top_k: int = 5) -> str:
        """
        Build a compact textual context for the given query.

        If Neo4j is not configured or no candidates are found, a fallback
        context string is returned instead.
        """

        if self._neo4j_client is None:
            logger.warning("Neo4j is not configured; using empty RAG context")
            return "No knowledge graph context is available."

        query_embedding = embed_text(query)
        candidates = await self._neo4j_client.get_related_qa(query=query, limit=20)

        if not candidates:
            logger.info("No Neo4j candidates found for query")
            return "No directly related entries were found in the knowledge graph."

        candidate_texts: List[str] = []
        for item in candidates:
            topic = item.get("topic") or "General"
            question = item.get("question") or ""
            answer = item.get("answer") or ""
            snippet = f"Topic: {topic}\nQuestion: {question}\nAnswer: {answer}"
            candidate_texts.append(snippet)

        candidate_embeddings = [embed_text(text) for text in candidate_texts]
        rankings = rank_by_similarity(query_embedding, candidate_embeddings)
        top_indices = [idx for idx, _ in rankings[:top_k]]

        selected_snippets = [candidate_texts[idx] for idx in top_indices]

        context = "You are an educational assistant using the following knowledge graph entries as context.\n\n"
        for i, snippet in enumerate(selected_snippets, start=1):
            context += f"Entry {i}:\n{snippet}\n\n"

        return context.strip()





