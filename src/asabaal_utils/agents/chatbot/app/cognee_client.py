import os
import asyncio
import logging
import time
from typing import List, Optional, Dict, Any
from .schemas import UsedMemory

# Fix Starlette compatibility issue with Cognee
try:
    import starlette.status
    # Handle different Starlette versions
    if hasattr(starlette.status, 'HTTP_422_UNPROCESSABLE_ENTITY'):
        if not hasattr(starlette.status, 'HTTP_422_UNPROCESSABLE_CONTENT'):
            setattr(starlette.status, 'HTTP_422_UNPROCESSABLE_CONTENT', 
                   getattr(starlette.status, 'HTTP_422_UNPROCESSABLE_ENTITY'))
except (ImportError, AttributeError):
    pass  # Starlette not available or different version

logger = logging.getLogger(__name__)

class CogneeClient:
    """Cognee integration layer for memory management"""
    
    def __init__(self):
        self._initialized = False
        self._cognee: Any = None
        
    async def initialize(self):
        """Initialize Cognee with environment configuration"""
        if self._initialized:
            return
            
        try:
            # Set environment variables for Cognee BEFORE importing
            os.environ["COGNEE_DB_PATH"] = os.environ.get("COGNEE_DB_PATH", "./data/cognee")
            os.environ["COGNEE_LANCEDB_PATH"] = os.environ.get("COGNEE_LANCEDB_PATH", "./data/lancedb")
            
            # Configure Ollama for Cognee
            os.environ["LLM_PROVIDER"] = os.environ.get("LLM_PROVIDER", "ollama")
            os.environ["LLM_MODEL"] = os.environ.get("LLM_MODEL", "qwen3:30b")
            os.environ["LLM_ENDPOINT"] = os.environ.get("LLM_ENDPOINT", "http://localhost:11434/v1")
            os.environ["LLM_API_KEY"] = os.environ.get("LLM_API_KEY", "ollama")
            
            os.environ["EMBEDDING_PROVIDER"] = os.environ.get("EMBEDDING_PROVIDER", "ollama")
            os.environ["EMBEDDING_MODEL"] = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text:latest")
            os.environ["EMBEDDING_ENDPOINT"] = os.environ.get("EMBEDDING_ENDPOINT", "http://localhost:11434/api/embed")
            os.environ["EMBEDDING_DIMENSIONS"] = os.environ.get("EMBEDDING_DIMENSIONS", "768")
            os.environ["HUGGINGFACE_TOKENIZER"] = os.environ.get("HUGGINGFACE_TOKENIZER", "nomic-ai/nomic-embed-text-v1.5")
            
            # Import Cognee only after setting environment variables
            import cognee
            
            # Cognee auto-initializes on import in 0.3.9
            self._cognee = cognee
            self._initialized = True
            logger.info("Cognee initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Cognee: {e}")
            self._initialized = False
            raise
    
    async def add_memory(self, title: str, content: str, tags: List[str] | None = None, memory_id: str | None = None) -> bool:
        """Add memory item to Cognee for indexing"""
        if not self._initialized:
            await self.initialize()
            
        try:
            # Create a formatted document with metadata
            document = f"# {title}\n\n{content}"
            
            if tags:
                document += f"\n\nTags: {', '.join(tags)}"
            
            if memory_id:
                document += f"\n\nMemory ID: {memory_id}"
            
            # Add to Cognee using correct API
            await self._cognee.add(document, dataset_name="chatbot_memories")
            logger.info(f"Added memory to Cognee: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add memory to Cognee: {e}")
            return False
    
    async def cognify_memories(self) -> bool:
        """Process added memories through Cognee's cognification pipeline"""
        if not self._initialized:
            await self.initialize()
            
        try:
            await self._cognee.cognify()
            logger.info("Cognification completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cognify memories: {e}")
            return False
    
    async def search_memories(self, query: str, top_k: int = 5) -> List[UsedMemory]:
        """Search memories using Cognee's semantic search with retry logic"""
        if not self._initialized:
            await self.initialize()
            
        max_retries = 3
        base_delay = 0.5  # Base delay in seconds
        
        for attempt in range(max_retries):
            try:
                # Perform search using correct API
                results = await self._cognee.search(query_text=query, top_k=top_k)
                
                # Convert results to UsedMemory format
                used_memories = []
                
                # Handle different result types from Cognee
                if hasattr(results, 'results'):
                    # CombinedSearchResult format
                    search_results = results.results
                elif isinstance(results, list):
                    # Direct list of results
                    search_results = results
                else:
                    # Single result or other format
                    search_results = [results] if results else []
                
                for result in search_results[:top_k]:
                    # Extract relevant information from Cognee result
                    if hasattr(result, 'text') or hasattr(result, 'content'):
                        title = getattr(result, 'title', 'Untitled Memory')
                        content = getattr(result, 'text', getattr(result, 'content', ''))
                        score = getattr(result, 'score', 0.5)
                        
                        # Create a simple title from content if no title
                        if title == 'Untitled Memory' and content:
                            title = content[:50] + "..." if len(content) > 50 else content
                        
                        used_memories.append(UsedMemory(
                            id=getattr(result, 'id', f"cognee_{len(used_memories)}"),
                            title=title,
                            score=float(score)
                        ))
                    elif isinstance(result, str):
                        # String result (common in GRAPH_COMPLETION)
                        used_memories.append(UsedMemory(
                            id=f"cognee_{len(used_memories)}",
                            title=result[:50] + "..." if len(result) > 50 else result,
                            score=0.8
                        ))
                
                logger.info(f"Cognee search returned {len(used_memories)} results for query: {query}")
                return used_memories
                
            except Exception as e:
                error_msg = str(e).lower()
                is_lock_error = any(keyword in error_msg for keyword in [
                    'lock', 'could not set lock', 'database locked', 
                    'io exception', 'kuzu'
                ])
                
                if is_lock_error and attempt < max_retries - 1:
                    # Exponential backoff for lock errors
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Cognee database locked (attempt {attempt + 1}/{max_retries}), retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"Failed to search memories with Cognee after {attempt + 1} attempts: {e}")
                    return []
        
        return []
    
    async def reset_cognee(self) -> bool:
        """Reset Cognee data (for testing/debugging) with retry logic"""
        if not self._initialized:
            await self.initialize()
            
        max_retries = 3
        base_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                await self._cognee.prune.prune_data()
                await self._cognee.prune.prune_system(metadata=True)
                logger.info("Cognee data reset successfully")
                return True
                
            except Exception as e:
                error_msg = str(e).lower()
                is_lock_error = any(keyword in error_msg for keyword in [
                    'lock', 'could not set lock', 'database locked', 
                    'io exception', 'kuzu'
                ])
                
                if is_lock_error and attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Cognee database locked during reset (attempt {attempt + 1}/{max_retries}), retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"Failed to reset Cognee after {attempt + 1} attempts: {e}")
                    return False
        
        return False
    
    def is_available(self) -> bool:
        """Check if Cognee is properly initialized and available"""
        return self._initialized and self._cognee is not None

# Global instance
_cognee_client = None

def get_cognee_client() -> CogneeClient:
    """Get or create global Cognee client instance"""
    global _cognee_client
    if _cognee_client is None:
        _cognee_client = CogneeClient()
    return _cognee_client

async def ensure_cognee_initialized():
    """Ensure Cognee is initialized (call this at startup)"""
    client = get_cognee_client()
    try:
        await client.initialize()
    except Exception as e:
        logger.warning(f"Cognee initialization failed, will use fallback: {e}")