import json, os, uuid, time
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Tuple
from .schemas import MemoryItem, MemoryCreate, MemoryUpdate, UsedMemory
from .cognee_client import get_cognee_client

logger = logging.getLogger(__name__)

DATA_FILE = os.environ.get("MEMORY_JSON_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "memory.json"))

def filter_memories_by_source(memories: List[MemoryItem], preferred_sources: List[str] | None = None) -> List[MemoryItem]:
    """Filter memories by source_type, with preferred sources getting priority"""
    if not preferred_sources:
        return memories
    
    # Separate memories by source type
    preferred = [m for m in memories if getattr(m, 'source_type', 'user_provided') in preferred_sources]
    other = [m for m in memories if getattr(m, 'source_type', 'user_provided') not in preferred_sources]
    
    # Return preferred memories first, then others
    return preferred + other

def _now() -> datetime:
    return datetime.utcnow()

def _load() -> List[MemoryItem]:
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return [MemoryItem(**x) for x in raw]
    except Exception as e:
        logger.error(f"Error loading memory file: {e}")
        return []

def _save(items: List[MemoryItem]) -> None:
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([x.model_dump(mode="json") for x in items], f, ensure_ascii=False, indent=2, default=str)

def list_items(query: str = "", tags: List[str] | None = None, status: str = "active", limit: int = 50) -> List[MemoryItem]:
    items = _load()
    if status:
        items = [i for i in items if i.status == status]
    if tags:
        items = [i for i in items if set(tags).issubset(set(i.tags or []))]
    if query:
        q = query.lower()
        items = [i for i in items if q in i.title.lower() or q in i.content.lower()]
    return items[:limit]

def create_item(payload: MemoryCreate) -> MemoryItem:
    items = _load()
    
    # Check for duplicates based on title and content similarity
    existing_item = find_duplicate_memory(items, payload.title.strip(), payload.content.strip())
    if existing_item:
        logger.info(f"Found duplicate memory: {existing_item.id}, updating instead of creating new")
        # Update existing memory with new tags if provided
        if payload.tags and set(payload.tags) != set(existing_item.tags or []):
            updated = update_item(existing_item.id, MemoryUpdate(tags=payload.tags))
            return updated or existing_item
        return existing_item
    
    new = MemoryItem(
        id=str(uuid.uuid4()),
        title=payload.title.strip(),
        content=payload.content.strip(),
        tags=payload.tags or [],
        status="active",
        created_at=_now(),
        updated_at=_now(),
        provenance={"source_type": "manual"},
        source_type=payload.source_type
    )
    items.append(new)
    _save(items)
    
    # Add to Cognee asynchronously (non-blocking)
    asyncio.create_task(_add_to_cognee(new))
    
    return new

def find_duplicate_memory(items: List[MemoryItem], title: str, content: str) -> MemoryItem | None:
    """Find duplicate memory based on title and content similarity"""
    title_lower = title.lower()
    content_lower = content.lower()
    
    for item in items:
        if item.status != "active":
            continue
            
        # Exact title match
        if item.title.lower() == title_lower:
            return item
        
        # High content similarity (simple check)
        item_content_lower = item.content.lower()
        if (len(content_lower) > 20 and len(item_content_lower) > 20 and
            (content_lower in item_content_lower or item_content_lower in content_lower)):
            # If one content contains the other and they're substantial
            similarity = max(
                len(content_lower) / len(item_content_lower) if item_content_lower else 0,
                len(item_content_lower) / len(content_lower) if content_lower else 0
            )
            if similarity > 0.8:  # 80% similarity threshold
                return item
    
    return None

async def _add_to_cognee(memory_item: MemoryItem):
    """Add memory item to Cognee for indexing with enhanced metadata"""
    try:
        cognee_client = get_cognee_client()
        
        # Enhanced document with source information for better semantic understanding
        enhanced_content = f"{memory_item.title}\n\n{memory_item.content}"
        
        # Add source information to content for better semantic context
        source_type = getattr(memory_item, 'source_type', 'user_provided')
        if source_type != 'user_provided':
            enhanced_content += f"\n\nSource: {source_type}"
        
        # Add tags for better categorization
        if memory_item.tags:
            enhanced_content += f"\n\nTags: {', '.join(memory_item.tags)}"
        
        success = await cognee_client.add_memory(
            title=memory_item.title,
            content=enhanced_content,
            tags=memory_item.tags or [],
            memory_id=memory_item.id
        )
        if success:
            logger.info(f"Added memory {memory_item.id} ({source_type}) to Cognee")
            # Trigger cognification in background
            asyncio.create_task(cognee_client.cognify_memories())
        else:
            logger.warning(f"Failed to add memory {memory_item.id} to Cognee")
    except Exception as e:
        logger.error(f"Error adding memory {memory_item.id} to Cognee: {e}")

def get_item(item_id: str) -> MemoryItem | None:
    for i in _load():
        if i.id == item_id:
            return i
    return None

def update_item(item_id: str, patch: MemoryUpdate) -> MemoryItem | None:
    items = _load()
    found = None
    for idx, it in enumerate(items):
        if it.id == item_id:
            data = it.model_dump()
            if patch.title is not None:
                data["title"] = patch.title
            if patch.content is not None:
                data["content"] = patch.content
            if patch.tags is not None:
                data["tags"] = patch.tags or []
            if patch.status is not None:
                data["status"] = patch.status
            data["updated_at"] = _now()
            found = MemoryItem(**data)
            items[idx] = found
            break
    if found:
        _save(items)
    return found

def delete_item(item_id: str) -> bool:
    items = _load()
    n_before = len(items)
    items = [i for i in items if i.id != item_id]
    _save(items)
    return len(items) < n_before

async def cognee_retrieval(user_query: str, top_k: int = 5) -> List[UsedMemory]:
    """Cognee-powered semantic search with fallback to keyword search."""
    try:
        cognee_client = get_cognee_client()
        
        # Ensure Cognee is initialized
        if not cognee_client._initialized:
            await cognee_client.initialize()
        
        if cognee_client.is_available():
            results = await cognee_client.search_memories(user_query, top_k)
            if results:
                logger.info(f"Cognee search found {len(results)} results")
                # Filter results to prioritize user-provided information
                return filter_cognee_results(results, user_query, top_k)
            else:
                logger.info("Cognee search returned no results, using fallback")
        else:
            logger.warning("Cognee not available, using fallback search")
    except Exception as e:
        logger.error(f"Cognee search failed: {e}, using fallback")
    
    # Fallback to keyword search
    return stub_retrieval_fallback(user_query, top_k)

def filter_cognee_results(results: List[UsedMemory], query: str, top_k: int = 5) -> List[UsedMemory]:
    """Enhanced memory ranking using semantic relevance and source attribution"""
    if not results:
        return results
    
    # Load memories to get source information
    memories = _load()
    memory_dict = {m.id: m for m in memories}
    
    # Enhance results with source information and calculate enhanced scores
    enhanced_results = []
    for result in results:
        memory = memory_dict.get(result.id)
        if memory:
            # Calculate enhanced score based on multiple factors
            base_score = result.score
            source_boost = 0.0
            
            # Source type boosts
            source_type = getattr(memory, 'source_type', 'user_provided')
            if source_type == 'user_provided':
                source_boost = 0.2  # Boost user-provided information
            elif source_type == 'system_knowledge':
                source_boost = 0.1  # Small boost for system knowledge
            # chatbot_response gets no boost
            
            # Tag-based boosts
            tag_boost = 0.0
            tags = memory.tags or []
            if any(tag in tags for tag in ['personal', 'user', 'profile']):
                tag_boost = 0.15  # Boost for personal information tags
            
            # Recency boost (newer memories get slight boost)
            import datetime
            days_old = (datetime.datetime.utcnow() - memory.updated_at).days
            recency_boost = max(0, 0.05 * (1 - days_old / 30))  # Decay over 30 days
            
            # Calculate final enhanced score
            enhanced_score = min(1.0, base_score + source_boost + tag_boost + recency_boost)
            
            enhanced_results.append({
                'result': result,
                'enhanced_score': enhanced_score,
                'source_type': source_type,
                'tags': tags
            })
    
    # Sort by enhanced score
    enhanced_results.sort(key=lambda x: x['enhanced_score'], reverse=True)
    
    # Return top results with updated scores
    final_results = []
    for item in enhanced_results[:top_k]:
        result = item['result']
        # Create new UsedMemory with enhanced score and source info
        enhanced_result = UsedMemory(
            id=result.id,
            title=result.title,
            score=item['enhanced_score'],
            source_type=item['source_type'],
            tags=item['tags']
        )
        final_results.append(enhanced_result)
    
    return final_results

def stub_retrieval_fallback(user_query: str, top_k: int = 5) -> List[UsedMemory]:
    """Very simple keyword-scoring fallback retrieval."""
    items = _load()
    q = user_query.lower()
    logger.info(f"Searching for query: '{q}' in {len(items)} memory items")
    
    scored: List[Tuple[MemoryItem, float]] = []
    for it in items:
        score = 0.0
        title_match = q in it.title.lower()
        content_match = q in it.content.lower()
        
        if title_match:
            score += 0.7
            logger.info(f"Title match: '{it.title}' contains '{q}'")
        if content_match:
            score += 0.6
            logger.info(f"Content match: '{it.title}' content contains '{q}'")
            
        # tag bonus for exact token matches
        for t in it.tags or []:
            if t.lower() in q.split():
                score += 0.1
                logger.info(f"Tag match: '{it.title}' has tag '{t}' matching query")
                
        if score > 0:
            scored.append((it, min(score, 1.0)))
            logger.info(f"Memory '{it.title}' scored {score}")
    
    scored.sort(key=lambda x: x[1], reverse=True)
    result = [UsedMemory(id=it.id, title=it.title, score=score) for it, score in scored[:top_k]]
    logger.info(f"Returning {len(result)} memory matches: {[r.title for r in result]}")
    return result

# Keep the original function for backward compatibility
def stub_retrieval(user_query: str, top_k: int = 5) -> List[UsedMemory]:
    """Wrapper that uses Cognee with fallback."""
    # This is now async, so we need to handle this differently in calling code
    # For now, return the fallback result
    return stub_retrieval_fallback(user_query, top_k)
