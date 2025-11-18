from __future__ import annotations

"""Async Neo4j client utilities for knowledge graph access."""

import logging
from typing import Any, Dict, List, Optional

from neo4j import AsyncGraphDatabase, AsyncDriver


logger = logging.getLogger(__name__)


class Neo4jClient:
    """Async Neo4j client handling connection and common queries."""

    def __init__(self, uri: str, user: str, password: str) -> None:
        self._uri = uri
        self._user = user
        self._password = password
        self._driver: Optional[AsyncDriver] = None

    async def _get_driver(self) -> AsyncDriver:
        """Create or return the cached AsyncDriver instance."""

        if self._driver is None:
            logger.info("Initializing Neo4j AsyncDriver")
            self._driver = AsyncGraphDatabase.driver(
                self._uri,
                auth=(self._user, self._password),
            )
        return self._driver

    async def close(self) -> None:
        """Close the underlying driver if it was initialized."""

        if self._driver is not None:
            await self._driver.close()
            self._driver = None

    async def get_related_qa(
        self,
        query: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Fetch candidate question/answer pairs related to the query.

        This uses a simple CONTAINS filter over question and answer text.
        The RAG layer will further re-rank these candidates using embeddings.
        """

        driver = await self._get_driver()
        cypher = """
        MATCH (q:Question)-[:HAS_ANSWER]->(a:Answer)
        OPTIONAL MATCH (t:Topic)-[:HAS_QUESTION]->(q)
        WHERE toLower(q.text) CONTAINS toLower($query)
           OR toLower(a.text) CONTAINS toLower($query)
           OR toLower(t.name) CONTAINS toLower($query)
        RETURN t.name AS topic, q.text AS question, a.text AS answer
        LIMIT $limit
        """

        records: List[Dict[str, Any]] = []
        try:
            async with driver.session() as session:
                result = await session.run(cypher, query=query, limit=limit)
                async for record in result:
                    records.append(record.data())
        except Exception as exc:  # noqa: BLE001
            logger.error("Error querying Neo4j: %s", exc)
        return records


async def init_demo_data(client: Neo4jClient) -> None:
    """
    Initialize a small demo knowledge graph with topics, questions, and answers.

    This function is safe to call multiple times; it uses MERGE to avoid
    creating duplicate nodes.
    """

    driver = await client._get_driver()
    cypher = """
    MERGE (t1:Topic {name: 'Linear Algebra'})
    MERGE (q1:Question {text: 'What is a matrix?'})
    MERGE (a1:Answer {text: 'A matrix is a rectangular array of numbers arranged in rows and columns.'})
    MERGE (t1)-[:HAS_QUESTION]->(q1)
    MERGE (q1)-[:HAS_ANSWER]->(a1)

    MERGE (t2:Topic {name: 'Calculus'})
    MERGE (q2:Question {text: 'What is a derivative?'})
    MERGE (a2:Answer {text: 'A derivative measures how a function changes as its input changes.'})
    MERGE (t2)-[:HAS_QUESTION]->(q2)
    MERGE (q2)-[:HAS_ANSWER]->(a2)

    MERGE (t3:Topic {name: 'Machine Learning'})
    MERGE (q3:Question {text: 'What is supervised learning?'})
    MERGE (a3:Answer {text: 'Supervised learning uses labeled data to train a model to make predictions.'})
    MERGE (t3)-[:HAS_QUESTION]->(q3)
    MERGE (q3)-[:HAS_ANSWER]->(a3)
    """

    try:
        async with driver.session() as session:
            await session.run(cypher)
        logger.info("Demo Neo4j data initialized successfully")
    except Exception as exc:  # noqa: BLE001
        logger.error("Error initializing Neo4j demo data: %s", exc)

