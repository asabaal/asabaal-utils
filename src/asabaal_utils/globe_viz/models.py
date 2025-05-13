"""
Data models for the Globe Visualization System.

This module contains the core data structures that represent entities, metrics,
and visualization configurations for the 3D globe visualization.
"""

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Union, Tuple, Any, Set


class MetricType(enum.Enum):
    """Types of metrics that can be visualized."""
    
    SCALAR = "scalar"  # Single numerical values (e.g., GDP, population)
    CATEGORICAL = "categorical"  # Discrete categories (e.g., development status)
    TEMPORAL = "temporal"  # Time series data
    VECTOR = "vector"  # Direction and magnitude (e.g., migration flows)
    COMPOUND = "compound"  # Composite of multiple metrics
    

@dataclass
class Metric:
    """Definition of a metric that can be visualized on the globe."""
    
    id: str  # Unique identifier
    name: str  # Display name
    description: str  # Detailed description
    unit: Optional[str] = None  # Unit of measurement (if applicable)
    source: Optional[str] = None  # Data source information
    last_updated: datetime = field(default_factory=datetime.now)
    metric_type: MetricType = MetricType.SCALAR
    range: Tuple[Optional[float], Optional[float]] = (None, None)  # Min and max values
    color_scale: List[str] = field(default_factory=list)  # Color scale for visualization
    aggregation_method: str = "average"  # Default aggregation method
    include_in_legend: bool = True  # Whether to include in legend
    render_order: int = 0  # Order for rendering (lower values rendered first)
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata
    
    def __post_init__(self):
        """Validate and process after initialization."""
        # Ensure color scale has at least default values if empty
        if not self.color_scale:
            if self.metric_type == MetricType.CATEGORICAL:
                self.color_scale = ["#4e79a7", "#f28e2c", "#e15759", "#76b7b2", "#59a14f"]
            elif self.metric_type == MetricType.SCALAR:
                self.color_scale = ["#313695", "#4575b4", "#74add1", "#abd9e9", "#fee090", "#fdae61", "#f46d43", "#d73027"]


@dataclass
class MetricData:
    """Container for metric data associated with an entity."""
    
    value: Optional[Union[float, str, List[float], Dict[str, float]]] = None
    history: List[Tuple[datetime, Any]] = field(default_factory=list)
    trend: Optional[float] = None  # Change direction/magnitude
    components: Optional[Dict[str, float]] = None  # Sub-components
    confidence: Optional[float] = None  # Confidence level (0-1)
    ranking: Optional[int] = None  # Rank among all entities
    percentile: Optional[float] = None  # Percentile among all entities
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata


@dataclass
class Entity:
    """Geographic entity that can be visualized on the globe (country, region, etc.)."""
    
    id: str  # Unique identifier
    name: str  # Display name
    type: str = "country"  # Entity type (country, region, etc.)
    parent_id: Optional[str] = None  # Parent entity ID (if any)
    
    # Geographic coordinates
    location: Tuple[float, float] = (0.0, 0.0)  # (latitude, longitude)
    bounding_box: Optional[List[Tuple[float, float]]] = None  # For areas
    
    # Entity data for different metrics
    metrics: Dict[str, MetricData] = field(default_factory=dict)
    
    # Visual properties
    highlighted: bool = False  # Whether entity is highlighted
    visible: bool = True  # Whether entity is visible
    selected: bool = False  # Whether entity is selected
    
    # Additional properties
    aliases: Set[str] = field(default_factory=set)  # Alternative names
    population: Optional[int] = None  # Population count (if applicable)
    area: Optional[float] = None  # Area in km²
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata
    
    def get_metric(self, metric_id: str) -> Optional[MetricData]:
        """Get data for a specific metric."""
        return self.metrics.get(metric_id)
    
    def update_metric(self, metric_id: str, data: MetricData) -> None:
        """Update data for a specific metric."""
        self.metrics[metric_id] = data
        
    def has_metric(self, metric_id: str) -> bool:
        """Check if entity has data for a specific metric."""
        return metric_id in self.metrics
        
    def get_ancestry(self, entity_map: Dict[str, 'Entity']) -> List[str]:
        """Get list of ancestor IDs from parent up to root."""
        ancestry = []
        current_parent = self.parent_id
        
        while current_parent and current_parent in entity_map:
            ancestry.append(current_parent)
            current_parent = entity_map[current_parent].parent_id
            
        return ancestry