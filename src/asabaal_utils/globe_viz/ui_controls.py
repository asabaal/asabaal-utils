"""
UI Controls for Globe Visualization.

This module provides user interface components for controlling and interacting
with the 3D globe visualization.
"""

import cv2
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from enum import Enum
from pathlib import Path

from .models import Entity, Metric, MetricData, MetricType


class ControlType(Enum):
    """Types of UI controls."""
    
    BUTTON = "button"
    SLIDER = "slider"
    DROPDOWN = "dropdown"
    TOGGLE = "toggle"
    TEXT = "text"
    PANEL = "panel"
    LEGEND = "legend"


class ControlEvent(Enum):
    """Types of control events."""
    
    CLICK = "click"
    CHANGE = "change"
    HOVER = "hover"
    DRAG_START = "drag_start"
    DRAG = "drag"
    DRAG_END = "drag_end"
    KEY = "key"


class UIControl:
    """Base class for UI controls."""
    
    def __init__(self, id: str, x: int, y: int, width: int, height: int, 
                 control_type: ControlType, visible: bool = True):
        """
        Initialize a UI control.
        
        Parameters
        ----------
        id : str
            Unique identifier for the control
        x : int
            X-coordinate of the top-left corner
        y : int
            Y-coordinate of the top-left corner
        width : int
            Width of the control
        height : int
            Height of the control
        control_type : ControlType
            Type of control
        visible : bool
            Whether the control is visible
        """
        self.id = id
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.control_type = control_type
        self.visible = visible
        self.enabled = True
        self.parent: Optional[UIControl] = None
        self.children: List[UIControl] = []
        
        # Event handlers
        self.event_handlers: Dict[ControlEvent, List[Callable]] = {
            event: [] for event in ControlEvent
        }
        
        # Style properties
        self.style: Dict[str, Any] = {
            "bg_color": (50, 50, 50),
            "fg_color": (255, 255, 255),
            "border_color": (100, 100, 100),
            "hover_color": (70, 70, 70),
            "active_color": (0, 120, 215),
            "disabled_color": (150, 150, 150),
            "font": cv2.FONT_HERSHEY_SIMPLEX,
            "font_scale": 0.5,
            "padding": 5,
            "border_width": 1,
            "corner_radius": 3,
            "alpha": 200  # Transparency (0-255)
        }
    
    def add_child(self, control: 'UIControl') -> None:
        """Add a child control."""
        control.parent = self
        self.children.append(control)
    
    def remove_child(self, control_id: str) -> None:
        """Remove a child control by ID."""
        self.children = [c for c in self.children if c.id != control_id]
    
    def get_absolute_position(self) -> Tuple[int, int]:
        """Get absolute position accounting for parent controls."""
        x, y = self.x, self.y
        
        # Add parent offsets
        parent = self.parent
        while parent:
            x += parent.x
            y += parent.y
            parent = parent.parent
        
        return x, y
    
    def contains_point(self, point: Tuple[int, int]) -> bool:
        """Check if point is within control bounds."""
        abs_x, abs_y = self.get_absolute_position()
        px, py = point
        
        return (
            abs_x <= px <= abs_x + self.width and
            abs_y <= py <= abs_y + self.height
        )
    
    def on(self, event_type: ControlEvent, handler: Callable) -> None:
        """Register an event handler."""
        self.event_handlers[event_type].append(handler)
    
    def off(self, event_type: ControlEvent, handler: Callable) -> None:
        """Remove an event handler."""
        if event_type in self.event_handlers:
            self.event_handlers[event_type] = [
                h for h in self.event_handlers[event_type] if h != handler
            ]
    
    def trigger(self, event_type: ControlEvent, event_data: Dict[str, Any] = None) -> None:
        """Trigger an event and call registered handlers."""
        if not self.enabled:
            return
            
        event_data = event_data or {}
        event_data["source"] = self
        
        for handler in self.event_handlers.get(event_type, []):
            try:
                handler(event_data)
            except Exception as e:
                logging.error(f"Error in event handler for {self.id}: {e}")
    
    def update_style(self, **kwargs) -> None:
        """Update style properties."""
        self.style.update(kwargs)
    
    def render(self, canvas: np.ndarray) -> None:
        """
        Render the control onto the canvas.
        
        Parameters
        ----------
        canvas : np.ndarray
            Canvas to render on
        """
        if not self.visible:
            return
        
        # Render this control
        self._render_self(canvas)
        
        # Render children
        for child in self.children:
            child.render(canvas)
    
    def _render_self(self, canvas: np.ndarray) -> None:
        """Render this control (to be implemented by subclasses)."""
        pass
    
    def handle_mouse_event(self, event_type: str, x: int, y: int, 
                           buttons: int, modifiers: Dict[str, bool]) -> bool:
        """
        Handle a mouse event.
        
        Parameters
        ----------
        event_type : str
            Type of mouse event
        x : int
            X-coordinate
        y : int
            Y-coordinate
        buttons : int
            Mouse buttons state
        modifiers : Dict[str, bool]
            Keyboard modifiers
            
        Returns
        -------
        bool
            True if event was handled, False otherwise
        """
        if not self.visible or not self.enabled:
            return False
        
        # Check if point is within bounds
        if not self.contains_point((x, y)):
            return False
        
        # Handle event in children first (in reverse order for proper layering)
        for child in reversed(self.children):
            if child.handle_mouse_event(event_type, x, y, buttons, modifiers):
                return True
        
        # Handle in this control
        if event_type == "press":
            self.trigger(ControlEvent.CLICK, {"x": x, "y": y, "buttons": buttons, "modifiers": modifiers})
            return True
        elif event_type == "move":
            self.trigger(ControlEvent.HOVER, {"x": x, "y": y})
            return True
        elif event_type == "drag_start":
            self.trigger(ControlEvent.DRAG_START, {"x": x, "y": y, "buttons": buttons})
            return True
        elif event_type == "drag":
            self.trigger(ControlEvent.DRAG, {"x": x, "y": y, "buttons": buttons})
            return True
        elif event_type == "drag_end":
            self.trigger(ControlEvent.DRAG_END, {"x": x, "y": y, "buttons": buttons})
            return True
        
        return False
    
    def handle_key_event(self, key: int, modifiers: Dict[str, bool]) -> bool:
        """
        Handle a key event.
        
        Parameters
        ----------
        key : int
            Key code
        modifiers : Dict[str, bool]
            Keyboard modifiers
            
        Returns
        -------
        bool
            True if event was handled, False otherwise
        """
        if not self.visible or not self.enabled:
            return False
        
        # Handle in children first
        for child in self.children:
            if child.handle_key_event(key, modifiers):
                return True
        
        # Handle in this control
        self.trigger(ControlEvent.KEY, {"key": key, "modifiers": modifiers})
        
        return False  # Default: not handled


class Button(UIControl):
    """Button control."""
    
    def __init__(self, id: str, x: int, y: int, width: int, height: int, 
                 text: str, callback: Callable = None):
        """
        Initialize a button.
        
        Parameters
        ----------
        id : str
            Unique identifier
        x : int
            X-coordinate
        y : int
            Y-coordinate
        width : int
            Width
        height : int
            Height
        text : str
            Button text
        callback : Callable, optional
            Click callback function
        """
        super().__init__(id, x, y, width, height, ControlType.BUTTON)
        self.text = text
        self.hovered = False
        self.pressed = False
        
        # Register callback if provided
        if callback:
            self.on(ControlEvent.CLICK, lambda e: callback())
    
    def _render_self(self, canvas: np.ndarray) -> None:
        """Render the button."""
        abs_x, abs_y = self.get_absolute_position()
        
        # Determine color based on state
        if not self.enabled:
            bg_color = self.style["disabled_color"]
        elif self.pressed:
            bg_color = self.style["active_color"]
        elif self.hovered:
            bg_color = self.style["hover_color"]
        else:
            bg_color = self.style["bg_color"]
        
        # Draw button background with rounded corners
        corner_radius = self.style["corner_radius"]
        if corner_radius > 0:
            # Draw rounded rectangle (using multiple rectangles and circles)
            # Top-left corner
            cv2.circle(
                canvas,
                (abs_x + corner_radius, abs_y + corner_radius),
                corner_radius,
                bg_color,
                -1
            )
            # Top-right corner
            cv2.circle(
                canvas,
                (abs_x + self.width - corner_radius, abs_y + corner_radius),
                corner_radius,
                bg_color,
                -1
            )
            # Bottom-left corner
            cv2.circle(
                canvas,
                (abs_x + corner_radius, abs_y + self.height - corner_radius),
                corner_radius,
                bg_color,
                -1
            )
            # Bottom-right corner
            cv2.circle(
                canvas,
                (abs_x + self.width - corner_radius, abs_y + self.height - corner_radius),
                corner_radius,
                bg_color,
                -1
            )
            
            # Fill in the rectangles between corners
            cv2.rectangle(
                canvas,
                (abs_x + corner_radius, abs_y),
                (abs_x + self.width - corner_radius, abs_y + self.height),
                bg_color,
                -1
            )
            cv2.rectangle(
                canvas,
                (abs_x, abs_y + corner_radius),
                (abs_x + self.width, abs_y + self.height - corner_radius),
                bg_color,
                -1
            )
        else:
            # Simple rectangle
            cv2.rectangle(
                canvas,
                (abs_x, abs_y),
                (abs_x + self.width, abs_y + self.height),
                bg_color,
                -1
            )
        
        # Draw border
        border_width = self.style["border_width"]
        if border_width > 0:
            cv2.rectangle(
                canvas,
                (abs_x, abs_y),
                (abs_x + self.width, abs_y + self.height),
                self.style["border_color"],
                border_width
            )
        
        # Draw text
        font = self.style["font"]
        font_scale = self.style["font_scale"]
        text_color = self.style["fg_color"] if self.enabled else (
            200, 200, 200
        )
        
        # Measure text size
        (text_width, text_height), _ = cv2.getTextSize(
            self.text, font, font_scale, 1
        )
        
        # Center text
        text_x = abs_x + (self.width - text_width) // 2
        text_y = abs_y + (self.height + text_height) // 2
        
        cv2.putText(
            canvas,
            self.text,
            (text_x, text_y),
            font,
            font_scale,
            text_color,
            1,
            cv2.LINE_AA
        )
    
    def handle_mouse_event(self, event_type: str, x: int, y: int, 
                          buttons: int, modifiers: Dict[str, bool]) -> bool:
        """Handle mouse events for the button."""
        if not self.visible or not self.enabled:
            return False
        
        contains = self.contains_point((x, y))
        
        if event_type == "move":
            self.hovered = contains
            if contains:
                self.trigger(ControlEvent.HOVER, {"x": x, "y": y})
                return True
        
        elif event_type == "press" and contains:
            self.pressed = True
            return True
        
        elif event_type == "release":
            was_pressed = self.pressed
            self.pressed = False
            
            if was_pressed and contains:
                self.trigger(ControlEvent.CLICK, {"x": x, "y": y, "buttons": buttons, "modifiers": modifiers})
                return True
        
        return False


class Slider(UIControl):
    """Slider control for numeric values."""
    
    def __init__(self, id: str, x: int, y: int, width: int, height: int, 
                 min_value: float, max_value: float, value: float = None, 
                 callback: Callable = None, step: float = None):
        """
        Initialize a slider.
        
        Parameters
        ----------
        id : str
            Unique identifier
        x : int
            X-coordinate
        y : int
            Y-coordinate
        width : int
            Width
        height : int
            Height
        min_value : float
            Minimum value
        max_value : float
            Maximum value
        value : float, optional
            Initial value
        callback : Callable, optional
            Value change callback function
        step : float, optional
            Step size for discrete values
        """
        super().__init__(id, x, y, width, height, ControlType.SLIDER)
        self.min_value = min_value
        self.max_value = max_value
        self.value = value if value is not None else min_value
        self.step = step
        self.dragging = False
        self.hover_position = None
        
        # Register callback if provided
        if callback:
            self.on(ControlEvent.CHANGE, lambda e: callback(e["value"]))
    
    def set_value(self, value: float, trigger_event: bool = True) -> None:
        """
        Set the slider value.
        
        Parameters
        ----------
        value : float
            New value
        trigger_event : bool
            Whether to trigger change event
        """
        # Clamp to min/max
        value = max(self.min_value, min(self.max_value, value))
        
        # Apply step if defined
        if self.step:
            steps = round((value - self.min_value) / self.step)
            value = self.min_value + steps * self.step
        
        if value != self.value:
            old_value = self.value
            self.value = value
            
            if trigger_event:
                self.trigger(ControlEvent.CHANGE, {"value": value, "old_value": old_value})
    
    def _value_to_position(self, value: float) -> int:
        """Convert value to slider position."""
        abs_x, _ = self.get_absolute_position()
        value_range = self.max_value - self.min_value
        if value_range == 0:
            return abs_x
        
        ratio = (value - self.min_value) / value_range
        slider_width = self.width - 20  # Accounting for thumb width
        return abs_x + 10 + int(ratio * slider_width)
    
    def _position_to_value(self, x: int) -> float:
        """Convert slider position to value."""
        abs_x, _ = self.get_absolute_position()
        slider_width = self.width - 20  # Accounting for thumb width
        
        # Calculate relative position
        rel_pos = max(0, min(x - (abs_x + 10), slider_width))
        
        # Convert to value
        ratio = rel_pos / slider_width
        return self.min_value + ratio * (self.max_value - self.min_value)
    
    def _render_self(self, canvas: np.ndarray) -> None:
        """Render the slider."""
        abs_x, abs_y = self.get_absolute_position()
        
        # Calculate slider track position
        track_y = abs_y + self.height // 2
        
        # Draw track background
        cv2.line(
            canvas,
            (abs_x + 10, track_y),
            (abs_x + self.width - 10, track_y),
            self.style["bg_color"],
            3,
            cv2.LINE_AA
        )
        
        # Draw filled portion
        thumb_x = self._value_to_position(self.value)
        cv2.line(
            canvas,
            (abs_x + 10, track_y),
            (thumb_x, track_y),
            self.style["active_color"],
            3,
            cv2.LINE_AA
        )
        
        # Draw thumb
        thumb_radius = 6
        thumb_color = self.style["active_color"] if self.enabled else self.style["disabled_color"]
        
        cv2.circle(
            canvas,
            (thumb_x, track_y),
            thumb_radius,
            thumb_color,
            -1,
            cv2.LINE_AA
        )
        
        # Draw value label
        value_text = f"{self.value:.1f}" if isinstance(self.value, float) else str(self.value)
        font = self.style["font"]
        font_scale = self.style["font_scale"]
        
        (text_width, text_height), _ = cv2.getTextSize(
            value_text, font, font_scale, 1
        )
        
        # Position text below the track
        text_x = thumb_x - text_width // 2
        text_y = abs_y + self.height - 5
        
        cv2.putText(
            canvas,
            value_text,
            (text_x, text_y),
            font,
            font_scale,
            self.style["fg_color"],
            1,
            cv2.LINE_AA
        )
        
        # Draw min/max labels
        min_text = str(self.min_value)
        max_text = str(self.max_value)
        
        cv2.putText(
            canvas,
            min_text,
            (abs_x + 5, abs_y + 12),
            font,
            font_scale * 0.8,
            self.style["fg_color"],
            1,
            cv2.LINE_AA
        )
        
        (max_width, _), _ = cv2.getTextSize(
            max_text, font, font_scale * 0.8, 1
        )
        
        cv2.putText(
            canvas,
            max_text,
            (abs_x + self.width - max_width - 5, abs_y + 12),
            font,
            font_scale * 0.8,
            self.style["fg_color"],
            1,
            cv2.LINE_AA
        )
    
    def handle_mouse_event(self, event_type: str, x: int, y: int, 
                          buttons: int, modifiers: Dict[str, bool]) -> bool:
        """Handle mouse events for the slider."""
        if not self.visible or not self.enabled:
            return False
        
        abs_x, abs_y = self.get_absolute_position()
        track_y = abs_y + self.height // 2
        thumb_x = self._value_to_position(self.value)
        
        # Check if mouse is over the thumb
        thumb_hit = (
            abs(x - thumb_x) <= 10 and
            abs(y - track_y) <= 10
        )
        
        # Check if mouse is over the track
        track_hit = (
            abs_x + 10 <= x <= abs_x + self.width - 10 and
            abs(y - track_y) <= 5
        )
        
        if event_type == "press" and (thumb_hit or track_hit):
            self.dragging = True
            self.set_value(self._position_to_value(x))
            return True
        
        elif event_type == "move":
            self.hover_position = (x, y) if thumb_hit or track_hit else None
            
            if self.dragging:
                self.set_value(self._position_to_value(x))
                return True
            
            if thumb_hit or track_hit:
                self.trigger(ControlEvent.HOVER, {"x": x, "y": y})
                return True
        
        elif event_type == "release":
            if self.dragging:
                self.dragging = False
                return True
        
        return False


class Dropdown(UIControl):
    """Dropdown control for selecting from a list of options."""
    
    def __init__(self, id: str, x: int, y: int, width: int, height: int, 
                 options: List[Tuple[str, str]], selected_index: int = 0, 
                 callback: Callable = None):
        """
        Initialize a dropdown.
        
        Parameters
        ----------
        id : str
            Unique identifier
        x : int
            X-coordinate
        y : int
            Y-coordinate
        width : int
            Width
        height : int
            Height
        options : List[Tuple[str, str]]
            List of (value, label) tuples
        selected_index : int
            Index of initially selected option
        callback : Callable, optional
            Selection change callback function
        """
        super().__init__(id, x, y, width, height, ControlType.DROPDOWN)
        self.options = options
        self.selected_index = min(selected_index, len(options) - 1) if options else -1
        self.open = False
        self.hovered = False
        self.hover_index = -1
        
        # Calculate dropdown height when open
        self.item_height = 25
        self.dropdown_height = len(options) * self.item_height
        
        # Register callback if provided
        if callback:
            self.on(ControlEvent.CHANGE, lambda e: callback(e["value"], e["index"]))
    
    def get_selected_option(self) -> Optional[Tuple[str, str]]:
        """Get the currently selected option."""
        if self.options and 0 <= self.selected_index < len(self.options):
            return self.options[self.selected_index]
        return None
    
    def get_selected_value(self) -> Optional[str]:
        """Get the value of the currently selected option."""
        option = self.get_selected_option()
        return option[0] if option else None
    
    def get_selected_label(self) -> Optional[str]:
        """Get the label of the currently selected option."""
        option = self.get_selected_option()
        return option[1] if option else None
    
    def set_selected_index(self, index: int, trigger_event: bool = True) -> None:
        """
        Set the selected option by index.
        
        Parameters
        ----------
        index : int
            New selected index
        trigger_event : bool
            Whether to trigger change event
        """
        if 0 <= index < len(self.options) and index != self.selected_index:
            old_index = self.selected_index
            old_value = self.get_selected_value()
            
            self.selected_index = index
            
            if trigger_event:
                self.trigger(ControlEvent.CHANGE, {
                    "index": index,
                    "value": self.get_selected_value(),
                    "old_index": old_index,
                    "old_value": old_value
                })
    
    def set_selected_value(self, value: str, trigger_event: bool = True) -> bool:
        """
        Set the selected option by value.
        
        Parameters
        ----------
        value : str
            Option value to select
        trigger_event : bool
            Whether to trigger change event
            
        Returns
        -------
        bool
            True if value was found and selected, False otherwise
        """
        for i, (opt_value, _) in enumerate(self.options):
            if opt_value == value:
                self.set_selected_index(i, trigger_event)
                return True
        return False
    
    def _render_self(self, canvas: np.ndarray) -> None:
        """Render the dropdown."""
        abs_x, abs_y = self.get_absolute_position()
        
        # Determine background color
        if not self.enabled:
            bg_color = self.style["disabled_color"]
        elif self.hovered:
            bg_color = self.style["hover_color"]
        else:
            bg_color = self.style["bg_color"]
        
        # Draw dropdown box
        cv2.rectangle(
            canvas,
            (abs_x, abs_y),
            (abs_x + self.width, abs_y + self.height),
            bg_color,
            -1
        )
        
        # Draw border
        cv2.rectangle(
            canvas,
            (abs_x, abs_y),
            (abs_x + self.width, abs_y + self.height),
            self.style["border_color"],
            self.style["border_width"]
        )
        
        # Draw selected option
        selected_label = self.get_selected_label() or "Select..."
        font = self.style["font"]
        font_scale = self.style["font_scale"]
        padding = self.style["padding"]
        
        cv2.putText(
            canvas,
            selected_label,
            (abs_x + padding, abs_y + self.height - padding),
            font,
            font_scale,
            self.style["fg_color"],
            1,
            cv2.LINE_AA
        )
        
        # Draw dropdown arrow
        arrow_size = 8
        arrow_x = abs_x + self.width - arrow_size - padding
        arrow_y = abs_y + (self.height - arrow_size) // 2
        
        if self.open:
            # Up arrow
            cv2.line(
                canvas,
                (arrow_x, arrow_y + arrow_size),
                (arrow_x + arrow_size // 2, arrow_y),
                self.style["fg_color"],
                1,
                cv2.LINE_AA
            )
            cv2.line(
                canvas,
                (arrow_x + arrow_size, arrow_y + arrow_size),
                (arrow_x + arrow_size // 2, arrow_y),
                self.style["fg_color"],
                1,
                cv2.LINE_AA
            )
        else:
            # Down arrow
            cv2.line(
                canvas,
                (arrow_x, arrow_y),
                (arrow_x + arrow_size // 2, arrow_y + arrow_size),
                self.style["fg_color"],
                1,
                cv2.LINE_AA
            )
            cv2.line(
                canvas,
                (arrow_x + arrow_size, arrow_y),
                (arrow_x + arrow_size // 2, arrow_y + arrow_size),
                self.style["fg_color"],
                1,
                cv2.LINE_AA
            )
        
        # Draw dropdown list if open
        if self.open:
            dropdown_y = abs_y + self.height
            
            # Draw dropdown background
            cv2.rectangle(
                canvas,
                (abs_x, dropdown_y),
                (abs_x + self.width, dropdown_y + self.dropdown_height),
                self.style["bg_color"],
                -1
            )
            
            # Draw border
            cv2.rectangle(
                canvas,
                (abs_x, dropdown_y),
                (abs_x + self.width, dropdown_y + self.dropdown_height),
                self.style["border_color"],
                self.style["border_width"]
            )
            
            # Draw options
            for i, (_, label) in enumerate(self.options):
                item_y = dropdown_y + i * self.item_height
                
                # Highlight hovered/selected item
                if i == self.hover_index:
                    cv2.rectangle(
                        canvas,
                        (abs_x, item_y),
                        (abs_x + self.width, item_y + self.item_height),
                        self.style["hover_color"],
                        -1
                    )
                elif i == self.selected_index:
                    cv2.rectangle(
                        canvas,
                        (abs_x, item_y),
                        (abs_x + self.width, item_y + self.item_height),
                        self.style["active_color"],
                        -1
                    )
                
                # Draw option text
                cv2.putText(
                    canvas,
                    label,
                    (abs_x + padding, item_y + self.item_height - padding),
                    font,
                    font_scale,
                    self.style["fg_color"],
                    1,
                    cv2.LINE_AA
                )
    
    def contains_point(self, point: Tuple[int, int]) -> bool:
        """Check if point is within control bounds, including dropdown area when open."""
        abs_x, abs_y = self.get_absolute_position()
        px, py = point
        
        # Check main control area
        in_main = (
            abs_x <= px <= abs_x + self.width and
            abs_y <= py <= abs_y + self.height
        )
        
        # Check dropdown area if open
        in_dropdown = (
            self.open and
            abs_x <= px <= abs_x + self.width and
            abs_y + self.height <= py <= abs_y + self.height + self.dropdown_height
        )
        
        return in_main or in_dropdown
    
    def handle_mouse_event(self, event_type: str, x: int, y: int, 
                          buttons: int, modifiers: Dict[str, bool]) -> bool:
        """Handle mouse events for the dropdown."""
        if not self.visible or not self.enabled:
            return False
        
        abs_x, abs_y = self.get_absolute_position()
        dropdown_y = abs_y + self.height
        
        # Check if point is in main control area
        in_main = (
            abs_x <= x <= abs_x + self.width and
            abs_y <= y <= abs_y + self.height
        )
        
        # Check if point is in dropdown area
        in_dropdown = (
            self.open and
            abs_x <= x <= abs_x + self.width and
            dropdown_y <= y <= dropdown_y + self.dropdown_height
        )
        
        # Update hover state
        self.hovered = in_main
        
        # Update hover index for dropdown items
        if in_dropdown:
            rel_y = y - dropdown_y
            self.hover_index = int(rel_y / self.item_height)
        else:
            self.hover_index = -1
        
        if event_type == "press":
            if in_main:
                # Toggle dropdown
                self.open = not self.open
                return True
            elif in_dropdown:
                # Select option
                self.set_selected_index(self.hover_index)
                self.open = False
                return True
            elif self.open:
                # Close dropdown if clicked outside
                self.open = False
                return True
        
        elif event_type == "move":
            if in_main or in_dropdown:
                self.trigger(ControlEvent.HOVER, {"x": x, "y": y})
                return True
        
        return False


class Toggle(UIControl):
    """Toggle switch control."""
    
    def __init__(self, id: str, x: int, y: int, width: int, height: int, 
                 value: bool = False, label: str = "", callback: Callable = None):
        """
        Initialize a toggle switch.
        
        Parameters
        ----------
        id : str
            Unique identifier
        x : int
            X-coordinate
        y : int
            Y-coordinate
        width : int
            Width
        height : int
            Height
        value : bool
            Initial state
        label : str
            Toggle label
        callback : Callable, optional
            Value change callback function
        """
        super().__init__(id, x, y, width, height, ControlType.TOGGLE)
        self.value = value
        self.label = label
        self.hovered = False
        
        # Register callback if provided
        if callback:
            self.on(ControlEvent.CHANGE, lambda e: callback(e["value"]))
    
    def set_value(self, value: bool, trigger_event: bool = True) -> None:
        """
        Set the toggle value.
        
        Parameters
        ----------
        value : bool
            New value
        trigger_event : bool
            Whether to trigger change event
        """
        if value != self.value:
            old_value = self.value
            self.value = value
            
            if trigger_event:
                self.trigger(ControlEvent.CHANGE, {"value": value, "old_value": old_value})
    
    def toggle(self) -> None:
        """Toggle the value."""
        self.set_value(not self.value)
    
    def _render_self(self, canvas: np.ndarray) -> None:
        """Render the toggle switch."""
        abs_x, abs_y = self.get_absolute_position()
        
        # Calculate toggle switch dimensions
        switch_width = 40
        switch_height = 20
        toggle_radius = switch_height // 2
        
        # Position toggle at the right side
        switch_x = abs_x + self.width - switch_width
        switch_y = abs_y + (self.height - switch_height) // 2
        
        # Determine colors
        if not self.enabled:
            track_color = self.style["disabled_color"]
            toggle_color = (200, 200, 200)
        elif self.value:
            track_color = self.style["active_color"]
            toggle_color = (255, 255, 255)
        else:
            track_color = (100, 100, 100)
            toggle_color = (255, 255, 255)
        
        # Draw track (rounded rectangle)
        cv2.rectangle(
            canvas,
            (switch_x + toggle_radius, switch_y),
            (switch_x + switch_width - toggle_radius, switch_y + switch_height),
            track_color,
            -1
        )
        
        cv2.circle(
            canvas,
            (switch_x + toggle_radius, switch_y + toggle_radius),
            toggle_radius,
            track_color,
            -1
        )
        
        cv2.circle(
            canvas,
            (switch_x + switch_width - toggle_radius, switch_y + toggle_radius),
            toggle_radius,
            track_color,
            -1
        )
        
        # Draw toggle position
        toggle_x = switch_x + switch_width - toggle_radius - 2 if self.value else switch_x + toggle_radius + 2
        
        cv2.circle(
            canvas,
            (toggle_x, switch_y + toggle_radius),
            toggle_radius - 2,
            toggle_color,
            -1
        )
        
        # Draw label
        if self.label:
            font = self.style["font"]
            font_scale = self.style["font_scale"]
            
            cv2.putText(
                canvas,
                self.label,
                (abs_x, abs_y + self.height // 2 + 5),
                font,
                font_scale,
                self.style["fg_color"],
                1,
                cv2.LINE_AA
            )
    
    def handle_mouse_event(self, event_type: str, x: int, y: int, 
                          buttons: int, modifiers: Dict[str, bool]) -> bool:
        """Handle mouse events for the toggle."""
        if not self.visible or not self.enabled:
            return False
        
        contains = self.contains_point((x, y))
        
        if event_type == "move":
            self.hovered = contains
            if contains:
                self.trigger(ControlEvent.HOVER, {"x": x, "y": y})
                return True
        
        elif event_type == "press" and contains:
            self.toggle()
            return True
        
        return False


class Panel(UIControl):
    """Container panel for organizing controls."""
    
    def __init__(self, id: str, x: int, y: int, width: int, height: int, 
                 title: str = "", draggable: bool = False, collapsible: bool = False,
                 minimized: bool = False):
        """
        Initialize a panel.
        
        Parameters
        ----------
        id : str
            Unique identifier
        x : int
            X-coordinate
        y : int
            Y-coordinate
        width : int
            Width
        height : int
            Height
        title : str
            Panel title
        draggable : bool
            Whether the panel can be dragged
        collapsible : bool
            Whether the panel can be collapsed
        minimized : bool
            Initial collapsed state
        """
        super().__init__(id, x, y, width, height, ControlType.PANEL)
        self.title = title
        self.draggable = draggable
        self.collapsible = collapsible
        self.minimized = minimized
        
        self.dragging = False
        self.drag_offset = (0, 0)
        
        # Header height
        self.header_height = 25 if title or collapsible else 0
        
        # Update style
        self.style.update({
            "bg_color": (40, 40, 40),
            "title_bg_color": (60, 60, 60),
            "alpha": 200  # Semi-transparent
        })
    
    def collapse(self) -> None:
        """Collapse the panel."""
        if self.collapsible and not self.minimized:
            self.minimized = True
    
    def expand(self) -> None:
        """Expand the panel."""
        if self.collapsible and self.minimized:
            self.minimized = False
    
    def toggle_collapse(self) -> None:
        """Toggle collapse state."""
        if self.collapsible:
            self.minimized = not self.minimized
    
    def _render_self(self, canvas: np.ndarray) -> None:
        """Render the panel."""
        abs_x, abs_y = self.get_absolute_position()
        
        # Create transparent overlay with alpha channel
        bg_color = (*self.style["bg_color"], self.style["alpha"])
        title_bg_color = (*self.style["title_bg_color"], self.style["alpha"])
        
        # Draw panel body if not minimized
        if not self.minimized:
            # Draw background
            cv2.rectangle(
                canvas,
                (abs_x, abs_y + self.header_height),
                (abs_x + self.width, abs_y + self.height),
                bg_color,
                -1
            )
            
            # Draw border
            cv2.rectangle(
                canvas,
                (abs_x, abs_y + self.header_height),
                (abs_x + self.width, abs_y + self.height),
                self.style["border_color"],
                self.style["border_width"]
            )
        
        # Draw header if needed
        if self.header_height > 0:
            # Draw header background
            cv2.rectangle(
                canvas,
                (abs_x, abs_y),
                (abs_x + self.width, abs_y + self.header_height),
                title_bg_color,
                -1
            )
            
            # Draw header border
            cv2.rectangle(
                canvas,
                (abs_x, abs_y),
                (abs_x + self.width, abs_y + self.header_height),
                self.style["border_color"],
                self.style["border_width"]
            )
            
            # Draw title
            if self.title:
                font = self.style["font"]
                font_scale = self.style["font_scale"]
                padding = self.style["padding"]
                
                cv2.putText(
                    canvas,
                    self.title,
                    (abs_x + padding, abs_y + self.header_height - 5),
                    font,
                    font_scale,
                    self.style["fg_color"],
                    1,
                    cv2.LINE_AA
                )
            
            # Draw collapse/expand button
            if self.collapsible:
                btn_size = 16
                btn_x = abs_x + self.width - btn_size - 5
                btn_y = abs_y + (self.header_height - btn_size) // 2
                
                # Draw button box
                cv2.rectangle(
                    canvas,
                    (btn_x, btn_y),
                    (btn_x + btn_size, btn_y + btn_size),
                    self.style["bg_color"],
                    1
                )
                
                # Draw +/- symbol
                if self.minimized:
                    # + symbol (to expand)
                    cv2.line(
                        canvas,
                        (btn_x + 4, btn_y + btn_size // 2),
                        (btn_x + btn_size - 4, btn_y + btn_size // 2),
                        self.style["fg_color"],
                        1
                    )
                    cv2.line(
                        canvas,
                        (btn_x + btn_size // 2, btn_y + 4),
                        (btn_x + btn_size // 2, btn_y + btn_size - 4),
                        self.style["fg_color"],
                        1
                    )
                else:
                    # - symbol (to collapse)
                    cv2.line(
                        canvas,
                        (btn_x + 4, btn_y + btn_size // 2),
                        (btn_x + btn_size - 4, btn_y + btn_size // 2),
                        self.style["fg_color"],
                        1
                    )
    
    def render(self, canvas: np.ndarray) -> None:
        """Render the panel and its children."""
        if not self.visible:
            return
        
        # Render panel
        self._render_self(canvas)
        
        # Render children only if not minimized
        if not self.minimized:
            for child in self.children:
                child.render(canvas)
    
    def handle_mouse_event(self, event_type: str, x: int, y: int, 
                          buttons: int, modifiers: Dict[str, bool]) -> bool:
        """Handle mouse events for the panel."""
        if not self.visible or not self.enabled:
            return False
        
        abs_x, abs_y = self.get_absolute_position()
        
        # Check if point is in header area
        in_header = (
            self.header_height > 0 and
            abs_x <= x <= abs_x + self.width and
            abs_y <= y <= abs_y + self.header_height
        )
        
        # Check for collapse button click
        if self.collapsible:
            btn_size = 16
            btn_x = abs_x + self.width - btn_size - 5
            btn_y = abs_y + (self.header_height - btn_size) // 2
            
            in_collapse_button = (
                btn_x <= x <= btn_x + btn_size and
                btn_y <= y <= btn_y + btn_size
            )
            
            if event_type == "press" and in_collapse_button:
                self.toggle_collapse()
                return True
        
        # Check if panel is being dragged
        if self.draggable and in_header:
            if event_type == "press":
                self.dragging = True
                self.drag_offset = (x - self.x, y - self.y)
                return True
            
            elif event_type == "move" and self.dragging:
                self.x = x - self.drag_offset[0]
                self.y = y - self.drag_offset[1]
                return True
        
        # Handle dragging release
        if event_type == "release" and self.dragging:
            self.dragging = False
            return True
        
        # If panel is minimized, don't process events for children
        if self.minimized:
            return in_header
        
        # Check if point is within panel body
        in_body = (
            abs_x <= x <= abs_x + self.width and
            abs_y + self.header_height <= y <= abs_y + self.height
        )
        
        # Handle events in children if within panel body
        if in_body:
            for child in reversed(self.children):
                if child.handle_mouse_event(event_type, x, y, buttons, modifiers):
                    return True
        
        # Return true if the point is within the panel (header or body)
        return in_header or in_body


class Legend(UIControl):
    """Legend for visualized metrics."""
    
    def __init__(self, id: str, x: int, y: int, width: int, height: int, 
                 title: str = "Legend"):
        """
        Initialize a legend.
        
        Parameters
        ----------
        id : str
            Unique identifier
        x : int
            X-coordinate
        y : int
            Y-coordinate
        width : int
            Width
        height : int
            Height
        title : str
            Legend title
        """
        super().__init__(id, x, y, width, height, ControlType.LEGEND)
        self.title = title
        self.metric: Optional[Metric] = None
        self.color_range: List[Tuple[float, Tuple[int, int, int]]] = []
        self.categories: List[Tuple[str, Tuple[int, int, int]]] = []
        
        # Update style
        self.style.update({
            "bg_color": (40, 40, 40),
            "title_bg_color": (60, 60, 60),
            "alpha": 200,  # Semi-transparent
            "item_height": 20
        })
    
    def set_metric(self, metric: Optional[Metric]) -> None:
        """
        Set the metric for the legend.
        
        Parameters
        ----------
        metric : Optional[Metric]
            Metric to display in legend
        """
        self.metric = metric
        self.color_range = []
        self.categories = []
        
        if metric:
            # Convert color scale to RGB tuples
            colors = []
            for color_hex in metric.color_scale:
                # Convert hex color to RGB
                r = int(color_hex[1:3], 16)
                g = int(color_hex[3:5], 16)
                b = int(color_hex[5:7], 16)
                colors.append((r, g, b))
            
            # Set up color range or categories based on metric type
            if metric.metric_type == MetricType.CATEGORICAL:
                # For categorical metrics, create category-color pairs
                if hasattr(metric, 'categories') and metric.categories:
                    for i, category in enumerate(metric.categories):
                        color_idx = i % len(colors)
                        self.categories.append((category, colors[color_idx]))
            else:
                # For numeric metrics, create value-color pairs
                min_val, max_val = metric.range
                if min_val is not None and max_val is not None:
                    num_steps = len(colors)
                    step = (max_val - min_val) / (num_steps - 1) if num_steps > 1 else 0
                    
                    for i in range(num_steps):
                        value = min_val + i * step
                        self.color_range.append((value, colors[i]))
    
    def _render_self(self, canvas: np.ndarray) -> None:
        """Render the legend."""
        if not self.metric:
            return
            
        abs_x, abs_y = self.get_absolute_position()
        
        # Create overlay with alpha channel
        bg_color = (*self.style["bg_color"], self.style["alpha"])
        title_bg_color = (*self.style["title_bg_color"], self.style["alpha"])
        
        # Calculate header height
        header_height = 25
        
        # Draw background
        cv2.rectangle(
            canvas,
            (abs_x, abs_y),
            (abs_x + self.width, abs_y + self.height),
            bg_color,
            -1
        )
        
        # Draw border
        cv2.rectangle(
            canvas,
            (abs_x, abs_y),
            (abs_x + self.width, abs_y + self.height),
            self.style["border_color"],
            self.style["border_width"]
        )
        
        # Draw header
        cv2.rectangle(
            canvas,
            (abs_x, abs_y),
            (abs_x + self.width, abs_y + header_height),
            title_bg_color,
            -1
        )
        
        # Draw title
        font = self.style["font"]
        font_scale = self.style["font_scale"]
        padding = self.style["padding"]
        
        title_text = self.title
        if self.metric:
            title_text = f"{title_text}: {self.metric.name}"
            
        cv2.putText(
            canvas,
            title_text,
            (abs_x + padding, abs_y + header_height - 5),
            font,
            font_scale,
            self.style["fg_color"],
            1,
            cv2.LINE_AA
        )
        
        # Draw content based on metric type
        content_y = abs_y + header_height + padding
        item_height = self.style["item_height"]
        
        if self.categories:
            # Draw categorical legend
            for i, (category, color) in enumerate(self.categories):
                item_y = content_y + i * item_height
                
                # Draw color box
                cv2.rectangle(
                    canvas,
                    (abs_x + padding, item_y),
                    (abs_x + padding + 15, item_y + 15),
                    color,
                    -1
                )
                
                # Draw border around color box
                cv2.rectangle(
                    canvas,
                    (abs_x + padding, item_y),
                    (abs_x + padding + 15, item_y + 15),
                    (255, 255, 255),
                    1
                )
                
                # Draw category label
                cv2.putText(
                    canvas,
                    category,
                    (abs_x + padding + 20, item_y + 12),
                    font,
                    font_scale,
                    self.style["fg_color"],
                    1,
                    cv2.LINE_AA
                )
        
        elif self.color_range:
            # Draw numeric legend
            if len(self.color_range) >= 2:
                # Draw gradient bar
                bar_width = self.width - 2 * padding
                bar_height = 15
                bar_y = content_y
                
                # Draw individual color segments
                segment_width = bar_width / (len(self.color_range) - 1)
                
                for i in range(len(self.color_range) - 1):
                    start_x = abs_x + padding + int(i * segment_width)
                    end_x = abs_x + padding + int((i + 1) * segment_width)
                    start_color = self.color_range[i][1]
                    end_color = self.color_range[i + 1][1]
                    
                    # Create gradient between colors
                    for j in range(int(end_x - start_x)):
                        ratio = j / (end_x - start_x)
                        color = (
                            int(start_color[0] * (1 - ratio) + end_color[0] * ratio),
                            int(start_color[1] * (1 - ratio) + end_color[1] * ratio),
                            int(start_color[2] * (1 - ratio) + end_color[2] * ratio)
                        )
                        
                        cv2.line(
                            canvas,
                            (start_x + j, bar_y),
                            (start_x + j, bar_y + bar_height),
                            color,
                            1
                        )
                
                # Draw border around gradient bar
                cv2.rectangle(
                    canvas,
                    (abs_x + padding, bar_y),
                    (abs_x + padding + bar_width, bar_y + bar_height),
                    (255, 255, 255),
                    1
                )
                
                # Draw min and max values
                min_val = self.color_range[0][0]
                max_val = self.color_range[-1][0]
                
                # Format values
                min_text = f"{min_val:.1f}" if isinstance(min_val, float) else str(min_val)
                max_text = f"{max_val:.1f}" if isinstance(max_val, float) else str(max_val)
                
                # Draw min value
                cv2.putText(
                    canvas,
                    min_text,
                    (abs_x + padding, bar_y + bar_height + 15),
                    font,
                    font_scale,
                    self.style["fg_color"],
                    1,
                    cv2.LINE_AA
                )
                
                # Measure max text width
                (max_width, _), _ = cv2.getTextSize(
                    max_text, font, font_scale, 1
                )
                
                # Draw max value
                cv2.putText(
                    canvas,
                    max_text,
                    (abs_x + padding + bar_width - max_width, bar_y + bar_height + 15),
                    font,
                    font_scale,
                    self.style["fg_color"],
                    1,
                    cv2.LINE_AA
                )
                
                # Draw unit if available
                if self.metric and self.metric.unit:
                    unit_y = bar_y + bar_height + 35
                    
                    cv2.putText(
                        canvas,
                        f"Unit: {self.metric.unit}",
                        (abs_x + padding, unit_y),
                        font,
                        font_scale,
                        self.style["fg_color"],
                        1,
                        cv2.LINE_AA
                    )


class UIController:
    """
    Controller for managing UI components and interactions.
    
    This class manages the creation, rendering, and interaction handling
    for all UI controls in the globe visualization.
    """
    
    def __init__(self, width: int, height: int):
        """
        Initialize the UI controller.
        
        Parameters
        ----------
        width : int
            Width of the UI canvas
        height : int
            Height of the UI canvas
        """
        self.width = width
        self.height = height
        self.controls: Dict[str, UIControl] = {}
        self.canvas = np.zeros((height, width, 4), dtype=np.uint8)
        
        # Track control interaction state
        self.hovered_control: Optional[UIControl] = None
        self.active_control: Optional[UIControl] = None
        self.dragging = False
        self.drag_start_pos = (0, 0)
        
        # Event handlers at controller level
        self.on_globe_rotate: Optional[Callable] = None
        self.on_globe_zoom: Optional[Callable] = None
        self.on_metric_change: Optional[Callable] = None
        self.on_entity_select: Optional[Callable] = None
    
    def add_control(self, control: UIControl) -> None:
        """
        Add a control to the UI.
        
        Parameters
        ----------
        control : UIControl
            Control to add
        """
        self.controls[control.id] = control
    
    def remove_control(self, control_id: str) -> None:
        """
        Remove a control from the UI.
        
        Parameters
        ----------
        control_id : str
            ID of the control to remove
        """
        if control_id in self.controls:
            del self.controls[control_id]
    
    def get_control(self, control_id: str) -> Optional[UIControl]:
        """
        Get a control by ID.
        
        Parameters
        ----------
        control_id : str
            ID of the control to retrieve
            
        Returns
        -------
        Optional[UIControl]
            The control if found, None otherwise
        """
        return self.controls.get(control_id)
    
    def clear_controls(self) -> None:
        """Clear all controls from the UI."""
        self.controls = {}
    
    def set_on_globe_rotate(self, callback: Callable) -> None:
        """
        Set the callback for globe rotation events.
        
        Parameters
        ----------
        callback : Callable
            Callback function for rotation events
        """
        self.on_globe_rotate = callback
    
    def set_on_globe_zoom(self, callback: Callable) -> None:
        """
        Set the callback for globe zoom events.
        
        Parameters
        ----------
        callback : Callable
            Callback function for zoom events
        """
        self.on_globe_zoom = callback
    
    def set_on_metric_change(self, callback: Callable) -> None:
        """
        Set the callback for metric change events.
        
        Parameters
        ----------
        callback : Callable
            Callback function for metric change events
        """
        self.on_metric_change = callback
    
    def set_on_entity_select(self, callback: Callable) -> None:
        """
        Set the callback for entity selection events.
        
        Parameters
        ----------
        callback : Callable
            Callback function for entity selection events
        """
        self.on_entity_select = callback
    
    def render(self) -> np.ndarray:
        """
        Render all UI controls.
        
        Returns
        -------
        np.ndarray
            Rendered UI canvas
        """
        # Clear the canvas
        self.canvas.fill(0)
        
        # Sort controls by z-index (assumed to be the order they were added)
        sorted_controls = sorted(
            self.controls.values(),
            key=lambda c: list(self.controls.values()).index(c)
        )
        
        # Render each control
        for control in sorted_controls:
            control.render(self.canvas)
        
        return self.canvas
    
    def handle_mouse_event(self, event_type: str, x: int, y: int, 
                          buttons: int = 0, modifiers: Dict[str, bool] = None) -> bool:
        """
        Handle a mouse event.
        
        Parameters
        ----------
        event_type : str
            Type of mouse event ('press', 'release', 'move', 'drag_start', 'drag', 'drag_end')
        x : int
            X-coordinate
        y : int
            Y-coordinate
        buttons : int
            Mouse buttons state
        modifiers : Dict[str, bool]
            Keyboard modifiers
            
        Returns
        -------
        bool
            True if event was handled, False otherwise
        """
        if modifiers is None:
            modifiers = {}
        
        # Special handling for drag events
        if event_type == "press":
            self.drag_start_pos = (x, y)
        
        elif event_type == "move" and self.active_control:
            # Check if this is actually a drag
            if self.active_control and not self.dragging:
                dx = abs(x - self.drag_start_pos[0])
                dy = abs(y - self.drag_start_pos[1])
                
                if dx > 5 or dy > 5:
                    self.dragging = True
                    event_type = "drag_start"
        
        elif event_type == "move" and self.dragging:
            event_type = "drag"
        
        elif event_type == "release" and self.dragging:
            event_type = "drag_end"
            self.dragging = False
        
        # Process control events (in reverse order for proper z-ordering)
        for control_id in reversed(list(self.controls.keys())):
            control = self.controls[control_id]
            
            if control.handle_mouse_event(event_type, x, y, buttons, modifiers):
                if event_type == "press":
                    self.active_control = control
                elif event_type == "release":
                    self.active_control = None
                
                return True
        
        # If no control handled the event, and it's in the main view area,
        # process as globe interaction
        if event_type == "drag":
            dx = x - self.drag_start_pos[0]
            dy = y - self.drag_start_pos[1]
            
            if self.on_globe_rotate:
                # Convert pixel movement to rotation angles
                # Horizontal movement (dx) causes vertical axis rotation
                # Vertical movement (dy) causes horizontal axis rotation
                angle_x = dy * 0.5  # Vertical movement -> rotation around X axis
                angle_y = -dx * 0.5  # Horizontal movement -> rotation around Y axis
                
                self.on_globe_rotate(angle_x, angle_y)
            
            self.drag_start_pos = (x, y)
            return True
        
        # Reset active control if clicked outside controls
        if event_type == "press":
            self.active_control = None
        
        return False
    
    def handle_key_event(self, key: int, modifiers: Dict[str, bool] = None) -> bool:
        """
        Handle a key event.
        
        Parameters
        ----------
        key : int
            Key code
        modifiers : Dict[str, bool]
            Keyboard modifiers
            
        Returns
        -------
        bool
            True if event was handled, False otherwise
        """
        if modifiers is None:
            modifiers = {}
        
        # Process key events in all controls
        for control in self.controls.values():
            if control.handle_key_event(key, modifiers):
                return True
        
        # Handle global keyboard shortcuts
        if key == ord('+') or key == ord('='):
            if self.on_globe_zoom:
                self.on_globe_zoom(0.1)  # Zoom in
                return True
        
        elif key == ord('-') or key == ord('_'):
            if self.on_globe_zoom:
                self.on_globe_zoom(-0.1)  # Zoom out
                return True
        
        return False
    
    def create_control_panel(self, metrics: Dict[str, Metric], 
                           current_metric: Optional[str] = None) -> Panel:
        """
        Create a standard control panel with metric selection and other controls.
        
        Parameters
        ----------
        metrics : Dict[str, Metric]
            Dictionary of available metrics
        current_metric : Optional[str]
            Currently selected metric ID
            
        Returns
        -------
        Panel
            The created control panel
        """
        # Create main panel
        panel = Panel(
            "control_panel",
            x=10,
            y=10,
            width=250,
            height=400,
            title="Globe Controls",
            draggable=True,
            collapsible=True
        )
        
        # Create metric selector
        metric_label = UIControl(
            "metric_label",
            x=10,
            y=35,
            width=230,
            height=20,
            control_type=ControlType.TEXT
        )
        
        # Create dropdown options from metrics
        options = []
        for metric_id, metric in metrics.items():
            options.append((metric_id, metric.name))
        
        # Sort options alphabetically by name
        options.sort(key=lambda o: o[1])
        
        # Find index of current metric
        selected_index = 0
        if current_metric:
            for i, (metric_id, _) in enumerate(options):
                if metric_id == current_metric:
                    selected_index = i
                    break
        
        metric_dropdown = Dropdown(
            "metric_dropdown",
            x=10,
            y=60,
            width=230,
            height=25,
            options=options,
            selected_index=selected_index
        )
        
        # Set up callback for metric change
        def on_metric_change(value, index):
            if self.on_metric_change:
                self.on_metric_change(value)
        
        metric_dropdown.on(ControlEvent.CHANGE, on_metric_change)
        
        # Add rotation controls
        rotation_label = UIControl(
            "rotation_label",
            x=10,
            y=100,
            width=230,
            height=20,
            control_type=ControlType.TEXT
        )
        
        # Create reset view button
        reset_view_btn = Button(
            "reset_view_btn",
            x=10,
            y=125,
            width=110,
            height=30,
            text="Reset View"
        )
        
        # Create snapshot button
        snapshot_btn = Button(
            "snapshot_btn",
            x=130,
            y=125,
            width=110,
            height=30,
            text="Take Snapshot"
        )
        
        # Add UI settings
        ui_label = UIControl(
            "ui_label",
            x=10,
            y=165,
            width=230,
            height=20,
            control_type=ControlType.TEXT
        )
        
        # Create toggle for showing labels
        show_labels_toggle = Toggle(
            "show_labels_toggle",
            x=10,
            y=190,
            width=230,
            height=25,
            value=True,
            label="Show Labels"
        )
        
        # Create toggle for showing outlines
        show_outlines_toggle = Toggle(
            "show_outlines_toggle",
            x=10,
            y=220,
            width=230,
            height=25,
            value=True,
            label="Show Country Outlines"
        )
        
        # Add controls to panel
        panel.add_child(metric_label)
        panel.add_child(metric_dropdown)
        panel.add_child(rotation_label)
        panel.add_child(reset_view_btn)
        panel.add_child(snapshot_btn)
        panel.add_child(ui_label)
        panel.add_child(show_labels_toggle)
        panel.add_child(show_outlines_toggle)
        
        # Add panel to controller
        self.add_control(panel)
        
        return panel
    
    def create_legend(self, metric: Optional[Metric] = None) -> Legend:
        """
        Create a legend for the current metric.
        
        Parameters
        ----------
        metric : Optional[Metric]
            Metric to display in the legend
            
        Returns
        -------
        Legend
            The created legend
        """
        legend = Legend(
            "metric_legend",
            x=self.width - 260,
            y=10,
            width=250,
            height=150,
            title="Legend"
        )
        
        if metric:
            legend.set_metric(metric)
        
        # Add to controller
        self.add_control(legend)
        
        return legend