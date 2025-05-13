"""
Data Management System for Globe Visualization.

This module provides functionality for loading, processing, and managing
different data sources for the 3D globe visualization.
"""

import json
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple, Set, Union
import sqlite3

from .models import Entity, Metric, MetricData, MetricType


class DataManager:
    """
    Manages data sources and processing for globe visualization.
    
    This class handles loading data from different sources (CSV, JSON, databases),
    normalizing and processing the data, and providing access to entities and metrics.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the data manager.
        
        Parameters
        ----------
        cache_dir : Optional[Path]
            Directory for caching data. If None, no caching is used.
        """
        self.entities: Dict[str, Entity] = {}
        self.metrics: Dict[str, Metric] = {}
        self.cache_dir = cache_dir or Path.home() / ".globe_viz_cache"
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        
        # Database connection for more efficient storage
        self._db_path = self.cache_dir / "globe_data.db"
        self._init_db()
        
        # Transformation functions registry
        self._transformers: Dict[str, Callable] = {}
        self._aggregators: Dict[str, Callable] = {}
        
        # Register default transformers and aggregators
        self._register_defaults()
        
        self.logger = logging.getLogger(__name__)
    
    def _init_db(self) -> None:
        """Initialize the SQLite database for caching data."""
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entity_cache (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                parent_id TEXT,
                lat REAL,
                lon REAL,
                data TEXT,
                last_updated TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metric_cache (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                unit TEXT,
                source TEXT,
                type TEXT,
                config TEXT,
                last_updated TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS value_cache (
                entity_id TEXT,
                metric_id TEXT,
                value TEXT,
                last_updated TEXT,
                PRIMARY KEY (entity_id, metric_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_source_cache (
                source_id TEXT PRIMARY KEY,
                source_type TEXT NOT NULL,
                source_path TEXT NOT NULL,
                last_updated TEXT,
                metadata TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _register_defaults(self) -> None:
        """Register default transformation and aggregation functions."""
        # Register default transformers
        self._transformers.update({
            "identity": lambda x: x,
            "log10": lambda x: 0 if x <= 0 else (10 if x > 10 else x).log10(),
            "normalize_0_1": lambda x, min_val, max_val: (x - min_val) / (max_val - min_val) if max_val > min_val else 0,
            "scale_by_population": lambda x, population: x / population if population else x,
            "scale_by_area": lambda x, area: x / area if area else x,
            "invert": lambda x: 1.0 / x if x else 0,
            "rank": lambda values: {v: i+1 for i, v in enumerate(sorted(set(values), reverse=True))},
            "percentile": lambda values: {v: i/len(set(values)) for i, v in enumerate(sorted(set(values)))}
        })
        
        # Register default aggregators
        self._aggregators.update({
            "sum": sum,
            "average": lambda values: sum(values) / len(values) if values else 0,
            "median": lambda values: sorted(values)[len(values) // 2] if values else 0,
            "min": min,
            "max": max,
            "count": len,
            "weighted_average": lambda values, weights: sum(v * w for v, w in zip(values, weights)) / sum(weights) if values and weights else 0
        })
    
    def register_transformer(self, name: str, func: Callable) -> None:
        """
        Register a custom data transformation function.
        
        Parameters
        ----------
        name : str
            Name of the transformer
        func : Callable
            Transformation function
        """
        self._transformers[name] = func
    
    def register_aggregator(self, name: str, func: Callable) -> None:
        """
        Register a custom data aggregation function.
        
        Parameters
        ----------
        name : str
            Name of the aggregator
        func : Callable
            Aggregation function
        """
        self._aggregators[name] = func
    
    def load_entities_from_json(self, file_path: Union[str, Path]) -> None:
        """
        Load entities from a JSON file.
        
        Parameters
        ----------
        file_path : Union[str, Path]
            Path to the JSON file containing entity data
        """
        path = Path(file_path)
        if not path.exists():
            self.logger.error(f"Entity file not found: {path}")
            return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Process entities
            for entity_data in data.get('entities', []):
                entity_id = entity_data.get('id')
                if not entity_id:
                    continue
                
                # Create or update entity
                if entity_id in self.entities:
                    entity = self.entities[entity_id]
                    # Update existing entity
                    for key, value in entity_data.items():
                        if key != 'id' and key != 'metrics':
                            setattr(entity, key, value)
                else:
                    # Extract basic entity properties
                    name = entity_data.get('name', entity_id)
                    entity_type = entity_data.get('type', 'country')
                    parent_id = entity_data.get('parent_id')
                    
                    # Extract location
                    loc_data = entity_data.get('location', {})
                    lat = loc_data.get('lat', 0.0)
                    lon = loc_data.get('lon', 0.0)
                    bounding_box = loc_data.get('boundingBox')
                    
                    # Create a new entity
                    entity = Entity(
                        id=entity_id,
                        name=name,
                        type=entity_type,
                        parent_id=parent_id,
                        location=(lat, lon),
                        bounding_box=bounding_box
                    )
                    
                    # Add additional properties
                    for key, value in entity_data.items():
                        if key not in ('id', 'name', 'type', 'parent_id', 'location', 'metrics'):
                            setattr(entity, key, value)
                    
                    self.entities[entity_id] = entity
                
                # Process metrics data if provided
                metrics_data = entity_data.get('metrics', {})
                for metric_id, metric_data in metrics_data.items():
                    if metric_id not in self.metrics:
                        self.logger.warning(f"Metric {metric_id} not found, skipping data for entity {entity_id}")
                        continue
                    
                    # Create or update metric data
                    if isinstance(metric_data, dict):
                        data_obj = MetricData(**metric_data)
                    else:
                        data_obj = MetricData(value=metric_data)
                    
                    entity.metrics[metric_id] = data_obj
            
            self.logger.info(f"Loaded {len(self.entities)} entities from {path}")
            
        except Exception as e:
            self.logger.error(f"Error loading entities from {path}: {e}")
    
    def load_metrics_from_json(self, file_path: Union[str, Path]) -> None:
        """
        Load metric definitions from a JSON file.
        
        Parameters
        ----------
        file_path : Union[str, Path]
            Path to the JSON file containing metric definitions
        """
        path = Path(file_path)
        if not path.exists():
            self.logger.error(f"Metrics file not found: {path}")
            return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Process metrics
            for metric_data in data.get('metrics', []):
                metric_id = metric_data.get('id')
                if not metric_id:
                    continue
                
                # Create or update metric
                if metric_id in self.metrics:
                    metric = self.metrics[metric_id]
                    # Update existing metric
                    for key, value in metric_data.items():
                        if key != 'id':
                            setattr(metric, key, value)
                else:
                    # Extract metric type
                    type_str = metric_data.get('metric_type', 'scalar')
                    try:
                        metric_type = MetricType[type_str.upper()]
                    except (KeyError, AttributeError):
                        metric_type = MetricType.SCALAR
                    
                    # Create a new metric
                    metric = Metric(
                        id=metric_id,
                        name=metric_data.get('name', metric_id),
                        description=metric_data.get('description', ''),
                        unit=metric_data.get('unit'),
                        source=metric_data.get('source'),
                        metric_type=metric_type
                    )
                    
                    # Process range
                    range_data = metric_data.get('range', {})
                    if isinstance(range_data, dict):
                        min_val = range_data.get('min')
                        max_val = range_data.get('max')
                        metric.range = (min_val, max_val)
                    
                    # Process color scale
                    color_scale = metric_data.get('colorScale', [])
                    if color_scale:
                        metric.color_scale = color_scale
                    
                    # Add additional properties
                    for key, value in metric_data.items():
                        if key not in ('id', 'name', 'description', 'unit', 'source', 'metric_type', 'range', 'colorScale'):
                            setattr(metric, key, value)
                    
                    self.metrics[metric_id] = metric
            
            self.logger.info(f"Loaded {len(self.metrics)} metrics from {path}")
            
        except Exception as e:
            self.logger.error(f"Error loading metrics from {path}: {e}")
    
    def load_data_from_csv(self, file_path: Union[str, Path], metric_id: str, 
                           entity_col: str = 'entity_id', value_col: str = 'value',
                           has_header: bool = True) -> None:
        """
        Load metric data from a CSV file.
        
        Parameters
        ----------
        file_path : Union[str, Path]
            Path to the CSV file
        metric_id : str
            ID of the metric to associate with this data
        entity_col : str
            Name or index of the column containing entity IDs
        value_col : str
            Name or index of the column containing values
        has_header : bool
            Whether the CSV file has a header row
        """
        path = Path(file_path)
        if not path.exists():
            self.logger.error(f"CSV file not found: {path}")
            return
        
        # Check if metric exists
        if metric_id not in self.metrics:
            self.logger.error(f"Metric {metric_id} not found, cannot load data")
            return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                
                # Process header row if present
                if has_header:
                    header = next(reader)
                    entity_idx = header.index(entity_col) if isinstance(entity_col, str) else entity_col
                    value_idx = header.index(value_col) if isinstance(value_col, str) else value_col
                else:
                    entity_idx = entity_col if isinstance(entity_col, int) else 0
                    value_idx = value_col if isinstance(value_col, int) else 1
                
                # Process data rows
                count = 0
                for row in reader:
                    if len(row) <= max(entity_idx, value_idx):
                        continue
                    
                    entity_id = row[entity_idx]
                    value_str = row[value_idx]
                    
                    # Skip empty values
                    if not entity_id or not value_str:
                        continue
                    
                    # Convert value to appropriate type
                    try:
                        value = float(value_str)
                    except ValueError:
                        value = value_str
                    
                    # Update entity data if entity exists
                    if entity_id in self.entities:
                        entity = self.entities[entity_id]
                        if metric_id in entity.metrics:
                            entity.metrics[metric_id].value = value
                        else:
                            entity.metrics[metric_id] = MetricData(value=value)
                        count += 1
            
            self.logger.info(f"Loaded {count} data points for metric {metric_id} from {path}")
            
        except Exception as e:
            self.logger.error(f"Error loading data from {path}: {e}")
    
    def compute_derived_metric(self, metric_id: str, source_metrics: List[str], 
                               transform_func: str, filter_func: Optional[Callable] = None) -> None:
        """
        Compute a derived metric based on other metrics.
        
        Parameters
        ----------
        metric_id : str
            ID of the derived metric to create or update
        source_metrics : List[str]
            List of source metric IDs to use for computation
        transform_func : str
            Name of the transformation function to apply
        filter_func : Optional[Callable]
            Optional function to filter entities before computation
        """
        # Check if all source metrics exist
        missing_metrics = [m for m in source_metrics if m not in self.metrics]
        if missing_metrics:
            self.logger.error(f"Source metrics not found: {missing_metrics}")
            return
        
        # Check if transform function exists
        if transform_func not in self._transformers:
            self.logger.error(f"Transform function not found: {transform_func}")
            return
        
        # Create the derived metric if it doesn't exist
        if metric_id not in self.metrics:
            derived_metric = Metric(
                id=metric_id,
                name=f"Derived: {metric_id}",
                description=f"Derived from: {', '.join(source_metrics)} using {transform_func}",
                metric_type=MetricType.SCALAR
            )
            self.metrics[metric_id] = derived_metric
        
        transformer = self._transformers[transform_func]
        count = 0
        
        # Compute the derived metric for each entity
        for entity_id, entity in self.entities.items():
            # Skip if filter function is provided and entity doesn't pass
            if filter_func and not filter_func(entity):
                continue
            
            # Collect values from source metrics
            source_values = {}
            for source_id in source_metrics:
                if source_id in entity.metrics:
                    metric_data = entity.metrics[source_id]
                    if metric_data.value is not None:
                        source_values[source_id] = metric_data.value
            
            # Skip if any source values are missing
            if len(source_values) != len(source_metrics):
                continue
            
            # Apply transformation
            try:
                derived_value = transformer(**source_values)
                
                # Update entity with derived metric
                if metric_id in entity.metrics:
                    entity.metrics[metric_id].value = derived_value
                else:
                    entity.metrics[metric_id] = MetricData(value=derived_value)
                count += 1
            except Exception as e:
                self.logger.error(f"Error computing derived metric for entity {entity_id}: {e}")
        
        self.logger.info(f"Computed derived metric {metric_id} for {count} entities")
    
    def normalize_metric(self, metric_id: str, min_val: Optional[float] = None, 
                        max_val: Optional[float] = None) -> None:
        """
        Normalize values for a metric to a 0-1 range.
        
        Parameters
        ----------
        metric_id : str
            ID of the metric to normalize
        min_val : Optional[float]
            Minimum value for normalization (if None, use actual minimum)
        max_val : Optional[float]
            Maximum value for normalization (if None, use actual maximum)
        """
        if metric_id not in self.metrics:
            self.logger.error(f"Metric {metric_id} not found, cannot normalize")
            return
        
        # Collect all values for the metric
        values = []
        for entity in self.entities.values():
            if metric_id in entity.metrics:
                metric_data = entity.metrics[metric_id]
                if metric_data.value is not None and isinstance(metric_data.value, (int, float)):
                    values.append(metric_data.value)
        
        if not values:
            self.logger.warning(f"No values found for metric {metric_id}, normalization skipped")
            return
        
        # Determine min and max values
        actual_min = min(values)
        actual_max = max(values)
        
        norm_min = min_val if min_val is not None else actual_min
        norm_max = max_val if max_val is not None else actual_max
        
        # Update metric range
        self.metrics[metric_id].range = (norm_min, norm_max)
        
        # Skip normalization if min and max are the same
        if norm_min == norm_max:
            self.logger.warning(f"Min and max values are the same for metric {metric_id}, normalization skipped")
            return
        
        # Apply normalization
        normalizer = self._transformers['normalize_0_1']
        for entity in self.entities.values():
            if metric_id in entity.metrics:
                metric_data = entity.metrics[metric_id]
                if metric_data.value is not None and isinstance(metric_data.value, (int, float)):
                    normalized_value = normalizer(metric_data.value, norm_min, norm_max)
                    # Store original value in metadata
                    if 'original_value' not in metric_data.metadata:
                        metric_data.metadata['original_value'] = metric_data.value
                    metric_data.value = normalized_value
        
        self.logger.info(f"Normalized {len(values)} values for metric {metric_id}")
    
    def compute_rankings(self, metric_id: str, ascending: bool = False) -> None:
        """
        Compute rankings for a metric.
        
        Parameters
        ----------
        metric_id : str
            ID of the metric to rank
        ascending : bool
            Whether lower values should be ranked higher
        """
        if metric_id not in self.metrics:
            self.logger.error(f"Metric {metric_id} not found, cannot compute rankings")
            return
        
        # Collect all values for the metric
        entities_with_values = []
        for entity_id, entity in self.entities.items():
            if metric_id in entity.metrics:
                metric_data = entity.metrics[metric_id]
                if metric_data.value is not None and isinstance(metric_data.value, (int, float)):
                    entities_with_values.append((entity_id, metric_data.value))
        
        if not entities_with_values:
            self.logger.warning(f"No values found for metric {metric_id}, ranking skipped")
            return
        
        # Sort by value (ascending or descending)
        entities_with_values.sort(key=lambda x: x[1], reverse=not ascending)
        
        # Assign rankings
        for rank, (entity_id, _) in enumerate(entities_with_values, 1):
            entity = self.entities[entity_id]
            entity.metrics[metric_id].ranking = rank
            entity.metrics[metric_id].percentile = rank / len(entities_with_values)
        
        self.logger.info(f"Computed rankings for {len(entities_with_values)} entities on metric {metric_id}")
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """
        Get an entity by ID.
        
        Parameters
        ----------
        entity_id : str
            ID of the entity to retrieve
            
        Returns
        -------
        Optional[Entity]
            The entity if found, None otherwise
        """
        return self.entities.get(entity_id)
    
    def get_metric(self, metric_id: str) -> Optional[Metric]:
        """
        Get a metric by ID.
        
        Parameters
        ----------
        metric_id : str
            ID of the metric to retrieve
            
        Returns
        -------
        Optional[Metric]
            The metric if found, None otherwise
        """
        return self.metrics.get(metric_id)
    
    def get_entities_by_type(self, entity_type: str) -> List[Entity]:
        """
        Get all entities of a specific type.
        
        Parameters
        ----------
        entity_type : str
            Type of entities to retrieve
            
        Returns
        -------
        List[Entity]
            List of entities of the specified type
        """
        return [e for e in self.entities.values() if e.type == entity_type]
    
    def get_metrics_by_type(self, metric_type: MetricType) -> List[Metric]:
        """
        Get all metrics of a specific type.
        
        Parameters
        ----------
        metric_type : MetricType
            Type of metrics to retrieve
            
        Returns
        -------
        List[Metric]
            List of metrics of the specified type
        """
        return [m for m in self.metrics.values() if m.metric_type == metric_type]
    
    def filter_entities(self, filter_func: Callable[[Entity], bool]) -> List[Entity]:
        """
        Filter entities based on a custom function.
        
        Parameters
        ----------
        filter_func : Callable[[Entity], bool]
            Function that takes an entity and returns True if it should be included
            
        Returns
        -------
        List[Entity]
            Filtered list of entities
        """
        return [e for e in self.entities.values() if filter_func(e)]
    
    def get_entity_metric_value(self, entity_id: str, metric_id: str) -> Optional[Any]:
        """
        Get the value of a metric for a specific entity.
        
        Parameters
        ----------
        entity_id : str
            ID of the entity
        metric_id : str
            ID of the metric
            
        Returns
        -------
        Optional[Any]
            The metric value if found, None otherwise
        """
        entity = self.entities.get(entity_id)
        if entity and metric_id in entity.metrics:
            return entity.metrics[metric_id].value
        return None
    
    def export_to_json(self, file_path: Union[str, Path]) -> None:
        """
        Export all entities and metrics to a JSON file.
        
        Parameters
        ----------
        file_path : Union[str, Path]
            Path to the output JSON file
        """
        path = Path(file_path)
        
        # Create output structure
        output = {
            "metrics": [self._serialize_metric(m) for m in self.metrics.values()],
            "entities": [self._serialize_entity(e) for e in self.entities.values()]
        }
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, default=self._json_serializer)
            
            self.logger.info(f"Exported data to {path}")
        except Exception as e:
            self.logger.error(f"Error exporting data to {path}: {e}")
    
    def _serialize_metric(self, metric: Metric) -> Dict[str, Any]:
        """Serialize a metric to a dictionary for JSON export."""
        metric_dict = {
            "id": metric.id,
            "name": metric.name,
            "description": metric.description,
            "metricType": metric.metric_type.value,
            "unit": metric.unit,
            "source": metric.source,
            "range": {"min": metric.range[0], "max": metric.range[1]},
            "colorScale": metric.color_scale,
            "aggregationMethod": metric.aggregation_method,
            "lastUpdated": metric.last_updated.isoformat()
        }
        
        # Add metadata
        if metric.metadata:
            metric_dict["metadata"] = metric.metadata
            
        return metric_dict
    
    def _serialize_entity(self, entity: Entity) -> Dict[str, Any]:
        """Serialize an entity to a dictionary for JSON export."""
        entity_dict = {
            "id": entity.id,
            "name": entity.name,
            "type": entity.type,
            "parentId": entity.parent_id,
            "location": {
                "lat": entity.location[0],
                "lon": entity.location[1]
            },
            "metrics": {}
        }
        
        # Add bounding box if available
        if entity.bounding_box:
            entity_dict["location"]["boundingBox"] = entity.bounding_box
            
        # Add population and area if available
        if entity.population is not None:
            entity_dict["population"] = entity.population
        if entity.area is not None:
            entity_dict["area"] = entity.area
            
        # Serialize metrics
        for metric_id, metric_data in entity.metrics.items():
            entity_dict["metrics"][metric_id] = {
                "value": metric_data.value,
                "ranking": metric_data.ranking,
                "percentile": metric_data.percentile
            }
            
            # Add history if available
            if metric_data.history:
                entity_dict["metrics"][metric_id]["history"] = [
                    {"date": date.isoformat(), "value": value}
                    for date, value in metric_data.history
                ]
                
            # Add components if available
            if metric_data.components:
                entity_dict["metrics"][metric_id]["components"] = metric_data.components
                
            # Add metadata if available
            if metric_data.metadata:
                entity_dict["metrics"][metric_id]["metadata"] = metric_data.metadata
        
        # Add aliases if available
        if entity.aliases:
            entity_dict["aliases"] = list(entity.aliases)
            
        # Add metadata if available
        if entity.metadata:
            entity_dict["metadata"] = entity.metadata
            
        return entity_dict
    
    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for handling non-serializable types."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, enum.Enum):
            return obj.value
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return str(obj)