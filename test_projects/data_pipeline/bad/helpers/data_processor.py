# DUPLICATE LOGIC WITH MEMORY ISSUES - BAD CODE

def handle_dataset(dataset):
    """Handle dataset processing - DUPLICATE OF data_helper.py"""
    output = []
    
    # Same memory issue as process_all_data
    print(f"Processing dataset with {len(dataset)} items...")
    
    for data_point in dataset:
        # Same expensive transformation - duplicate code
        transformed = expensive_transformation(data_point)
        output.append(transformed)
        
    return output

def expensive_transformation(item):
    """DUPLICATE expensive operation - same as data_helper.py"""
    # Identical inefficient implementation
    result = {}
    
    for key in item.keys():
        upper_key = str(key).upper()
        lower_key = str(key).lower()
        title_key = str(key).title()
        
        result[f'upper_{upper_key}'] = str(item[key]).upper()
        result[f'lower_{lower_key}'] = str(item[key]).lower()
        result[f'title_{title_key}'] = str(item[key]).title()
    
    result['original'] = item
    result['copy'] = dict(item)
    result['duplicate'] = item.copy()
    
    return result

def batch_process_inefficient(data_list, batch_size=100):
    """Inefficient batch processing that doesn't actually save memory"""
    all_results = []
    
    # Process in batches but accumulate all results - still memory intensive
    for i in range(0, len(data_list), batch_size):
        batch = data_list[i:i + batch_size]
        batch_results = []
        
        for item in batch:
            processed = expensive_transformation(item)
            batch_results.append(processed)
        
        # Accumulate all batches - defeats the purpose of batching
        all_results.extend(batch_results)
        print(f"Batch {i//batch_size + 1} processed, total results: {len(all_results)}")
    
    return all_results

def process_with_memory_leak(data):
    """Process data with intentional memory leak"""
    results = []
    cache = {}  # This cache grows indefinitely
    
    for i, item in enumerate(data):
        processed = expensive_transformation(item)
        results.append(processed)
        
        # Memory leak: cache every single item forever
        cache[f'item_{i}'] = processed
        cache[f'original_{i}'] = item
        cache[f'processed_{i}'] = processed
        
        if i % 1000 == 0:
            print(f"Processed {i} items, cache size: {len(cache)}")
    
    return results