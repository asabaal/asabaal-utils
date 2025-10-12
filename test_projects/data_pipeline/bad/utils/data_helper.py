# MEMORY INEFFICIENT DATA PROCESSING - BAD CODE

def process_all_data(data_list):
    """Process all data at once - MEMORY INTENSIVE ANTI-PATTERN"""
    results = []
    
    # Load entire dataset into memory at once
    print(f"Loading {len(data_list)} items into memory...")
    
    for item in data_list:
        # Process each item without batching - memory intensive
        processed = expensive_transformation(item)
        results.append(processed)
        
        # No memory cleanup - will cause issues with large datasets
        if len(results) % 10000 == 0:
            print(f"Processed {len(results)} items - memory growing...")
    
    return results

def expensive_transformation(item):
    """Expensive operation that should be optimized"""
    # Simulate expensive processing that creates many temporary objects
    result = {}
    
    # Inefficient string operations
    for key in item.keys():
        # Create multiple intermediate strings
        upper_key = str(key).upper()
        lower_key = str(key).lower()
        title_key = str(key).title()
        
        # Store all variations - wasteful
        result[f'upper_{upper_key}'] = str(item[key]).upper()
        result[f'lower_{lower_key}'] = str(item[key]).lower()
        result[f'title_{title_key}'] = str(item[key]).title()
    
    # Add redundant data
    result['original'] = item
    result['copy'] = dict(item)
    result['duplicate'] = item.copy()
    
    return result

def load_large_dataset(filename):
    """Load entire file into memory at once"""
    with open(filename, 'r') as f:
        # Read entire file into memory - bad for large files
        content = f.read()
        
    # Split into lines - still all in memory
    lines = content.split('\n')
    
    # Parse all lines at once
    data = []
    for line in lines:
        if line.strip():
            # Parse and store all data immediately
            data.append(eval(line))  # Unsafe eval usage
            
    return data

def process_without_error_handling(data):
    """Process data without proper error handling"""
    results = []
    
    for item in data:
        # No try/catch - will crash entire process on bad data
        processed = expensive_transformation(item)
        results.append(processed)
        
    return results