# Agentic Batch Processing Toolkit

A reusable framework for processing large datasets through AI agents with smart batching, progress tracking, and verification loops.

## 🎯 Purpose

This toolkit solves the common problem of **AI agent overwhelm** when processing large datasets. Instead of trying to process hundreds of items in a single agent call (which often results in incomplete processing), this system:

- **Breaks large datasets into manageable batches**
- **Processes items systematically with progress tracking**
- **Verifies completeness with fallback loops**
- **Handles failures gracefully with retry logic**
- **Supports resumability for long-running tasks**

## 🚀 Key Features

### ✅ **Smart Batching**
- Fixed size batching (configurable)
- Adaptive batching (future enhancement)
- Token-aware batching (future enhancement)

### ✅ **Progress Tracking & Resumability**
- Automatic progress saving after each batch
- Resume from interruption points
- Clean up progress files on completion

### ✅ **Verification & Completeness**
- Detect missed items from batch processing
- Individual processing fallback for missed items
- Configurable verification loops

### ✅ **Error Handling**
- Retry logic with exponential backoff
- Graceful degradation on failures
- Debug mode with detailed logging

### ✅ **Extensible Design**
- Abstract base class for custom processors
- Pre-built processors for common tasks (HTML generation, etc.)
- Easy integration with existing workflows

## 📋 Quick Start

### 1. Install Dependencies
```bash
# Ensure Claude CLI is installed and configured
claude setup-token
```

### 2. Create a Custom Processor
```python
from asabaal_utils.agentic_toolkit import BatchProcessor, BatchProcessingConfig

class MyCustomProcessor(BatchProcessor):
    def process_batch(self, batch_items, context):
        # Process a batch of items using AI agent
        prompt = f"Process these {len(batch_items)} items: {batch_items}"
        response = self.call_agent(prompt)
        return self.parse_response(response)
    
    def process_single_item(self, item, context):
        # Process single item (fallback for missed items)
        prompt = f"Process this item: {item}"
        response = self.call_agent(prompt)
        return self.parse_single_response(response)
    
    def get_item_identifier(self, item):
        # Return unique identifier for progress tracking
        return str(item.get('id', hash(str(item))))
    
    def combine_results(self, all_results):
        # Combine all results into final output
        return {"results": all_results, "total": len(all_results)}
```

### 3. Use the Processor
```python
# Configure processing
config = BatchProcessingConfig(
    batch_size=20,
    debug_mode=True,
    verify_completeness=True
)

# Create processor
processor = MyCustomProcessor("./output", config)

# Process your data
result = processor.process_all(your_large_dataset)

if result.success:
    print(f"✅ Processed {result.processed_count} items successfully")
else:
    print(f"❌ Processing failed: {result.error_message}")
```

## 🏗️ Built-in Processors

### DetailedAnalysisProcessor
Specialized for detailed file-level code analysis at class/function level:

```python
from asabaal_utils.agentic_toolkit import create_detailed_analysis_processor

processor = create_detailed_analysis_processor(
    repo_path="./my_repo",
    output_dir="./analysis_output",
    instructions_path="./analysis_instructions.txt",
    output_format_path="./output_format.json",
    batch_size=12,
    debug_mode=True
)

result = processor.process_all(file_list)
```

### HTMLBatchProcessor
Specialized for generating HTML from large file analysis datasets:

```python
from asabaal_utils.agentic_toolkit import create_html_batch_processor

processor = create_html_batch_processor(
    output_dir="./html_output",
    html_template_path="./template.html", 
    instructions_path="./instructions.txt",
    batch_size=25,
    debug_mode=True
)

result = processor.process_all(file_analysis_data)
```

## 📊 Configuration Options

```python
BatchProcessingConfig(
    batch_size=20,                    # Items per batch
    strategy=BatchStrategy.FIXED_SIZE, # Batching strategy
    max_retries=3,                    # Retry attempts per batch
    retry_delay=1.0,                  # Delay between retries
    save_progress=True,               # Enable progress tracking
    verify_completeness=True,         # Enable verification loops
    timeout_seconds=300,              # Agent call timeout
    debug_mode=False                  # Enable debug output
)
```

## 🔍 Debug Mode

Enable debug mode for detailed insight into processing:

```python
config = BatchProcessingConfig(debug_mode=True)
processor = MyProcessor("./output", config)
```

Debug mode provides:
- **Batch-by-batch progress updates**
- **Saved prompts and responses** for inspection
- **Error details and retry attempts**
- **Verification loop details**
- **Performance metrics**

## 📈 Use Cases

### ✅ **Perfect For**
- Processing large file analysis datasets (100+ files)
- Document summarization at scale
- Code analysis and review
- Content generation from templates
- Data transformation and enrichment
- Any task requiring systematic AI agent processing

### ⚠️ **Not Suitable For**
- Small datasets (< 20 items) - use direct agent calls
- Real-time processing requirements
- Tasks requiring cross-item dependencies in single agent call

## 🔮 Future Enhancements

This toolkit is designed to be **future-ready**:

- **Token-aware batching** - Dynamically adjust batch size based on token limits
- **Adaptive sizing** - Learn optimal batch sizes from success/failure patterns  
- **Multi-agent support** - Route different item types to specialized agents
- **Parallel processing** - Process multiple batches concurrently
- **Agent capability detection** - Auto-adjust strategies as agent capabilities improve

## 📝 Examples

See `examples/batch_processing_example.py` for a complete working example showing:
- Custom processor implementation
- Configuration and usage
- Error handling
- Results processing

## 🛠️ Integration

The toolkit integrates seamlessly with existing workflows:

```python
# In your existing code
if len(dataset) > 50:  # Large dataset
    processor = create_batch_processor(MyProcessor, "./output")
    result = processor.process_all(dataset)
else:  # Small dataset  
    result = process_directly(dataset)
```

## 🎯 Design Philosophy

**"Better solutions will emerge, so make this one replaceable."**

This toolkit is designed to:
1. **Solve today's agent limitations** with smart batching
2. **Be easily replaceable** when agent capabilities improve
3. **Provide immediate value** while being future-ready
4. **Abstract complexity** into reusable components

When future AI agents can handle larger contexts reliably, simply swap out the processing strategy while keeping the same interface.

---

*Built for the Asabaal Ventures ecosystem but designed for universal applicability.*