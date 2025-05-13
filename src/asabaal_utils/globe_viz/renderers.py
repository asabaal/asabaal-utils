"""
3D Globe Rendering Module.

This module provides the rendering components for the 3D globe visualization
system, including the main GlobeRenderer class that handles the rendering of
geographic entities and metrics on a 3D globe.
"""

import cv2
import numpy as np
import os
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union, Callable

from ..base import create_3d_rotation, create_side_rotation
from .models import Entity, Metric, MetricData, MetricType


class MarkerStyle(Enum):
    """Styles for markers on the globe."""
    
    CIRCLE = "circle"
    SQUARE = "square"
    DIAMOND = "diamond"
    TRIANGLE = "triangle"
    STAR = "star"
    CUSTOM = "custom"


class ColorMapType(Enum):
    """Types of color maps for visualization."""
    
    SEQUENTIAL = "sequential"  # Gradient from low to high
    DIVERGING = "diverging"  # Gradient with a midpoint
    CATEGORICAL = "categorical"  # Discrete colors for categories
    CUSTOM = "custom"  # Custom color map


class RenderLayer:
    """A layer for rendering specific elements on the globe."""
    
    def __init__(self, name: str, z_index: int = 0, visible: bool = True):
        """
        Initialize a render layer.
        
        Parameters
        ----------
        name : str
            Name of the layer
        z_index : int
            Z-index for layer ordering (higher values are rendered on top)
        visible : bool
            Whether the layer is visible
        """
        self.name = name
        self.z_index = z_index
        self.visible = visible
        self.entities: List[str] = []  # IDs of entities in this layer
        self.metric_id: Optional[str] = None  # ID of metric visualized in this layer
        self.style: Dict[str, Any] = {}  # Visual styling properties
    
    def add_entity(self, entity_id: str) -> None:
        """Add an entity to this layer."""
        if entity_id not in self.entities:
            self.entities.append(entity_id)
    
    def remove_entity(self, entity_id: str) -> None:
        """Remove an entity from this layer."""
        if entity_id in self.entities:
            self.entities.remove(entity_id)
    
    def clear_entities(self) -> None:
        """Clear all entities from this layer."""
        self.entities = []
    
    def set_metric(self, metric_id: Optional[str]) -> None:
        """Set the metric to visualize in this layer."""
        self.metric_id = metric_id
    
    def update_style(self, **kwargs) -> None:
        """Update styling properties for this layer."""
        self.style.update(kwargs)


class GlobeRenderer:
    """
    Core renderer for the 3D globe visualization.
    
    This class handles the rendering of the globe, entities, and metrics
    using 3D transformations and visualization techniques.
    """
    
    def __init__(self, globe_image_path: Optional[Union[str, Path]] = None,
                 output_dir: Optional[Union[str, Path]] = None,
                 width: int = 800, height: int = 800):
        """
        Initialize the globe renderer.
        
        Parameters
        ----------
        globe_image_path : Optional[Union[str, Path]]
            Path to the base globe image (if None, a default is used)
        output_dir : Optional[Union[str, Path]]
            Directory for saving rendered outputs
        width : int
            Width of the rendered output
        height : int
            Height of the rendered output
        """
        self.width = width
        self.height = height
        
        # Set up output directory
        self.output_dir = Path(output_dir) if output_dir else Path.cwd() / "globe_renders"
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Load or create base globe image
        if globe_image_path and os.path.exists(globe_image_path):
            self.base_globe = cv2.imread(str(globe_image_path))
            self.base_globe = cv2.resize(self.base_globe, (width, height))
        else:
            # Create a simple default globe (blue sphere)
            self.base_globe = self._create_default_globe()
        
        # Initialize rendering properties
        self.layers: Dict[str, RenderLayer] = {}
        self.rotation_x = 0.0  # Rotation around x-axis (vertical tilt)
        self.rotation_y = 0.0  # Rotation around y-axis (horizontal rotation)
        self.zoom = 1.0  # Zoom level
        self.perspective = 2000  # Perspective distance
        
        # Current viewing state
        self.current_metric_id: Optional[str] = None
        self.highlighted_entities: List[str] = []
        self.selected_entities: List[str] = []
        
        # Add standard layers
        self._init_standard_layers()
        
        # Color mapping functions
        self.color_mappers: Dict[str, Callable] = {
            ColorMapType.SEQUENTIAL.value: self._sequential_color_map,
            ColorMapType.DIVERGING.value: self._diverging_color_map,
            ColorMapType.CATEGORICAL.value: self._categorical_color_map
        }
    
    def _create_default_globe(self) -> np.ndarray:
        """Create a default globe image (blue sphere)."""
        # Create a black background
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Add a blue sphere in the center
        center = (self.width // 2, self.height // 2)
        radius = min(self.width, self.height) // 2 - 20
        
        # Draw the sphere
        cv2.circle(img, center, radius, (255, 0, 0), -1)  # Filled blue circle
        
        # Add a simple gradient to make it look more 3D
        for i in range(radius):
            alpha = int(255 * (i / radius) ** 2)
            cv2.circle(img, center, radius - i, (255, alpha, alpha), 1)
        
        # Add grid lines
        for angle in range(0, 180, 15):
            # Convert angle to radians
            rad = np.deg2rad(angle)
            
            # Calculate endpoints for longitude lines (vertical)
            x1 = int(center[0] + radius * np.cos(rad))
            y1 = center[1] - radius
            x2 = int(center[0] + radius * np.cos(rad))
            y2 = center[1] + radius
            cv2.line(img, (x1, y1), (x2, y2), (200, 200, 200), 1)
            
            # Calculate endpoints for latitude lines (horizontal)
            y_offset = int(radius * np.sin(rad))
            x1 = center[0] - int(np.sqrt(radius**2 - y_offset**2))
            x2 = center[0] + int(np.sqrt(radius**2 - y_offset**2))
            cv2.line(img, (x1, center[1] + y_offset), (x2, center[1] + y_offset), (200, 200, 200), 1)
            cv2.line(img, (x1, center[1] - y_offset), (x2, center[1] - y_offset), (200, 200, 200), 1)
        
        return img
    
    def _init_standard_layers(self) -> None:
        """Initialize standard rendering layers."""
        # Base globe layer
        base_layer = RenderLayer("base", z_index=0, visible=True)
        self.layers["base"] = base_layer
        
        # Country outlines layer
        outline_layer = RenderLayer("outlines", z_index=10, visible=True)
        outline_layer.style.update({
            "line_color": (255, 255, 255),
            "line_thickness": 1
        })
        self.layers["outlines"] = outline_layer
        
        # Data visualization layer
        data_layer = RenderLayer("data", z_index=20, visible=True)
        data_layer.style.update({
            "marker_style": MarkerStyle.CIRCLE.value,
            "marker_size": 8,
            "color_map_type": ColorMapType.SEQUENTIAL.value
        })
        self.layers["data"] = data_layer
        
        # Highlight layer for selected entities
        highlight_layer = RenderLayer("highlights", z_index=30, visible=True)
        highlight_layer.style.update({
            "marker_style": MarkerStyle.CIRCLE.value,
            "marker_size": 12,
            "marker_color": (255, 255, 0),  # Yellow highlight
            "line_thickness": 2
        })
        self.layers["highlights"] = highlight_layer
        
        # Label layer for entity names
        label_layer = RenderLayer("labels", z_index=40, visible=True)
        label_layer.style.update({
            "font_scale": 0.5,
            "font_color": (255, 255, 255),
            "font_thickness": 1,
            "bg_color": (0, 0, 0, 128),  # Semi-transparent black background
            "padding": 2
        })
        self.layers["labels"] = label_layer
    
    def add_layer(self, name: str, z_index: int = 50, visible: bool = True) -> RenderLayer:
        """
        Add a new custom rendering layer.
        
        Parameters
        ----------
        name : str
            Name of the layer
        z_index : int
            Z-index for layer ordering
        visible : bool
            Whether the layer is visible
            
        Returns
        -------
        RenderLayer
            The newly created layer
        """
        layer = RenderLayer(name, z_index, visible)
        self.layers[name] = layer
        return layer
    
    def remove_layer(self, name: str) -> None:
        """
        Remove a rendering layer.
        
        Parameters
        ----------
        name : str
            Name of the layer to remove
        """
        if name in self.layers:
            del self.layers[name]
    
    def set_rotation(self, x: float = None, y: float = None) -> None:
        """
        Set the globe rotation angles.
        
        Parameters
        ----------
        x : float, optional
            Rotation angle around x-axis (vertical tilt) in degrees
        y : float, optional
            Rotation angle around y-axis (horizontal rotation) in degrees
        """
        if x is not None:
            self.rotation_x = x
        if y is not None:
            self.rotation_y = y
    
    def rotate(self, delta_x: float = 0.0, delta_y: float = 0.0) -> None:
        """
        Rotate the globe by specified deltas.
        
        Parameters
        ----------
        delta_x : float
            Change in x-axis rotation in degrees
        delta_y : float
            Change in y-axis rotation in degrees
        """
        self.rotation_x += delta_x
        self.rotation_y += delta_y
        
        # Normalize angles to -180 to 180 degrees
        self.rotation_x = ((self.rotation_x + 180) % 360) - 180
        self.rotation_y = ((self.rotation_y + 180) % 360) - 180
    
    def set_zoom(self, zoom: float) -> None:
        """
        Set the zoom level for the globe.
        
        Parameters
        ----------
        zoom : float
            Zoom level (1.0 is default, >1 zooms in, <1 zooms out)
        """
        self.zoom = max(0.1, min(zoom, 5.0))  # Clamp between 0.1 and 5
    
    def zoom_by(self, delta: float) -> None:
        """
        Change the zoom level by a delta.
        
        Parameters
        ----------
        delta : float
            Change in zoom level
        """
        self.set_zoom(self.zoom + delta)
    
    def set_current_metric(self, metric_id: Optional[str]) -> None:
        """
        Set the current metric for visualization.
        
        Parameters
        ----------
        metric_id : Optional[str]
            ID of the metric to visualize (None to clear)
        """
        self.current_metric_id = metric_id
        
        # Update data layer to use this metric
        if "data" in self.layers:
            self.layers["data"].set_metric(metric_id)
    
    def highlight_entity(self, entity_id: str) -> None:
        """
        Highlight an entity on the globe.
        
        Parameters
        ----------
        entity_id : str
            ID of the entity to highlight
        """
        if entity_id not in self.highlighted_entities:
            self.highlighted_entities.append(entity_id)
            self.layers["highlights"].add_entity(entity_id)
    
    def clear_highlights(self) -> None:
        """Clear all entity highlights."""
        self.highlighted_entities = []
        self.layers["highlights"].clear_entities()
    
    def select_entity(self, entity_id: str) -> None:
        """
        Select an entity on the globe.
        
        Parameters
        ----------
        entity_id : str
            ID of the entity to select
        """
        if entity_id not in self.selected_entities:
            self.selected_entities.append(entity_id)
    
    def deselect_entity(self, entity_id: str) -> None:
        """
        Deselect an entity on the globe.
        
        Parameters
        ----------
        entity_id : str
            ID of the entity to deselect
        """
        if entity_id in self.selected_entities:
            self.selected_entities.remove(entity_id)
    
    def clear_selections(self) -> None:
        """Clear all entity selections."""
        self.selected_entities = []
    
    def _sequential_color_map(self, value: float, min_val: float, max_val: float, 
                              colors: List[Tuple[int, int, int]]) -> Tuple[int, int, int]:
        """
        Map a value to a color using a sequential color map.
        
        Parameters
        ----------
        value : float
            Value to map to a color
        min_val : float
            Minimum value in the range
        max_val : float
            Maximum value in the range
        colors : List[Tuple[int, int, int]]
            List of RGB color tuples representing the color gradient
            
        Returns
        -------
        Tuple[int, int, int]
            RGB color tuple
        """
        if min_val == max_val:
            return colors[0]
        
        # Normalize value to [0, 1]
        norm_value = (value - min_val) / (max_val - min_val)
        norm_value = max(0.0, min(1.0, norm_value))  # Clamp to [0, 1]
        
        # Map to color index
        if len(colors) == 1:
            return colors[0]
        
        idx = norm_value * (len(colors) - 1)
        lower_idx = int(idx)
        upper_idx = min(lower_idx + 1, len(colors) - 1)
        
        # Interpolate between colors
        weight = idx - lower_idx
        lower_color = colors[lower_idx]
        upper_color = colors[upper_idx]
        
        r = int(lower_color[0] * (1 - weight) + upper_color[0] * weight)
        g = int(lower_color[1] * (1 - weight) + upper_color[1] * weight)
        b = int(lower_color[2] * (1 - weight) + upper_color[2] * weight)
        
        return (r, g, b)
    
    def _diverging_color_map(self, value: float, min_val: float, max_val: float, 
                             colors: List[Tuple[int, int, int]], 
                             mid_val: Optional[float] = None) -> Tuple[int, int, int]:
        """
        Map a value to a color using a diverging color map.
        
        Parameters
        ----------
        value : float
            Value to map to a color
        min_val : float
            Minimum value in the range
        max_val : float
            Maximum value in the range
        colors : List[Tuple[int, int, int]]
            List of RGB color tuples representing the color gradient
        mid_val : Optional[float]
            Midpoint value (defaults to average of min and max)
            
        Returns
        -------
        Tuple[int, int, int]
            RGB color tuple
        """
        if min_val == max_val:
            return colors[len(colors) // 2]
        
        # Use default midpoint if not specified
        if mid_val is None:
            mid_val = (min_val + max_val) / 2
        
        # Ensure colors list has odd length
        if len(colors) % 2 == 0:
            # If even, use first half for below midpoint, second half for above
            mid_idx = len(colors) // 2
            below_colors = colors[:mid_idx]
            above_colors = colors[mid_idx:]
        else:
            # If odd, use middle color at midpoint
            mid_idx = len(colors) // 2
            below_colors = colors[:mid_idx+1]
            above_colors = colors[mid_idx:]
        
        # Map to appropriate color range
        if value <= mid_val:
            return self._sequential_color_map(value, min_val, mid_val, below_colors)
        else:
            return self._sequential_color_map(value, mid_val, max_val, above_colors)
    
    def _categorical_color_map(self, category: Union[str, int], 
                               categories: List[Union[str, int]],
                               colors: List[Tuple[int, int, int]]) -> Tuple[int, int, int]:
        """
        Map a category to a color.
        
        Parameters
        ----------
        category : Union[str, int]
            Category to map to a color
        categories : List[Union[str, int]]
            List of all possible categories
        colors : List[Tuple[int, int, int]]
            List of RGB color tuples for each category
            
        Returns
        -------
        Tuple[int, int, int]
            RGB color tuple
        """
        try:
            idx = categories.index(category) % len(colors)
            return colors[idx]
        except (ValueError, IndexError):
            # Default color for unknown categories
            return (128, 128, 128)
    
    def render_globe(self, entities: Dict[str, Entity], metrics: Dict[str, Metric]) -> np.ndarray:
        """
        Render the 3D globe with entities and metrics.
        
        Parameters
        ----------
        entities : Dict[str, Entity]
            Dictionary of entities to render
        metrics : Dict[str, Metric]
            Dictionary of metrics
            
        Returns
        -------
        np.ndarray
            Rendered image
        """
        # Start with a copy of the base globe
        globe_img = self.base_globe.copy()
        
        # Apply 3D rotation to the base globe
        rotated_globe = self._apply_rotation(globe_img)
        
        # Sort layers by z-index
        sorted_layers = sorted(self.layers.values(), key=lambda l: l.z_index)
        
        # Render each visible layer
        for layer in sorted_layers:
            if not layer.visible:
                continue
            
            # Skip empty layers
            if layer.name == "base":
                continue  # Base layer is already rendered
            
            # Create transparent overlay for this layer
            overlay = np.zeros((self.height, self.width, 4), dtype=np.uint8)
            
            # Render layer content
            if layer.name == "data" and layer.metric_id and layer.metric_id in metrics:
                self._render_data_layer(overlay, entities, metrics[layer.metric_id], layer)
            elif layer.name == "outlines":
                self._render_outlines_layer(overlay, entities, layer)
            elif layer.name == "highlights":
                self._render_highlights_layer(overlay, entities, layer)
            elif layer.name == "labels":
                self._render_labels_layer(overlay, entities, layer)
            else:
                # Custom layer rendering can be added here
                pass
            
            # Apply rotation to the overlay
            rotated_overlay = self._apply_rotation(overlay)
            
            # Blend the rotated overlay with the globe
            self._blend_overlay(rotated_globe, rotated_overlay)
        
        return rotated_globe
    
    def _apply_rotation(self, image: np.ndarray) -> np.ndarray:
        """
        Apply 3D rotation to an image.
        
        Parameters
        ----------
        image : np.ndarray
            Image to rotate
            
        Returns
        -------
        np.ndarray
            Rotated image
        """
        # Make a temporary copy to store the image
        temp_path = self.output_dir / "temp_rotation_input.png"
        cv2.imwrite(str(temp_path), image)
        
        # Apply y-axis rotation first (side rotation)
        if self.rotation_y != 0:
            rotated = create_side_rotation(
                str(temp_path),
                self.rotation_y,
                perspective=self.perspective
            )
            # Save the intermediate result
            cv2.imwrite(str(temp_path), rotated)
        
        # Apply x-axis rotation (vertical tilt)
        if self.rotation_x != 0:
            rotated = create_3d_rotation(
                str(temp_path),
                self.rotation_x
            )
        else:
            # If no x rotation, use the image as is
            rotated = cv2.imread(str(temp_path))
        
        # Clean up temporary file
        if temp_path.exists():
            os.remove(temp_path)
        
        return rotated
    
    def _blend_overlay(self, base_img: np.ndarray, overlay: np.ndarray) -> None:
        """
        Blend an overlay image with alpha channel onto the base image.
        
        Parameters
        ----------
        base_img : np.ndarray
            Base image (modified in place)
        overlay : np.ndarray
            Overlay image with alpha channel
        """
        # Extract alpha channel
        if overlay.shape[2] == 4:
            alpha = overlay[:, :, 3] / 255.0
            
            # Create a color array without alpha
            color = overlay[:, :, :3]
            
            # Reshape alpha for broadcasting
            alpha = np.dstack([alpha, alpha, alpha])
            
            # Blend images
            base_img[:] = (base_img * (1 - alpha) + color * alpha).astype(np.uint8)
    
    def _render_data_layer(self, overlay: np.ndarray, entities: Dict[str, Entity], 
                           metric: Metric, layer: RenderLayer) -> None:
        """
        Render the data visualization layer.
        
        Parameters
        ----------
        overlay : np.ndarray
            Image overlay to draw on
        entities : Dict[str, Entity]
            Dictionary of entities
        metric : Metric
            Metric to visualize
        layer : RenderLayer
            Layer configuration
        """
        # Get layer style properties
        marker_style = layer.style.get("marker_style", MarkerStyle.CIRCLE.value)
        marker_size = layer.style.get("marker_size", 8)
        color_map_type = layer.style.get("color_map_type", ColorMapType.SEQUENTIAL.value)
        
        # Extract color scale from metric
        colors = []
        for color_hex in metric.color_scale:
            # Convert hex color to RGB
            r = int(color_hex[1:3], 16)
            g = int(color_hex[3:5], 16)
            b = int(color_hex[5:7], 16)
            colors.append((r, g, b))
        
        # If no colors defined, use default blue gradient
        if not colors:
            colors = [(0, 0, 255), (0, 128, 255), (0, 255, 255)]
        
        # Get metric range
        min_val, max_val = metric.range
        if min_val is None or max_val is None:
            # Calculate from data if not specified
            values = []
            for entity in entities.values():
                if entity.has_metric(metric.id):
                    value = entity.get_metric(metric.id).value
                    if isinstance(value, (int, float)):
                        values.append(value)
            
            if values:
                min_val = min(values) if min_val is None else min_val
                max_val = max(values) if max_val is None else max_val
            else:
                min_val = 0 if min_val is None else min_val
                max_val = 1 if max_val is None else max_val
        
        # Get color mapping function
        if color_map_type == ColorMapType.DIVERGING.value:
            mid_val = layer.style.get("mid_value", (min_val + max_val) / 2)
            color_mapper = lambda v: self._diverging_color_map(v, min_val, max_val, colors, mid_val)
        elif color_map_type == ColorMapType.CATEGORICAL.value:
            # For categorical data, collect all unique categories
            categories = list(set(
                entity.get_metric(metric.id).value
                for entity in entities.values()
                if entity.has_metric(metric.id) and entity.get_metric(metric.id).value is not None
            ))
            color_mapper = lambda v: self._categorical_color_map(v, categories, colors)
        else:  # Default to sequential
            color_mapper = lambda v: self._sequential_color_map(v, min_val, max_val, colors)
        
        # Render each entity
        for entity_id, entity in entities.items():
            if not entity.has_metric(metric.id) or not entity.visible:
                continue
            
            # Get metric value
            metric_data = entity.get_metric(metric.id)
            if metric_data.value is None:
                continue
            
            # Get entity position (lat, lon)
            lat, lon = entity.location
            
            # Convert to x, y coordinates on the globe
            x, y = self._geo_to_xy(lat, lon)
            
            # Skip if outside the image
            if x < 0 or x >= self.width or y < 0 or y >= self.height:
                continue
            
            # Map value to color
            value = metric_data.value
            if isinstance(value, (int, float)):
                color = color_mapper(value)
            elif isinstance(value, str) and metric.metric_type == MetricType.CATEGORICAL:
                color = color_mapper(value)
            else:
                # Default color for non-numeric, non-categorical
                color = (128, 128, 128)
            
            # Draw marker
            self._draw_marker(overlay, (x, y), marker_style, marker_size, color, alpha=200)
    
    def _render_outlines_layer(self, overlay: np.ndarray, entities: Dict[str, Entity], 
                               layer: RenderLayer) -> None:
        """
        Render country outlines.
        
        Parameters
        ----------
        overlay : np.ndarray
            Image overlay to draw on
        entities : Dict[str, Entity]
            Dictionary of entities
        layer : RenderLayer
            Layer configuration
        """
        # Get layer style properties
        line_color = layer.style.get("line_color", (255, 255, 255))
        line_thickness = layer.style.get("line_thickness", 1)
        alpha = layer.style.get("alpha", 150)
        
        # Draw outlines for entities with bounding boxes
        for entity_id, entity in entities.items():
            if not entity.visible or not entity.bounding_box:
                continue
            
            # Convert bounding box points to screen coordinates
            points = []
            for lat, lon in entity.bounding_box:
                x, y = self._geo_to_xy(lat, lon)
                points.append((x, y))
            
            # Draw polygon
            if len(points) >= 3:
                points_array = np.array(points, dtype=np.int32)
                cv2.polylines(
                    overlay, 
                    [points_array], 
                    True, 
                    (*line_color, alpha), 
                    line_thickness
                )
    
    def _render_highlights_layer(self, overlay: np.ndarray, entities: Dict[str, Entity], 
                                 layer: RenderLayer) -> None:
        """
        Render highlighted entities.
        
        Parameters
        ----------
        overlay : np.ndarray
            Image overlay to draw on
        entities : Dict[str, Entity]
            Dictionary of entities
        layer : RenderLayer
            Layer configuration
        """
        # Get layer style properties
        marker_style = layer.style.get("marker_style", MarkerStyle.CIRCLE.value)
        marker_size = layer.style.get("marker_size", 12)
        marker_color = layer.style.get("marker_color", (255, 255, 0))  # Yellow highlight
        line_thickness = layer.style.get("line_thickness", 2)
        alpha = layer.style.get("alpha", 200)
        
        # Draw highlights for selected entities
        for entity_id in layer.entities:
            if entity_id not in entities or not entities[entity_id].visible:
                continue
            
            entity = entities[entity_id]
            lat, lon = entity.location
            
            # Convert to x, y coordinates on the globe
            x, y = self._geo_to_xy(lat, lon)
            
            # Skip if outside the image
            if x < 0 or x >= self.width or y < 0 or y >= self.height:
                continue
            
            # Draw marker
            self._draw_marker(overlay, (x, y), marker_style, marker_size, marker_color, alpha=alpha)
            
            # Draw outline if bounding box exists
            if entity.bounding_box:
                points = []
                for lat, lon in entity.bounding_box:
                    x, y = self._geo_to_xy(lat, lon)
                    points.append((x, y))
                
                if len(points) >= 3:
                    points_array = np.array(points, dtype=np.int32)
                    cv2.polylines(
                        overlay, 
                        [points_array], 
                        True, 
                        (*marker_color, alpha), 
                        line_thickness
                    )
    
    def _render_labels_layer(self, overlay: np.ndarray, entities: Dict[str, Entity], 
                             layer: RenderLayer) -> None:
        """
        Render entity labels.
        
        Parameters
        ----------
        overlay : np.ndarray
            Image overlay to draw on
        entities : Dict[str, Entity]
            Dictionary of entities
        layer : RenderLayer
            Layer configuration
        """
        # Get layer style properties
        font_scale = layer.style.get("font_scale", 0.5)
        font_color = layer.style.get("font_color", (255, 255, 255))
        font_thickness = layer.style.get("font_thickness", 1)
        bg_color = layer.style.get("bg_color", (0, 0, 0, 128))
        padding = layer.style.get("padding", 2)
        
        # Draw labels for selected entities
        for entity_id in self.selected_entities:
            if entity_id not in entities or not entities[entity_id].visible:
                continue
            
            entity = entities[entity_id]
            lat, lon = entity.location
            
            # Convert to x, y coordinates on the globe
            x, y = self._geo_to_xy(lat, lon)
            
            # Skip if outside the image
            if x < 0 or x >= self.width or y < 0 or y >= self.height:
                continue
            
            # Draw label
            text = entity.name
            
            # Add metric value if available
            if self.current_metric_id and entity.has_metric(self.current_metric_id):
                metric_data = entity.get_metric(self.current_metric_id)
                if metric_data.value is not None:
                    text += f": {metric_data.value}"
            
            # Get text size
            font = cv2.FONT_HERSHEY_SIMPLEX
            (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, font_thickness)
            
            # Calculate label position (above the marker)
            label_x = x - text_width // 2
            label_y = y - 15  # Offset above marker
            
            # Ensure label is within image bounds
            label_x = max(padding, min(label_x, self.width - text_width - padding))
            label_y = max(text_height + padding, min(label_y, self.height - padding))
            
            # Draw label background
            cv2.rectangle(
                overlay,
                (label_x - padding, label_y - text_height - padding),
                (label_x + text_width + padding, label_y + padding),
                bg_color,
                -1  # Filled rectangle
            )
            
            # Draw text
            cv2.putText(
                overlay,
                text,
                (label_x, label_y),
                font,
                font_scale,
                font_color,
                font_thickness,
                cv2.LINE_AA
            )
    
    def _geo_to_xy(self, lat: float, lon: float) -> Tuple[int, int]:
        """
        Convert geographical coordinates to screen coordinates.
        
        Parameters
        ----------
        lat : float
            Latitude in degrees
        lon : float
            Longitude in degrees
            
        Returns
        -------
        Tuple[int, int]
            (x, y) screen coordinates
        """
        # Convert to radians
        lat_rad = np.deg2rad(lat)
        lon_rad = np.deg2rad(lon)
        
        # Apply rotation
        # Note: This is a simplified projection that doesn't account for full 3D rotation
        # For a more accurate projection, a full 3D transformation matrix would be needed
        
        # Basic equirectangular projection
        r = min(self.width, self.height) / 2 * 0.8  # Radius of globe
        
        # Center of globe
        cx = self.width / 2
        cy = self.height / 2
        
        # Calculate x, y position
        x = cx + r * np.cos(lat_rad) * np.sin(lon_rad)
        y = cy - r * np.sin(lat_rad)
        
        return int(x), int(y)
    
    def _draw_marker(self, img: np.ndarray, position: Tuple[int, int], 
                     style: str, size: int, color: Tuple[int, int, int], 
                     alpha: int = 255) -> None:
        """
        Draw a marker on the image.
        
        Parameters
        ----------
        img : np.ndarray
            Image to draw on
        position : Tuple[int, int]
            (x, y) position
        style : str
            Marker style
        size : int
            Marker size
        color : Tuple[int, int, int]
            RGB color
        alpha : int
            Alpha transparency (0-255)
        """
        x, y = position
        
        if style == MarkerStyle.CIRCLE.value:
            cv2.circle(img, (x, y), size, (*color, alpha), -1)
            # Add a white outline
            cv2.circle(img, (x, y), size, (255, 255, 255, alpha), 1)
        
        elif style == MarkerStyle.SQUARE.value:
            half_size = size // 2
            cv2.rectangle(
                img,
                (x - half_size, y - half_size),
                (x + half_size, y + half_size),
                (*color, alpha),
                -1
            )
            # Add a white outline
            cv2.rectangle(
                img,
                (x - half_size, y - half_size),
                (x + half_size, y + half_size),
                (255, 255, 255, alpha),
                1
            )
        
        elif style == MarkerStyle.DIAMOND.value:
            points = np.array([
                [x, y - size],
                [x + size, y],
                [x, y + size],
                [x - size, y]
            ])
            cv2.fillPoly(img, [points], (*color, alpha))
            # Add a white outline
            cv2.polylines(img, [points], True, (255, 255, 255, alpha), 1)
        
        elif style == MarkerStyle.TRIANGLE.value:
            points = np.array([
                [x, y - size],
                [x + size, y + size],
                [x - size, y + size]
            ])
            cv2.fillPoly(img, [points], (*color, alpha))
            # Add a white outline
            cv2.polylines(img, [points], True, (255, 255, 255, alpha), 1)
        
        elif style == MarkerStyle.STAR.value:
            # Draw a five-pointed star
            outer_points = []
            inner_points = []
            for i in range(5):
                # Outer points (vertices)
                angle_outer = np.deg2rad(i * 72 - 90)
                outer_x = x + int(size * np.cos(angle_outer))
                outer_y = y + int(size * np.sin(angle_outer))
                outer_points.append((outer_x, outer_y))
                
                # Inner points (between vertices)
                angle_inner = np.deg2rad(i * 72 + 36 - 90)
                inner_x = x + int(size * 0.4 * np.cos(angle_inner))
                inner_y = y + int(size * 0.4 * np.sin(angle_inner))
                inner_points.append((inner_x, inner_y))
            
            # Interleave outer and inner points to create star shape
            star_points = []
            for i in range(5):
                star_points.append(outer_points[i])
                star_points.append(inner_points[i])
            
            # Convert to numpy array
            star_array = np.array(star_points, dtype=np.int32)
            
            # Draw filled star
            cv2.fillPoly(img, [star_array], (*color, alpha))
            
            # Add white outline
            cv2.polylines(img, [star_array], True, (255, 255, 255, alpha), 1)
    
    def save_render(self, image: np.ndarray, filename: str) -> str:
        """
        Save the rendered image to a file.
        
        Parameters
        ----------
        image : np.ndarray
            Image to save
        filename : str
            Base filename (without extension)
            
        Returns
        -------
        str
            Path to the saved file
        """
        output_path = self.output_dir / f"{filename}.png"
        cv2.imwrite(str(output_path), image)
        return str(output_path)
    
    def capture_viewport(self) -> Dict[str, float]:
        """
        Capture the current viewport settings.
        
        Returns
        -------
        Dict[str, float]
            Dictionary of viewport settings
        """
        return {
            "rotation_x": self.rotation_x,
            "rotation_y": self.rotation_y,
            "zoom": self.zoom,
            "perspective": self.perspective
        }
    
    def restore_viewport(self, viewport: Dict[str, float]) -> None:
        """
        Restore viewport settings.
        
        Parameters
        ----------
        viewport : Dict[str, float]
            Dictionary of viewport settings
        """
        self.rotation_x = viewport.get("rotation_x", self.rotation_x)
        self.rotation_y = viewport.get("rotation_y", self.rotation_y)
        self.zoom = viewport.get("zoom", self.zoom)
        self.perspective = viewport.get("perspective", self.perspective)