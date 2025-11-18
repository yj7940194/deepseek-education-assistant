"""
Initialize demo data in Neo4j.

This script can be run to seed the knowledge graph with sample educational content.
"""

import asyncio
import logging
from backend.config import get_settings
from backend.utils.neo4j_client import Neo4jClient, init_demo_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Initialize demo data in Neo4j."""
    settings = get_settings()
    
    if not all([settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password]):
        logger.error("Neo4j configuration is incomplete. Please set NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD in .env")
        return
    
    client = Neo4jClient(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    
    try:
        await init_demo_data(client)
        logger.info("Demo data initialization completed successfully!")
    except Exception as e:
        logger.error(f"Error initializing demo data: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())





