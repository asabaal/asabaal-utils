#!/usr/bin/env python3
"""
Example: Using the Agentic Batch Processing Toolkit

This example shows how to create a custom batch processor for any large dataset
processing task using AI agents.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from asabaal_utils.agentic_toolkit import BatchProcessor, BatchProcessingConfig, BatchStrategy


class DocumentSummaryProcessor(BatchProcessor):
    """
    Example processor that summarizes large collections of documents.
    
    This demonstrates how to create a custom batch processor for any task
    that involves processing many items through an AI agent.
    """
    
    def process_batch(self, batch_items: List[Dict], context: Dict[str, Any]) -> List[Dict]:
        """Process a batch of documents into summaries"""
        
        # Create prompt for summarizing this batch
        document_list = "\n".join([
            f"- {doc['title']}: {doc['content'][:200]}..." 
            for doc in batch_items
        ])
        
        prompt = f"""Summarize these {len(batch_items)} documents. For each document, provide:
1. Main topic (1-2 words)
2. Key points (bullet list)
3. Sentiment (positive/negative/neutral)
4. Word count estimate

Documents:
{document_list}

Return as JSON array with format:
[{{"title": "...", "topic": "...", "key_points": [...], "sentiment": "...", "word_count": 123}}]"""

        try:
            response = self.call_agent(prompt)
            
            # Parse JSON response
            if '```json' in response:
                json_start = response.find('```json') + 7
                json_end = response.find('```', json_start)
                json_str = response[json_start:json_end]
            else:
                json_str = response
            
            summaries = json.loads(json_str)
            return summaries
            
        except Exception as e:
            if self.config.debug_mode:
                print(f"❌ Batch processing failed: {e}")
            return []
    
    def process_single_item(self, item: Dict, context: Dict[str, Any]) -> Optional[Dict]:
        """Process a single document (fallback for missed items)"""
        
        prompt = f"""Summarize this document:
Title: {item['title']}
Content: {item['content']}

Return JSON:
{{"title": "...", "topic": "...", "key_points": [...], "sentiment": "...", "word_count": 123}}"""

        try:
            response = self.call_agent(prompt)
            
            # Simple JSON extraction
            if '{' in response:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                summary = json.loads(response[json_start:json_end])
                return summary
            
        except Exception as e:
            if self.config.debug_mode:
                print(f"❌ Single item processing failed: {e}")
        
        return None
    
    def get_item_identifier(self, item: Dict) -> str:
        """Get unique identifier for a document"""
        return item.get('title', str(hash(item['content'])))
    
    def combine_results(self, all_summaries: List[Dict]) -> Dict[str, Any]:
        """Combine all summaries into final report"""
        
        # Analyze sentiment distribution
        sentiments = [s.get('sentiment', 'neutral') for s in all_summaries]
        sentiment_counts = {
            'positive': sentiments.count('positive'),
            'negative': sentiments.count('negative'), 
            'neutral': sentiments.count('neutral')
        }
        
        # Calculate total word count
        total_words = sum(s.get('word_count', 0) for s in all_summaries)
        
        return {
            "total_documents": len(all_summaries),
            "sentiment_analysis": sentiment_counts,
            "total_word_count": total_words,
            "average_words_per_doc": total_words // len(all_summaries) if all_summaries else 0,
            "document_summaries": all_summaries,
            "processing_complete": True
        }


def main():
    """Example usage of the batch processing toolkit"""
    
    # Sample documents (in practice, these would come from files, databases, APIs, etc.)
    sample_documents = [
        {
            "title": "AI in Healthcare",
            "content": "Artificial intelligence is revolutionizing healthcare through diagnostic tools, treatment optimization, and personalized medicine. Machine learning algorithms can analyze medical images with unprecedented accuracy..."
        },
        {
            "title": "Climate Change Report", 
            "content": "The latest climate data shows alarming trends in global temperature rise. Ice caps are melting at accelerated rates, and weather patterns are becoming increasingly unpredictable..."
        },
        {
            "title": "Remote Work Benefits",
            "content": "Companies adopting remote work policies report increased employee satisfaction and productivity. The flexibility of working from home allows for better work-life balance..."
        },
        # Add more documents to test batch processing
        *[{
            "title": f"Document {i}",
            "content": f"This is sample content for document {i}. It contains various topics and ideas that would need to be summarized by an AI agent."
        } for i in range(4, 50)]  # Create 46 more documents for testing
    ]
    
    print(f"📚 Processing {len(sample_documents)} documents using batch processing toolkit")
    
    # Configure batch processing
    config = BatchProcessingConfig(
        batch_size=10,  # Process 10 documents at a time
        strategy=BatchStrategy.FIXED_SIZE,
        debug_mode=True,
        verify_completeness=True,
        save_progress=True
    )
    
    # Create processor
    output_dir = Path("./batch_processing_output")
    processor = DocumentSummaryProcessor(str(output_dir), config)
    
    # Process all documents
    result = processor.process_all(sample_documents)
    
    # Display results
    if result.success:
        print(f"\n✅ Processing completed successfully!")
        print(f"📊 Processed: {result.processed_count}/{result.total_count} documents")
        print(f"⏱️  Time taken: {result.processing_time:.1f} seconds")
        
        # Load final results
        if processor.results_file.exists():
            with open(processor.results_file, 'r') as f:
                final_report = json.load(f)
            
            print(f"\n📈 Final Report:")
            print(f"   Total documents: {final_report['total_documents']}")
            print(f"   Sentiment breakdown: {final_report['sentiment_analysis']}")
            print(f"   Total words: {final_report['total_word_count']:,}")
            print(f"   Average words per doc: {final_report['average_words_per_doc']}")
    else:
        print(f"\n❌ Processing failed: {result.error_message}")
        print(f"📊 Partial progress: {result.processed_count}/{result.total_count} documents")


if __name__ == "__main__":
    main()