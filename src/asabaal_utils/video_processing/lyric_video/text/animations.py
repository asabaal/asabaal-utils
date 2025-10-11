"""Text animation system for kinetic typography."""

from enum import Enum
from dataclasses import dataclass
from typing import Tuple, Optional, Callable
import numpy as np
import math


class AnimationType(Enum):
    """Available text animation types."""
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    SLIDE_IN = "slide_in"
    SLIDE_OUT = "slide_out"
    SCALE_IN = "scale_in"
    SCALE_OUT = "scale_out"
    ROTATE_IN = "rotate_in"
    TYPEWRITER = "typewriter"
    BOUNCE_IN = "bounce_in"
    ELASTIC_IN = "elastic_in"
    WAVE = "wave"
    SHAKE = "shake"
    GLOW_PULSE = "glow_pulse"


class AnimationEasing(Enum):
    """Easing functions for smooth animations."""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    BOUNCE = "bounce"
    ELASTIC = "elastic"
    BACK = "back"


@dataclass
class AnimationState:
    """Current state of an animation."""
    position: Tuple[float, float] = (0.0, 0.0)
    scale: Tuple[float, float] = (1.0, 1.0)
    rotation: float = 0.0
    opacity: float = 1.0
    char_progress: float = 1.0  # For character-by-character animations


class TextAnimation:
    """Manages text animations with various effects."""
    
    @staticmethod
    def ease_linear(t: float) -> float:
        """Linear easing function."""
        return t
        
    @staticmethod
    def ease_in_quad(t: float) -> float:
        """Quadratic ease-in."""
        return t * t
        
    @staticmethod
    def ease_out_quad(t: float) -> float:
        """Quadratic ease-out."""
        return t * (2 - t)
        
    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        """Quadratic ease-in-out."""
        if t < 0.5:
            return 2 * t * t
        return -1 + (4 - 2 * t) * t
        
    @staticmethod
    def ease_bounce(t: float) -> float:
        """Bounce easing."""
        if t < 0.363636:
            return 7.5625 * t * t
        elif t < 0.727272:
            t -= 0.545454
            return 7.5625 * t * t + 0.75
        elif t < 0.909090:
            t -= 0.818181
            return 7.5625 * t * t + 0.9375
        else:
            t -= 0.954545
            return 7.5625 * t * t + 0.984375
            
    @staticmethod
    def ease_elastic(t: float) -> float:
        """Elastic easing."""
        if t == 0 or t == 1:
            return t
        p = 0.3
        s = p / 4
        return pow(2, -10 * t) * math.sin((t - s) * (2 * math.pi) / p) + 1
        
    @staticmethod
    def ease_back(t: float) -> float:
        """Back easing (overshoot)."""
        s = 1.70158
        return t * t * ((s + 1) * t - s)
        
    @staticmethod
    def get_easing_function(easing: AnimationEasing) -> Callable[[float], float]:
        """Get easing function by type."""
        easing_functions = {
            AnimationEasing.LINEAR: TextAnimation.ease_linear,
            AnimationEasing.EASE_IN: TextAnimation.ease_in_quad,
            AnimationEasing.EASE_OUT: TextAnimation.ease_out_quad,
            AnimationEasing.EASE_IN_OUT: TextAnimation.ease_in_out_quad,
            AnimationEasing.BOUNCE: TextAnimation.ease_bounce,
            AnimationEasing.ELASTIC: TextAnimation.ease_elastic,
            AnimationEasing.BACK: TextAnimation.ease_back
        }
        return easing_functions.get(easing, TextAnimation.ease_linear)
        
    @staticmethod
    def calculate_animation_state(animation_type: AnimationType,
                                 progress: float,
                                 easing: AnimationEasing = AnimationEasing.EASE_OUT,
                                 start_pos: Tuple[float, float] = (0, 0),
                                 target_pos: Tuple[float, float] = (0, 0),
                                 amplitude: float = 1.0) -> AnimationState:
        """Calculate animation state for given progress.
        
        Args:
            animation_type: Type of animation
            progress: Animation progress (0.0 to 1.0)
            easing: Easing function to use
            start_pos: Starting position
            target_pos: Target position
            amplitude: Animation amplitude/strength
            
        Returns:
            Current animation state
        """
        # Apply easing
        easing_func = TextAnimation.get_easing_function(easing)
        eased_progress = easing_func(progress)
        
        state = AnimationState()
        
        if animation_type == AnimationType.FADE_IN:
            state.opacity = eased_progress
            state.position = target_pos
            
        elif animation_type == AnimationType.FADE_OUT:
            state.opacity = 1.0 - eased_progress
            state.position = target_pos
            
        elif animation_type == AnimationType.SLIDE_IN:
            # Slide from start to target
            state.position = (
                start_pos[0] + (target_pos[0] - start_pos[0]) * eased_progress,
                start_pos[1] + (target_pos[1] - start_pos[1]) * eased_progress
            )
            
        elif animation_type == AnimationType.SLIDE_OUT:
            # Slide from target to end
            end_x = target_pos[0] + (target_pos[0] - start_pos[0])
            end_y = target_pos[1] + (target_pos[1] - start_pos[1])
            state.position = (
                target_pos[0] + (end_x - target_pos[0]) * eased_progress,
                target_pos[1] + (end_y - target_pos[1]) * eased_progress
            )
            
        elif animation_type == AnimationType.SCALE_IN:
            state.scale = (eased_progress, eased_progress)
            state.position = target_pos
            
        elif animation_type == AnimationType.SCALE_OUT:
            scale = 1.0 + (amplitude - 1.0) * eased_progress
            state.scale = (scale, scale)
            state.position = target_pos
            state.opacity = 1.0 - eased_progress
            
        elif animation_type == AnimationType.ROTATE_IN:
            state.rotation = 360 * (1.0 - eased_progress) * amplitude
            state.position = target_pos
            state.opacity = eased_progress
            
        elif animation_type == AnimationType.TYPEWRITER:
            state.char_progress = eased_progress
            state.position = target_pos
            
        elif animation_type == AnimationType.BOUNCE_IN:
            # Use bounce easing for position
            bounce_progress = TextAnimation.ease_bounce(progress)
            state.position = (
                start_pos[0] + (target_pos[0] - start_pos[0]) * bounce_progress,
                start_pos[1] + (target_pos[1] - start_pos[1]) * bounce_progress
            )
            state.opacity = min(progress * 2, 1.0)  # Quick fade in
            
        elif animation_type == AnimationType.ELASTIC_IN:
            # Use elastic easing
            elastic_progress = TextAnimation.ease_elastic(progress)
            state.scale = (elastic_progress, elastic_progress)
            state.position = target_pos
            state.opacity = min(progress * 3, 1.0)  # Quick fade in
            
        elif animation_type == AnimationType.WAVE:
            # Wave motion
            wave_offset = math.sin(progress * math.pi * 2 * amplitude) * 20
            state.position = (target_pos[0], target_pos[1] + wave_offset)
            
        elif animation_type == AnimationType.SHAKE:
            # Random shake
            if progress < 1.0:
                shake_x = (np.random.random() - 0.5) * amplitude * 10
                shake_y = (np.random.random() - 0.5) * amplitude * 10
                state.position = (target_pos[0] + shake_x, target_pos[1] + shake_y)
            else:
                state.position = target_pos
                
        elif animation_type == AnimationType.GLOW_PULSE:
            # Pulsing glow effect (handled in rendering)
            state.position = target_pos
            # Store glow intensity in opacity for renderer to use
            state.opacity = 0.5 + 0.5 * math.sin(progress * math.pi * 2 * amplitude)
            
        return state
        
    @staticmethod
    def interpolate_states(state1: AnimationState, state2: AnimationState, 
                          blend: float) -> AnimationState:
        """Interpolate between two animation states.
        
        Args:
            state1: First state
            state2: Second state
            blend: Blend factor (0.0 = state1, 1.0 = state2)
            
        Returns:
            Interpolated state
        """
        return AnimationState(
            position=(
                state1.position[0] + (state2.position[0] - state1.position[0]) * blend,
                state1.position[1] + (state2.position[1] - state1.position[1]) * blend
            ),
            scale=(
                state1.scale[0] + (state2.scale[0] - state1.scale[0]) * blend,
                state1.scale[1] + (state2.scale[1] - state1.scale[1]) * blend
            ),
            rotation=state1.rotation + (state2.rotation - state1.rotation) * blend,
            opacity=state1.opacity + (state2.opacity - state1.opacity) * blend,
            char_progress=state1.char_progress + (state2.char_progress - state1.char_progress) * blend
        )