from typing import Iterator, Dict, List, Any
from dataclasses import dataclass

@dataclass
class TransformResult:
    processed_count: int
    errors: List[str]
    processing_time: float

class DataTransformer:
    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size
        
    def transform_large_dataset(self, data: Iterator[Dict]) -> Iterator[Dict]:
        """Memory-efficient data transformation using batches"""
        total_processed = 0
        
        for batch in self._batch_generator(data):
            try:
                yield from self._process_batch(batch)
                total_processed += len(batch)
            except Exception as e:
                print(f"Error processing batch: {e}")
                continue
                
    def _batch_generator(self, data: Iterator[Dict]) -> Iterator[List[Dict]]:
        """Split data into memory-efficient batches"""
        batch = []
        for item in data:
            batch.append(item)
            if len(batch) >= self.batch_size:
                yield batch
                batch = []
        if batch:
            yield batch
            
    def _process_batch(self, batch: List[Dict]) -> Iterator[Dict]:
        """Process a single batch efficiently"""
        for item in batch:
            try:
                transformed = self._transform_item(item)
                if transformed:
                    yield transformed
            except Exception as e:
                print(f"Error transforming item {item.get('id', 'unknown')}: {e}")
                continue
                
    def _transform_item(self, item: Dict) -> Dict:
        """Transform individual data item"""
        if not isinstance(item, dict):
            return None
            
        transformed = {
            'id': item.get('id'),
            'name': item.get('name', '').strip().title(),
            'value': float(item.get('value', 0)),
            'category': item.get('category', 'unknown').lower(),
            'processed_at': self._get_timestamp()
        }
        
        # Validate required fields
        if not transformed['id'] or not transformed['name']:
            return None
            
        return transformed
        
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
        
    def transform_with_stats(self, data: Iterator[Dict]) -> tuple[Iterator[Dict], TransformResult]:
        """Transform data with performance statistics"""
        import time
        start_time = time.time()
        errors = []
        processed_count = 0
        
        def transform_generator():
            nonlocal processed_count, errors
            for item in self.transform_large_dataset(data):
                processed_count += 1
                yield item
                
        processing_time = time.time() - start_time
        stats = TransformResult(
            processed_count=processed_count,
            errors=errors,
            processing_time=processing_time
        )
        
        return transform_generator(), stats