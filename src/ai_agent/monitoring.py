"""
Monitoring utilities for the AI Agent Framework.

This module provides tools for tracking token usage, costs, and agent performance.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from .models.base import TokenUsage


@dataclass
class RequestStats:
    """Statistics for a single request to an AI model."""
    timestamp: float
    prompt_tokens: int
    completion_tokens: int
    model_name: str
    cost: float
    latency_ms: float
    task_type: str
    success: bool
    

@dataclass
class SessionStats:
    """Aggregated statistics for an agent session."""
    start_time: float
    end_time: Optional[float] = None
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_cost: float = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    requests: List[RequestStats] = field(default_factory=list)
    
    @property
    def duration_seconds(self) -> float:
        """Get the session duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time
    
    @property
    def total_tokens(self) -> int:
        """Get the total number of tokens used."""
        return self.total_prompt_tokens + self.total_completion_tokens
    
    @property
    def success_rate(self) -> float:
        """Get the success rate of requests."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def average_cost_per_request(self) -> float:
        """Get the average cost per request."""
        if self.total_requests == 0:
            return 0.0
        return self.total_cost / self.total_requests
    
    def add_request(self, request: RequestStats) -> None:
        """Add a request to the session statistics.
        
        Args:
            request: The request statistics to add
        """
        self.requests.append(request)
        self.total_prompt_tokens += request.prompt_tokens
        self.total_completion_tokens += request.completion_tokens
        self.total_cost += request.cost
        self.total_requests += 1
        
        if request.success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
    
    def to_dict(self) -> Dict:
        """Convert the session statistics to a dictionary.
        
        Returns:
            A dictionary representation of the session statistics
        """
        return {
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "total_cost": round(self.total_cost, 6),
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": round(self.success_rate, 4),
            "average_cost_per_request": round(self.average_cost_per_request, 6),
            "requests": [
                {
                    "timestamp": datetime.fromtimestamp(r.timestamp).isoformat(),
                    "prompt_tokens": r.prompt_tokens,
                    "completion_tokens": r.completion_tokens,
                    "model_name": r.model_name,
                    "cost": round(r.cost, 6),
                    "latency_ms": round(r.latency_ms, 2),
                    "task_type": r.task_type,
                    "success": r.success,
                }
                for r in self.requests
            ]
        }
    
    def save(self, file_path: Union[str, Path]) -> None:
        """Save the session statistics to a file.
        
        Args:
            file_path: Path to save the file to
        """
        path = Path(file_path)
        
        # Ensure the directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the statistics
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


class CostMonitor:
    """Tracks and reports on token usage and costs for an agent session."""
    
    def __init__(self, session_dir: Optional[Union[str, Path]] = None):
        """Initialize the cost monitor.
        
        Args:
            session_dir: Directory to save session data to
        """
        self.stats = SessionStats(start_time=time.time())
        self.session_dir = Path(session_dir) if session_dir else None
        
        if self.session_dir:
            self.session_dir.mkdir(parents=True, exist_ok=True)
        
        logging.info(f"Cost monitoring started at {datetime.fromtimestamp(self.stats.start_time).isoformat()}")
    
    def record_request(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model_name: str,
        cost: float,
        latency_ms: float,
        task_type: str,
        success: bool = True,
    ) -> None:
        """Record a model request.
        
        Args:
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            model_name: Name of the model used
            cost: Cost of the request
            latency_ms: Latency in milliseconds
            task_type: Type of task (e.g., 'plan', 'implement', 'validate')
            success: Whether the request was successful
        """
        request = RequestStats(
            timestamp=time.time(),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            model_name=model_name,
            cost=cost,
            latency_ms=latency_ms,
            task_type=task_type,
            success=success,
        )
        
        self.stats.add_request(request)
        
        if not success:
            logging.warning(f"Failed request to {model_name} for task: {task_type}")
        
        # Log token usage and cost
        logging.info(
            f"Request: {task_type}, Model: {model_name}, Tokens: {prompt_tokens}+{completion_tokens}, "
            f"Cost: ${cost:.6f}, Latency: {latency_ms:.2f}ms, Success: {success}"
        )
    
    def record_usage(
        self,
        usage: TokenUsage,
        model_name: str,
        latency_ms: float,
        task_type: str,
        success: bool = True,
    ) -> None:
        """Record usage from a standardized TokenUsage object.
        
        Args:
            usage: Token usage information
            model_name: Name of the model used
            latency_ms: Latency in milliseconds
            task_type: Type of task
            success: Whether the request was successful
        """
        self.record_request(
            prompt_tokens=usage.input_tokens,
            completion_tokens=usage.output_tokens,
            model_name=model_name,
            cost=usage.total_cost,
            latency_ms=latency_ms,
            task_type=task_type,
            success=success,
        )
    
    def end_session(self) -> SessionStats:
        """End the monitoring session and save the results.
        
        Returns:
            The final session statistics
        """
        self.stats.end_time = time.time()
        
        duration = self.stats.duration_seconds
        total_cost = self.stats.total_cost
        total_tokens = self.stats.total_tokens
        
        logging.info(
            f"Session ended after {duration:.2f} seconds. "
            f"Total tokens: {total_tokens}, Total cost: ${total_cost:.6f}"
        )
        
        # Save the session statistics if a directory was provided
        if self.session_dir:
            timestamp = datetime.fromtimestamp(self.stats.start_time).strftime("%Y%m%d_%H%M%S")
            stats_file = self.session_dir / f"session_{timestamp}.json"
            self.stats.save(stats_file)
            logging.info(f"Session statistics saved to {stats_file}")
        
        return self.stats
    
    def get_stats(self) -> SessionStats:
        """Get the current session statistics.
        
        Returns:
            The current session statistics
        """
        return self.stats
    
    def get_budget_status(self, budget: float) -> Tuple[float, float, bool]:
        """Get the status of the budget.
        
        Args:
            budget: The budget in USD
            
        Returns:
            A tuple of (cost, remaining, under_budget)
        """
        cost = self.stats.total_cost
        remaining = budget - cost
        under_budget = remaining > 0
        
        return cost, remaining, under_budget
