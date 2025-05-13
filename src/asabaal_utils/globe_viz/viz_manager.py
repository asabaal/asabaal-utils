"""
Globe Visualization Manager.

This module provides the main visualization manager class that coordinates
the globe renderer, data management, and UI controls for the 3D globe
visualization system.
"""

import os
import cv2
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable, Union

import numpy as np

from .models import Entity, Metric, MetricData, MetricType
from .renderers import GlobeRenderer, ColorMapType, MarkerStyle
from .data_manager import DataManager
from .ui_controls import (
    UIController, Panel, Button, Dropdown, Slider, Toggle, 
    ControlEvent, ControlType
)


class GlobeVisualizationManager:
    """
    Main manager for the 3D globe visualization system.
    
    This class coordinates the globe renderer, data management, and UI controls
    to provide a complete visualization system.
    """
    
    def __init__(self, 
                 width: int = 1200, 
                 height: int = 800,
                 globe_image_path: Optional[Union[str, Path]] = None,
                 data_dir: Optional[Union[str, Path]] = None,
                 output_dir: Optional[Union[str, Path]] = None):
        """
        Initialize the globe visualization manager.
        
        Parameters
        ----------
        width : int
            Width of the visualization window
        height : int
            Height of the visualization window
        globe_image_path : Optional[Union[str, Path]]
            Path to the base globe image (if None, a default is used)
        data_dir : Optional[Union[str, Path]]
            Directory for data files
        output_dir : Optional[Union[str, Path]]
            Directory for output files
        """
        self.width = width
        self.height = height
        
        # Set up output directory
        self.output_dir = Path(output_dir) if output_dir else Path.cwd() / "globe_viz_output"
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Set up data directory
        data_dir = Path(data_dir) if data_dir else Path.cwd() / "globe_viz_data"
        
        # Initialize components
        self.data_manager = DataManager(data_dir)
        self.renderer = GlobeRenderer(
            globe_image_path=globe_image_path,
            output_dir=self.output_dir,
            width=width,
            height=height
        )
        self.ui_controller = UIController(width, height)
        
        # Current state
        self.current_metric_id: Optional[str] = None
        self.show_ui = True
        self.running = False
        self.paused = False
        self.frame_count = 0
        
        # Viewport history
        self.viewport_history: Dict[str, Dict[str, float]] = {}
        
        # Set up UI event handlers
        self.ui_controller.set_on_globe_rotate(self._handle_globe_rotate)
        self.ui_controller.set_on_globe_zoom(self._handle_globe_zoom)
        self.ui_controller.set_on_metric_change(self._handle_metric_change)
        self.ui_controller.set_on_entity_select(self._handle_entity_select)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
    
    def load_data(self, entities_file: Union[str, Path], metrics_file: Union[str, Path]) -> None:
        """
        Load entity and metric data.
        
        Parameters
        ----------
        entities_file : Union[str, Path]
            Path to the entities JSON file
        metrics_file : Union[str, Path]
            Path to the metrics JSON file
        """
        self.data_manager.load_metrics_from_json(metrics_file)
        self.data_manager.load_entities_from_json(entities_file)
        
        self.logger.info(f"Loaded {len(self.data_manager.metrics)} metrics and {len(self.data_manager.entities)} entities")
        
        # Set up UI with loaded data
        self._setup_ui()
    
    def load_metric_data(self, data_file: Union[str, Path], metric_id: str, 
                        entity_col: str = 'entity_id', value_col: str = 'value') -> None:
        """
        Load data for a specific metric.
        
        Parameters
        ----------
        data_file : Union[str, Path]
            Path to the data file (CSV)
        metric_id : str
            ID of the metric to associate with this data
        entity_col : str
            Name of the column containing entity IDs
        value_col : str
            Name of the column containing values
        """
        self.data_manager.load_data_from_csv(
            data_file, metric_id, entity_col, value_col
        )
        
        # Normalize the data
        self.data_manager.normalize_metric(metric_id)
        
        # Compute rankings
        self.data_manager.compute_rankings(metric_id)
        
        # If this is the first metric, set it as current
        if self.current_metric_id is None:
            self.set_current_metric(metric_id)
    
    def derive_metric(self, derived_metric_id: str, source_metrics: List[str], 
                     transform_func: str) -> None:
        """
        Create a derived metric from other metrics.
        
        Parameters
        ----------
        derived_metric_id : str
            ID of the derived metric to create
        source_metrics : List[str]
            List of source metric IDs
        transform_func : str
            Name of the transformation function to apply
        """
        self.data_manager.compute_derived_metric(
            derived_metric_id, source_metrics, transform_func
        )
        
        # Normalize the data
        self.data_manager.normalize_metric(derived_metric_id)
        
        # Compute rankings
        self.data_manager.compute_rankings(derived_metric_id)
    
    def set_current_metric(self, metric_id: Optional[str]) -> None:
        """
        Set the current metric for visualization.
        
        Parameters
        ----------
        metric_id : Optional[str]
            ID of the metric to visualize (None to clear)
        """
        if metric_id is not None and metric_id not in self.data_manager.metrics:
            self.logger.error(f"Metric {metric_id} not found")
            return
        
        self.current_metric_id = metric_id
        
        # Update renderer
        self.renderer.set_current_metric(metric_id)
        
        # Update UI
        metric_dropdown = self.ui_controller.get_control("metric_dropdown")
        if metric_dropdown and isinstance(metric_dropdown, Dropdown):
            metric_dropdown.set_selected_value(metric_id, False)
        
        # Update legend
        legend = self.ui_controller.get_control("metric_legend")
        if legend:
            if metric_id:
                legend.set_metric(self.data_manager.metrics.get(metric_id))
            else:
                legend.set_metric(None)
        
        # Restore viewport if we've seen this metric before
        if metric_id in self.viewport_history:
            self.renderer.restore_viewport(self.viewport_history[metric_id])
        
        self.logger.info(f"Set current metric to {metric_id}")
    
    def select_entity(self, entity_id: str) -> None:
        """
        Select an entity on the globe.
        
        Parameters
        ----------
        entity_id : str
            ID of the entity to select
        """
        if entity_id not in self.data_manager.entities:
            self.logger.error(f"Entity {entity_id} not found")
            return
        
        self.renderer.select_entity(entity_id)
        self.renderer.highlight_entity(entity_id)
        
        self.logger.info(f"Selected entity {entity_id}")
    
    def deselect_entity(self, entity_id: str) -> None:
        """
        Deselect an entity on the globe.
        
        Parameters
        ----------
        entity_id : str
            ID of the entity to deselect
        """
        self.renderer.deselect_entity(entity_id)
        
        # Remove from highlights
        if entity_id in self.renderer.highlighted_entities:
            self.renderer.highlighted_entities.remove(entity_id)
            self.renderer.layers["highlights"].remove_entity(entity_id)
        
        self.logger.info(f"Deselected entity {entity_id}")
    
    def clear_selections(self) -> None:
        """Clear all entity selections."""
        self.renderer.clear_selections()
        self.renderer.clear_highlights()
        
        self.logger.info("Cleared all entity selections")
    
    def set_rotation(self, x: float = None, y: float = None) -> None:
        """
        Set the globe rotation.
        
        Parameters
        ----------
        x : float
            Rotation around x-axis (vertical tilt)
        y : float
            Rotation around y-axis (horizontal rotation)
        """
        self.renderer.set_rotation(x, y)
    
    def rotate(self, delta_x: float = 0.0, delta_y: float = 0.0) -> None:
        """
        Rotate the globe by specified deltas.
        
        Parameters
        ----------
        delta_x : float
            Change in x-axis rotation
        delta_y : float
            Change in y-axis rotation
        """
        self.renderer.rotate(delta_x, delta_y)
    
    def set_zoom(self, zoom: float) -> None:
        """
        Set the zoom level.
        
        Parameters
        ----------
        zoom : float
            Zoom level (1.0 is default)
        """
        self.renderer.set_zoom(zoom)
    
    def zoom_by(self, delta: float) -> None:
        """
        Change the zoom level by a delta.
        
        Parameters
        ----------
        delta : float
            Change in zoom level
        """
        self.renderer.zoom_by(delta)
    
    def take_snapshot(self) -> str:
        """
        Save a snapshot of the current view.
        
        Returns
        -------
        str
            Path to the saved snapshot
        """
        # Render the globe with entities and metrics
        globe_img = self.render_frame(show_ui=False)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metric_suffix = f"_{self.current_metric_id}" if self.current_metric_id else ""
        filename = f"globe_snapshot{metric_suffix}_{timestamp}"
        
        # Save image
        output_path = self.renderer.save_render(globe_img, filename)
        
        self.logger.info(f"Saved snapshot to {output_path}")
        
        return output_path
    
    def reset_view(self) -> None:
        """Reset the globe view to default settings."""
        self.renderer.set_rotation(0.0, 0.0)
        self.renderer.set_zoom(1.0)
        
        self.logger.info("Reset view to default")
    
    def save_viewport(self) -> None:
        """Save the current viewport for the current metric."""
        if self.current_metric_id:
            self.viewport_history[self.current_metric_id] = self.renderer.capture_viewport()
            
            self.logger.info(f"Saved viewport for metric {self.current_metric_id}")
    
    def render_frame(self, show_ui: bool = True) -> np.ndarray:
        """
        Render a single frame of the visualization.
        
        Parameters
        ----------
        show_ui : bool
            Whether to show the UI controls
            
        Returns
        -------
        np.ndarray
            Rendered frame
        """
        # Render the globe with entities and metrics
        globe_img = self.renderer.render_globe(
            self.data_manager.entities,
            self.data_manager.metrics
        )
        
        # If UI is hidden, return just the globe
        if not show_ui:
            return globe_img
        
        # Render UI
        ui_img = self.ui_controller.render()
        
        # Combine globe and UI
        # UI overlay has an alpha channel, so we need to blend it
        alpha = ui_img[:, :, 3:4] / 255.0
        rgb = ui_img[:, :, :3]
        
        # Blend the UI onto the globe image
        blended = (globe_img * (1 - alpha) + rgb * alpha).astype(np.uint8)
        
        return blended
    
    def run(self, interactive: bool = True, framerate: int = 30, 
           duration: Optional[float] = None) -> None:
        """
        Run the visualization.
        
        Parameters
        ----------
        interactive : bool
            Whether to run in interactive mode (with UI)
        framerate : int
            Target framerate for the visualization
        duration : Optional[float]
            Duration to run in seconds (None for indefinite)
        """
        try:
            # Set up window
            window_name = "3D Globe Visualization"
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(window_name, self.width, self.height)
            
            # Start running
            self.running = True
            self.paused = False
            self.frame_count = 0
            start_time = datetime.now()
            
            # Set up interactive controls if needed
            if interactive:
                cv2.setMouseCallback(window_name, self._handle_mouse_event)
            
            while self.running:
                if not self.paused:
                    # Render frame
                    frame = self.render_frame(show_ui=self.show_ui)
                    
                    # Display frame
                    cv2.imshow(window_name, frame)
                    
                    # Increment frame count
                    self.frame_count += 1
                
                # Check for key presses
                key = cv2.waitKey(int(1000 / framerate))
                if key != -1:
                    self._handle_key_event(key)
                
                # Check if duration expired
                if duration is not None:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if elapsed >= duration:
                        self.running = False
            
            # Clean up
            cv2.destroyAllWindows()
            
        except Exception as e:
            self.logger.error(f"Error in visualization: {e}")
            raise
    
    def save_video(self, filename: str, rotation_speed: float = 1.0, 
                  duration: float = 10.0, framerate: int = 30, 
                  resolution: Tuple[int, int] = None) -> str:
        """
        Save a video of the globe rotating.
        
        Parameters
        ----------
        filename : str
            Output filename (without extension)
        rotation_speed : float
            Speed of rotation in degrees per frame
        duration : float
            Duration of the video in seconds
        framerate : int
            Video framerate
        resolution : Tuple[int, int]
            Video resolution (width, height)
            
        Returns
        -------
        str
            Path to the saved video
        """
        try:
            # Set resolution
            if resolution is None:
                resolution = (self.width, self.height)
            
            # Calculate total frames
            total_frames = int(duration * framerate)
            
            # Set up video writer
            output_path = self.output_dir / f"{filename}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(
                str(output_path), 
                fourcc, 
                framerate, 
                resolution
            )
            
            # Hide UI for video
            old_show_ui = self.show_ui
            self.show_ui = False
            
            # Save and reset initial rotation
            initial_rotation_y = self.renderer.rotation_y
            
            # Record frames
            for i in range(total_frames):
                # Update rotation for smooth animation
                angle = (i * rotation_speed) % 360
                self.renderer.set_rotation(y=angle)
                
                # Render frame
                frame = self.render_frame(show_ui=False)
                
                # Resize if needed
                if frame.shape[1] != resolution[0] or frame.shape[0] != resolution[1]:
                    frame = cv2.resize(frame, resolution)
                
                # Write frame
                writer.write(frame)
            
            # Restore UI and rotation
            self.show_ui = old_show_ui
            self.renderer.set_rotation(y=initial_rotation_y)
            
            # Release writer
            writer.release()
            
            self.logger.info(f"Saved video to {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Error saving video: {e}")
            raise
    
    def export_data(self, filename: str) -> str:
        """
        Export all data to a JSON file.
        
        Parameters
        ----------
        filename : str
            Output filename (without extension)
            
        Returns
        -------
        str
            Path to the exported file
        """
        output_path = self.output_dir / f"{filename}.json"
        self.data_manager.export_to_json(output_path)
        
        self.logger.info(f"Exported data to {output_path}")
        
        return str(output_path)
    
    def _setup_ui(self) -> None:
        """Set up the UI controls."""
        # Create control panel
        self.ui_controller.create_control_panel(
            self.data_manager.metrics,
            self.current_metric_id
        )
        
        # Create legend
        current_metric = None
        if self.current_metric_id:
            current_metric = self.data_manager.metrics.get(self.current_metric_id)
        
        self.ui_controller.create_legend(current_metric)
        
        # Set up callbacks
        control_panel = self.ui_controller.get_control("control_panel")
        if control_panel:
            # Get reset view button
            reset_btn = control_panel.children[3]  # reset_view_btn
            if reset_btn and isinstance(reset_btn, Button):
                reset_btn.on(ControlEvent.CLICK, lambda e: self.reset_view())
            
            # Get snapshot button
            snapshot_btn = control_panel.children[4]  # snapshot_btn
            if snapshot_btn and isinstance(snapshot_btn, Button):
                snapshot_btn.on(ControlEvent.CLICK, lambda e: self.take_snapshot())
            
            # Get show labels toggle
            labels_toggle = control_panel.children[6]  # show_labels_toggle
            if labels_toggle and isinstance(labels_toggle, Toggle):
                labels_toggle.on(ControlEvent.CHANGE, lambda e: self._toggle_labels(e["value"]))
            
            # Get show outlines toggle
            outlines_toggle = control_panel.children[7]  # show_outlines_toggle
            if outlines_toggle and isinstance(outlines_toggle, Toggle):
                outlines_toggle.on(ControlEvent.CHANGE, lambda e: self._toggle_outlines(e["value"]))
    
    def _handle_globe_rotate(self, delta_x: float, delta_y: float) -> None:
        """
        Handle globe rotation event.
        
        Parameters
        ----------
        delta_x : float
            Change in x-axis rotation
        delta_y : float
            Change in y-axis rotation
        """
        self.rotate(delta_x, delta_y)
        
        # Save viewport if we have a current metric
        if self.current_metric_id:
            self.save_viewport()
    
    def _handle_globe_zoom(self, delta: float) -> None:
        """
        Handle globe zoom event.
        
        Parameters
        ----------
        delta : float
            Change in zoom level
        """
        self.zoom_by(delta)
        
        # Save viewport if we have a current metric
        if self.current_metric_id:
            self.save_viewport()
    
    def _handle_metric_change(self, metric_id: str) -> None:
        """
        Handle metric change event.
        
        Parameters
        ----------
        metric_id : str
            ID of the new metric
        """
        self.set_current_metric(metric_id)
    
    def _handle_entity_select(self, entity_id: str) -> None:
        """
        Handle entity selection event.
        
        Parameters
        ----------
        entity_id : str
            ID of the selected entity
        """
        self.select_entity(entity_id)
    
    def _toggle_labels(self, show: bool) -> None:
        """
        Toggle visibility of labels.
        
        Parameters
        ----------
        show : bool
            Whether to show labels
        """
        if "labels" in self.renderer.layers:
            self.renderer.layers["labels"].visible = show
    
    def _toggle_outlines(self, show: bool) -> None:
        """
        Toggle visibility of country outlines.
        
        Parameters
        ----------
        show : bool
            Whether to show outlines
        """
        if "outlines" in self.renderer.layers:
            self.renderer.layers["outlines"].visible = show
    
    def _handle_mouse_event(self, event: int, x: int, y: int, flags: int, param: Any) -> None:
        """
        Handle OpenCV mouse events.
        
        Parameters
        ----------
        event : int
            OpenCV event type
        x : int
            X-coordinate
        y : int
            Y-coordinate
        flags : int
            Event flags
        param : Any
            Additional parameters
        """
        # Convert OpenCV event types to our event types
        if event == cv2.EVENT_LBUTTONDOWN:
            event_type = "press"
            buttons = 1
        elif event == cv2.EVENT_LBUTTONUP:
            event_type = "release"
            buttons = 1
        elif event == cv2.EVENT_MOUSEMOVE:
            event_type = "move"
            buttons = 0
            if flags & cv2.EVENT_FLAG_LBUTTON:
                buttons = 1
        else:
            return
        
        # Set up modifiers
        modifiers = {
            "shift": bool(flags & cv2.EVENT_FLAG_SHIFTKEY),
            "ctrl": bool(flags & cv2.EVENT_FLAG_CTRLKEY),
            "alt": bool(flags & cv2.EVENT_FLAG_ALTKEY)
        }
        
        # Pass to UI controller
        self.ui_controller.handle_mouse_event(event_type, x, y, buttons, modifiers)
    
    def _handle_key_event(self, key: int) -> None:
        """
        Handle keyboard events.
        
        Parameters
        ----------
        key : int
            OpenCV key code
        """
        # Handle global keys first
        if key == 27:  # ESC
            self.running = False
        elif key == ord(' '):
            self.paused = not self.paused
        elif key == ord('h'):
            self.show_ui = not self.show_ui
        elif key == ord('s'):
            self.take_snapshot()
        elif key == ord('r'):
            self.reset_view()
        elif key == ord('v'):
            self.save_video("globe_rotation", rotation_speed=1.0)
        
        # Pass other keys to UI controller
        else:
            # Set up modifiers (we don't have access to modifier keys here)
            modifiers = {"shift": False, "ctrl": False, "alt": False}
            
            self.ui_controller.handle_key_event(key, modifiers)