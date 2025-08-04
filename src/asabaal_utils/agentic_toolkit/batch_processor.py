#!/usr/bin/env python3
"""
Agentic Batch Processing Toolkit

A reusable system for processing large datasets through AI agents using smart batching,
progress tracking, and verification loops. Designed to handle agent limitations with
large datasets while maintaining reliability and resumability.

Future-ready: Built to be easily replaceable when better agent capabilities emerge.
"""

import json
import os
import subprocess
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum


class TokenEstimator:
    """Utility class for estimating token usage to make smart processing decisions"""
    
    @staticmethod
    def estimate_tokens(data: Any) -> int:
        """
        Estimate token count for arbitrary data.
        
        Uses rough heuristics based on string length, JSON structure, etc.
        Not perfect but good enough for batch processing decisions.
        """
        if isinstance(data, str):
            # Rough estimate: ~4 characters per token
            return len(data) // 4
        
        elif isinstance(data, dict):
            # Convert to JSON and estimate
            json_str = json.dumps(data, separators=(',', ':'))
            return len(json_str) // 4
        
        elif isinstance(data, list):
            # Sum tokens for all items
            return sum(TokenEstimator.estimate_tokens(item) for item in data)
        
        else:
            # Convert to string and estimate
            return len(str(data)) // 4
    
    @staticmethod 
    def estimate_prompt_tokens(base_prompt: str, data: Any) -> int:
        """Estimate total tokens for a prompt + data combination"""
        base_tokens = TokenEstimator.estimate_tokens(base_prompt)
        data_tokens = TokenEstimator.estimate_tokens(data)
        
        # Add some overhead for formatting
        overhead = max(100, (base_tokens + data_tokens) // 10)
        
        return base_tokens + data_tokens + overhead
    
    @staticmethod
    def should_use_batch_processing(data: List[Any], 
                                   base_prompt: str = "",
                                   token_threshold: int = 100000,
                                   context_window: int = 200000) -> Dict[str, Any]:
        """
        Smart decision maker for batch processing.
        
        Returns decision data including recommended approach and batch size.
        """
        if not data:
            return {
                "use_batching": False,
                "reason": "empty_dataset",
                "estimated_tokens": 0,
                "recommended_batch_size": 1
            }
        
        # Estimate total tokens
        total_tokens = TokenEstimator.estimate_prompt_tokens(base_prompt, data)
        
        # Calculate tokens per item (for batch sizing)
        avg_tokens_per_item = total_tokens // len(data) if data else 0
        
        # Decision logic
        if total_tokens <= token_threshold:
            return {
                "use_batching": False,
                "reason": "under_threshold",
                "estimated_tokens": total_tokens,
                "threshold": token_threshold,
                "recommended_batch_size": len(data)
            }
        
        elif total_tokens <= context_window * 0.8:  # 80% of context window
            return {
                "use_batching": False,
                "reason": "within_context_window", 
                "estimated_tokens": total_tokens,
                "context_window": context_window,
                "recommended_batch_size": len(data)
            }
        
        else:
            # Calculate optimal batch size
            target_tokens_per_batch = token_threshold // 2  # Conservative
            optimal_batch_size = max(1, target_tokens_per_batch // avg_tokens_per_item)
            
            return {
                "use_batching": True,
                "reason": "exceeds_context_limits",
                "estimated_tokens": total_tokens,
                "recommended_batch_size": optimal_batch_size,
                "estimated_batches": (len(data) + optimal_batch_size - 1) // optimal_batch_size
            }


class BatchStrategy(Enum):
    """Different strategies for batch processing"""
    FIXED_SIZE = "fixed_size"          # Fixed number of items per batch
    ADAPTIVE_SIZE = "adaptive_size"    # Adjust batch size based on success/failure
    TOKEN_AWARE = "token_aware"        # Consider token limits (future enhancement)


@dataclass
class BatchProcessingConfig:
    """Configuration for batch processing operations"""
    batch_size: int = 20
    strategy: BatchStrategy = BatchStrategy.FIXED_SIZE
    max_retries: int = 3
    retry_delay: float = 1.0
    save_progress: bool = True
    verify_completeness: bool = True
    timeout_seconds: int = 300
    debug_mode: bool = False


@dataclass
class ProcessingResult:
    """Result of a batch processing operation"""
    success: bool
    processed_count: int
    total_count: int
    failed_items: List[Any]
    processing_time: float
    error_message: Optional[str] = None


class BatchProcessor(ABC):
    """
    Abstract base class for agentic batch processing.
    
    Subclasses implement specific processing logic while inheriting:
    - Smart batching with verification loops
    - Progress tracking and resumability  
    - Error handling and retry logic
    - Debug mode capabilities
    """
    
    def __init__(self, 
                 output_dir: str,
                 config: Optional[BatchProcessingConfig] = None):
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.config = config or BatchProcessingConfig()
        
        # Progress tracking files
        self.progress_file = self.output_dir / f"{self.__class__.__name__.lower()}_progress.json"
        self.results_file = self.output_dir / f"{self.__class__.__name__.lower()}_results.json"
        
        # Debug directory
        if self.config.debug_mode:
            self.debug_dir = self.output_dir / "debug" / self.__class__.__name__.lower()
            self.debug_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def process_batch(self, batch_items: List[Any], context: Dict[str, Any]) -> List[Any]:
        """
        Process a batch of items using an AI agent.
        
        Args:
            batch_items: List of items to process in this batch
            context: Additional context from previous batches
            
        Returns:
            List of processed results (can be partial if some items failed)
        """
        pass
    
    @abstractmethod
    def process_single_item(self, item: Any, context: Dict[str, Any]) -> Optional[Any]:
        """
        Process a single item (fallback for missed items).
        
        Args:
            item: Single item to process
            context: Context from all previous processing
            
        Returns:
            Processed result or None if failed
        """
        pass
    
    @abstractmethod
    def get_item_identifier(self, item: Any) -> str:
        """
        Get unique identifier for an item (for progress tracking).
        
        Args:
            item: Item to get identifier for
            
        Returns:
            Unique string identifier
        """
        pass
    
    @abstractmethod
    def combine_results(self, all_results: List[Any]) -> Any:
        """
        Combine all processed results into final output.
        
        Args:
            all_results: List of all processed results
            
        Returns:
            Combined final result
        """
        pass
    
    def create_agent_prompt(self, batch_items: List[Any], context: Dict[str, Any]) -> str:
        """
        Create prompt for AI agent. Override if needed.
        
        Args:
            batch_items: Items to process in this batch
            context: Additional context
            
        Returns:
            Prompt string for the agent
        """
        return f"Process these {len(batch_items)} items: {batch_items}"
    
    def call_agent(self, prompt: str) -> str:
        """
        Call AI agent with prompt. Override to use different agents.
        
        Args:
            prompt: Prompt to send to agent
            
        Returns:
            Agent response
        """
        oauth_token = os.environ.get('CLAUDE_CODE_OAUTH_TOKEN')
        if not oauth_token:
            raise Exception("CLAUDE_CODE_OAUTH_TOKEN not available")
        
        if self.config.debug_mode:
            # Save prompt for debugging
            prompt_file = self.debug_dir / f"prompt_{int(time.time())}.txt"
            with open(prompt_file, 'w') as f:
                f.write(prompt)
        
        try:
            cmd = ['claude', '-p', prompt]
            result = subprocess.run(
                cmd,
                env={**os.environ, 'CLAUDE_CODE_OAUTH_TOKEN': oauth_token},
                capture_output=True,
                text=True,
                timeout=None  # No timeout - allow unlimited processing time
            )
            
            if result.returncode != 0:
                raise Exception(f"Agent call failed: {result.stderr}")
            
            response = result.stdout.strip()
            
            if self.config.debug_mode:
                # Save response for debugging
                response_file = self.debug_dir / f"response_{int(time.time())}.txt"
                with open(response_file, 'w') as f:
                    f.write(response)
            
            return response
            
        except subprocess.TimeoutExpired:
            # This should never happen now since timeout=None, but keep for safety
            raise Exception("Agent call timed out (unexpected - timeout was disabled)")
    
    def load_progress(self) -> Dict[str, Any]:
        """Load previous progress if available"""
        if not self.progress_file.exists():
            return {"completed_items": set(), "partial_results": []}
        
        try:
            with open(self.progress_file, 'r') as f:
                data = json.load(f)
                return {
                    "completed_items": set(data.get("completed_items", [])),
                    "partial_results": data.get("partial_results", [])
                }
        except:
            return {"completed_items": set(), "partial_results": []}
    
    def save_progress(self, completed_items: set, partial_results: List[Any]):
        """Save current progress"""
        if not self.config.save_progress:
            return
        
        progress_data = {
            "completed_items": list(completed_items),
            "partial_results": partial_results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_completed": len(completed_items)
        }
        
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(progress_data, f, indent=2)
        except Exception as e:
            if self.config.debug_mode:
                print(f"⚠️  Could not save progress: {e}")
    
    def cleanup_progress(self):
        """Clean up progress files after successful completion"""
        # Only clean up progress file, NOT results file (results are needed by calling code)
        if self.progress_file.exists():
            try:
                self.progress_file.unlink()
            except:
                pass
    
    def process_all(self, items: List[Any], **kwargs) -> ProcessingResult:
        """
        Main entry point: Process all items using smart batch processing.
        
        Args:
            items: List of all items to process
            **kwargs: Additional context passed to processing methods
            
        Returns:
            ProcessingResult with success status and metrics
        """
        start_time = time.time()
        
        if self.config.debug_mode:
            print(f"🔄 Starting batch processing: {len(items)} items")
        
        try:
            # Load previous progress
            progress = self.load_progress()
            completed_items = progress["completed_items"] 
            all_results = progress["partial_results"]
            
            # Filter out already completed items
            remaining_items = [item for item in items if self.get_item_identifier(item) not in completed_items]
            
            if completed_items and self.config.debug_mode:
                print(f"📋 Resuming: {len(completed_items)} items already processed")
                print(f"📊 Processing {len(remaining_items)} remaining items")
            
            # Smart batching decision
            base_prompt = self.create_agent_prompt([], kwargs)  # Get base prompt template
            smart_decision = TokenEstimator.should_use_batch_processing(
                data=remaining_items,
                base_prompt=base_prompt,
                token_threshold=100000,  # 100K tokens
                context_window=200000    # 200K context window
            )
            
            if self.config.debug_mode:
                print(f"🧠 Smart batching decision: {'BATCHING' if smart_decision['use_batching'] else 'SINGLE PASS'}")
                print(f"📊 Reason: {smart_decision['reason']}")
                print(f"🔢 Estimated tokens: {smart_decision['estimated_tokens']:,}")
                if smart_decision['use_batching']:
                    print(f"📦 Recommended batch size: {smart_decision['recommended_batch_size']}")
                    print(f"🔄 Estimated batches: {smart_decision.get('estimated_batches', 'unknown')}")
            
            if smart_decision['use_batching']:
                # Use adaptive batch size from smart decision
                effective_batch_size = min(self.config.batch_size, smart_decision['recommended_batch_size'])
                
                # Batch processing
                for batch_start in range(0, len(remaining_items), effective_batch_size):
                    batch_end = min(batch_start + effective_batch_size, len(remaining_items))
                    batch_items = remaining_items[batch_start:batch_end]
                    
                    batch_num = batch_start // effective_batch_size + 1
                    if self.config.debug_mode:
                        print(f"🔄 Processing batch {batch_num}: items {batch_start+1}-{batch_end}")
                    
                    # Process batch with retries
                    batch_results = self._process_batch_with_retries(batch_items, kwargs)
                    
                    if batch_results:
                        all_results.extend(batch_results)
                        # Mark all batch items as completed (not just those in results)
                        completed_items.update([self.get_item_identifier(item) for item in batch_items])
                        
                        # Save progress after each batch
                        self.save_progress(completed_items, all_results)
            else:
                # Process all items in single pass
                if self.config.debug_mode:
                    print(f"🚀 Processing all {len(remaining_items)} items in single pass")
                
                batch_results = self._process_batch_with_retries(remaining_items, kwargs)
                
                if batch_results:
                    all_results.extend(batch_results)
                    # Mark all items as completed (not just those in results)
                    completed_items.update([self.get_item_identifier(item) for item in remaining_items])
                    
                    # Save progress
                    self.save_progress(completed_items, all_results)
            
            # Verification loop for missed items
            if self.config.verify_completeness:
                self._verify_and_complete(items, completed_items, all_results, kwargs)
            
            # Combine final results
            final_result = self.combine_results(all_results)
            
            # Save final results
            with open(self.results_file, 'w') as f:
                json.dump(final_result, f, indent=2)
            
            # Clean up progress files (but keep results file)
            self.cleanup_progress()
            
            processing_time = time.time() - start_time
            
            # Get actual processed count (handles single-pass correctly)
            actual_processed = final_result.get('actual_item_count', len(all_results))
            
            if self.config.debug_mode:
                print(f"✅ Batch processing completed: {actual_processed}/{len(items)} items")
                print(f"⏱️  Total time: {processing_time:.1f}s")
            
            return ProcessingResult(
                success=True,
                processed_count=actual_processed,
                total_count=len(items),
                failed_items=[],
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            
            if self.config.debug_mode:
                print(f"❌ Batch processing failed: {error_msg}")
            
            return ProcessingResult(
                success=False,
                processed_count=len(progress.get("partial_results", [])),
                total_count=len(items),
                failed_items=[],
                processing_time=processing_time,
                error_message=error_msg
            )
    
    def _process_batch_with_retries(self, batch_items: List[Any], context: Dict[str, Any]) -> List[Any]:
        """Process a batch with retry logic"""
        for attempt in range(self.config.max_retries):
            try:
                return self.process_batch(batch_items, context)
            except Exception as e:
                if attempt == self.config.max_retries - 1:
                    if self.config.debug_mode:
                        print(f"❌ Batch failed after {self.config.max_retries} attempts: {e}")
                    return []
                
                if self.config.debug_mode:
                    print(f"⚠️  Batch attempt {attempt + 1} failed, retrying: {e}")
                
                time.sleep(self.config.retry_delay * (attempt + 1))
        
        return []
    
    def _verify_and_complete(self, all_items: List[Any], completed_items: set, all_results: List[Any], context: Dict[str, Any]):
        """Verify all items processed and handle missed items"""
        all_item_ids = {self.get_item_identifier(item) for item in all_items}
        missed_item_ids = all_item_ids - completed_items
        
        if missed_item_ids:
            if self.config.debug_mode:
                print(f"⚠️  Found {len(missed_item_ids)} missed items, processing individually...")
            
            for item_id in missed_item_ids:
                item = next((item for item in all_items if self.get_item_identifier(item) == item_id), None)
                if item:
                    result = self.process_single_item(item, context)
                    if result:
                        all_results.append(result)
                        completed_items.add(item_id)
                        
                        # Save progress after each individual item
                        self.save_progress(completed_items, all_results)


# Utility function for easy instantiation
def create_batch_processor(processor_class: type, 
                          output_dir: str,
                          config: Optional[BatchProcessingConfig] = None) -> BatchProcessor:
    """
    Factory function to create batch processor instances.
    
    Args:
        processor_class: Class that inherits from BatchProcessor
        output_dir: Directory for output and progress files
        config: Processing configuration
        
    Returns:
        Configured batch processor instance
    """
    return processor_class(output_dir, config)