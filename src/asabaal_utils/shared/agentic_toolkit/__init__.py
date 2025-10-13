"""
Agentic Batch Processing Toolkit

A reusable framework for processing large datasets through AI agents with:
- Smart batching strategies
- Progress tracking and resumability
- Verification loops for completeness
- Error handling and retry logic
- Debug capabilities

Future-ready: Designed to be easily replaceable when agent capabilities improve.
"""

from .batch_processor import (
    BatchProcessor,
    BatchProcessingConfig,
    BatchStrategy,
    ProcessingResult,
    create_batch_processor
)

from .html_batch_processor import (
    HTMLBatchProcessor,
    create_html_batch_processor
)

from .detailed_analysis_processor import (
    DetailedAnalysisProcessor,
    create_detailed_analysis_processor
)

__version__ = "1.0.0"
__all__ = [
    "BatchProcessor",
    "BatchProcessingConfig", 
    "BatchStrategy",
    "ProcessingResult",
    "create_batch_processor",
    "HTMLBatchProcessor",
    "create_html_batch_processor",
    "DetailedAnalysisProcessor",
    "create_detailed_analysis_processor"
]