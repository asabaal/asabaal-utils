"""Predefined effect library with common video editor style effects."""

from typing import Dict, List
from .motion_effects import MotionEffect, EffectType, EffectKeyframe, create_effect


class EffectLibrary:
    """Library of predefined motion effects."""
    
    @staticmethod
    def cinematic_zoom_in(duration: float = 3.0) -> MotionEffect:
        """Slow cinematic zoom in effect."""
        return create_effect(
            EffectType.ZOOM_IN,
            duration=duration,
            start_value=0.0,
            peak_value=0.8,
            easing='ease_in_out',
            audio_reactive=True,
            energy_sensitivity=0.2
        )
    
    @staticmethod
    def dramatic_zoom_out(duration: float = 2.0) -> MotionEffect:
        """Dramatic zoom out effect."""
        return create_effect(
            EffectType.ZOOM_OUT,
            duration=duration,
            start_value=0.0,
            peak_value=1.0,
            easing='ease_out',
            audio_reactive=True,
            energy_sensitivity=0.3
        )
    
    @staticmethod
    def sliding_text_left(duration: float = 1.5) -> MotionEffect:
        """Text slides in from left."""
        return create_effect(
            EffectType.SLIDE_IN_LEFT,
            duration=duration,
            start_value=0.0,
            peak_value=1.0,
            easing='ease_out',
            audio_reactive=True,
            beat_multiplier=1.2
        )
    
    @staticmethod
    def sliding_text_right(duration: float = 1.5) -> MotionEffect:
        """Text slides in from right."""
        return create_effect(
            EffectType.SLIDE_IN_RIGHT,
            duration=duration,
            start_value=0.0,
            peak_value=1.0,
            easing='ease_out',
            audio_reactive=True,
            beat_multiplier=1.2
        )
    
    @staticmethod
    def bouncy_entrance(duration: float = 1.0) -> MotionEffect:
        """Bouncy scale entrance effect."""
        return create_effect(
            EffectType.SCALE_BOUNCE,
            duration=duration,
            start_value=0.0,
            peak_value=1.0,
            easing='bounce',
            audio_reactive=True,
            beat_multiplier=1.5
        )
    
    @staticmethod
    def elastic_entrance(duration: float = 1.2) -> MotionEffect:
        """Elastic scale entrance effect."""
        return create_effect(
            EffectType.SCALE_ELASTIC,
            duration=duration,
            start_value=0.0,
            peak_value=1.0,
            easing='elastic',
            audio_reactive=True,
            energy_sensitivity=0.4
        )
    
    @staticmethod
    def smooth_fade_in(duration: float = 0.8) -> MotionEffect:
        """Smooth fade in effect."""
        return create_effect(
            EffectType.FADE_IN,
            duration=duration,
            start_value=0.0,
            peak_value=1.0,
            easing='ease_in_out'
        )
    
    @staticmethod
    def dramatic_fade_out(duration: float = 1.0) -> MotionEffect:
        """Dramatic fade out effect."""
        return create_effect(
            EffectType.FADE_OUT,
            duration=duration,
            start_value=0.0,
            peak_value=1.0,
            easing='ease_in'
        )
    
    @staticmethod
    def pulse_beat_sync(duration: float = 0.5) -> MotionEffect:
        """Pulsing effect synchronized to beats."""
        return create_effect(
            EffectType.SCALE_PULSE,
            duration=duration,
            start_value=0.0,
            peak_value=1.0,
            easing='ease_in_out',
            loop=True,
            audio_reactive=True,
            beat_multiplier=2.0,
            energy_sensitivity=0.5
        )
    
    @staticmethod
    def camera_shake_intense(duration: float = 0.3) -> MotionEffect:
        """Intense camera shake effect."""
        return create_effect(
            EffectType.CAMERA_SHAKE,
            duration=duration,
            start_value=0.0,
            peak_value=1.0,
            easing='ease_out',
            audio_reactive=True,
            beat_multiplier=2.0
        )
    
    @staticmethod
    def rotate_spin_in(duration: float = 1.0) -> MotionEffect:
        """Spinning rotation entrance."""
        return create_effect(
            EffectType.ROTATE_CW,
            duration=duration,
            start_value=0.0,
            peak_value=1.0,
            easing='ease_out',
            audio_reactive=True,
            energy_sensitivity=0.3
        )
    
    @staticmethod
    def wave_distortion(duration: float = 2.0) -> MotionEffect:
        """Horizontal wave distortion."""
        return create_effect(
            EffectType.WAVE_HORIZONTAL,
            duration=duration,
            start_value=0.0,
            peak_value=1.0,
            easing='ease_in_out',
            loop=True,
            amplitude=15,
            frequency=0.15,
            audio_reactive=True,
            energy_sensitivity=0.6
        )
    
    @staticmethod
    def motion_blur_fast(duration: float = 0.5) -> MotionEffect:
        """Fast motion blur effect."""
        return create_effect(
            EffectType.MOTION_BLUR,
            duration=duration,
            start_value=0.0,
            peak_value=1.0,
            easing='ease_in_out',
            angle=45,
            audio_reactive=True,
            beat_multiplier=1.8
        )
    
    @staticmethod
    def color_shift_rainbow(duration: float = 3.0) -> MotionEffect:
        """Rainbow color shifting effect."""
        return create_effect(
            EffectType.COLOR_SHIFT,
            duration=duration,
            start_value=0.0,
            peak_value=1.0,
            easing='linear',
            loop=True,
            hue_range=360,
            audio_reactive=True,
            energy_sensitivity=0.4
        )
    
    @staticmethod
    def brightness_strobe(duration: float = 0.2) -> MotionEffect:
        """Strobe brightness effect."""
        return create_effect(
            EffectType.BRIGHTNESS_PULSE,
            duration=duration,
            start_value=0.0,
            peak_value=1.0,
            easing='linear',
            loop=True,
            audio_reactive=True,
            beat_multiplier=3.0
        )
    
    @staticmethod
    def pan_follow_motion(duration: float = 2.0) -> MotionEffect:
        """Pan that follows background motion."""
        return create_effect(
            EffectType.PAN_LEFT,
            duration=duration,
            start_value=0.0,
            peak_value=0.5,
            easing='ease_in_out',
            audio_reactive=True,
            energy_sensitivity=0.3
        )
    
    # === BOLD NEW EFFECTS ===
    @staticmethod
    def digital_glitch_intense(duration: float = 0.5) -> MotionEffect:
        """Intense digital glitch effect."""
        return create_effect(
            EffectType.GLITCH_DIGITAL,
            duration=duration,
            start_value=0.0,
            peak_value=1.0,
            easing='linear',
            audio_reactive=True,
            beat_multiplier=2.5
        )
    
    @staticmethod
    def neon_cyberpunk_glow(duration: float = 2.0) -> MotionEffect:
        """Cyberpunk neon glow effect."""
        return create_effect(
            EffectType.NEON_GLOW,
            duration=duration,
            start_value=0.0,
            peak_value=1.0,
            easing='ease_in_out',
            loop=True,
            audio_reactive=True,
            energy_sensitivity=0.6
        )
    
    @staticmethod
    def energy_explosion(duration: float = 1.0) -> MotionEffect:
        """Energy burst explosion effect."""
        return create_effect(
            EffectType.ENERGY_BURST,
            duration=duration,
            start_value=0.0,
            peak_value=1.0,
            easing='ease_out',
            audio_reactive=True,
            beat_multiplier=3.0
        )
    
    @staticmethod
    def liquid_dream_warp(duration: float = 3.0) -> MotionEffect:
        """Dreamy liquid warp effect."""
        return create_effect(
            EffectType.LIQUID_WARP,
            duration=duration,
            start_value=0.0,
            peak_value=1.0,
            easing='ease_in_out',
            loop=True,
            audio_reactive=True,
            energy_sensitivity=0.4
        )
    
    @staticmethod
    def portal_dimensional_rift(duration: float = 2.5) -> MotionEffect:
        """Portal swirl dimensional rift."""
        return create_effect(
            EffectType.PORTAL_SWIRL,
            duration=duration,
            start_value=0.0,
            peak_value=1.0,
            easing='elastic',
            audio_reactive=True,
            energy_sensitivity=0.7
        )
    
    @staticmethod
    def hologram_sci_fi(duration: float = 1.5) -> MotionEffect:
        """Sci-fi hologram flicker effect."""
        return create_effect(
            EffectType.HOLOGRAM_FLICKER,
            duration=duration,
            start_value=0.0,
            peak_value=1.0,
            easing='linear',
            loop=True,
            audio_reactive=True,
            beat_multiplier=1.8
        )
    
    @staticmethod
    def shatter_glass_break(duration: float = 0.8) -> MotionEffect:
        """Glass shatter break effect."""
        return create_effect(
            EffectType.SHATTER_BREAK,
            duration=duration,
            start_value=0.0,
            peak_value=1.0,
            easing='ease_out',
            audio_reactive=True,
            beat_multiplier=2.0
        )
    
    @staticmethod
    def kaleidoscope_trip(duration: float = 4.0) -> MotionEffect:
        """Kaleidoscope psychedelic effect."""
        return create_effect(
            EffectType.MIRROR_KALEIDOSCOPE,
            duration=duration,
            start_value=0.0,
            peak_value=1.0,
            easing='ease_in_out',
            loop=True,
            segments=8,
            audio_reactive=True,
            energy_sensitivity=0.5
        )


# Pre-built effect combinations
EFFECT_COMBINATIONS = {
    "energetic_entrance": [
        EffectLibrary.sliding_text_left(1.0),
        EffectLibrary.bouncy_entrance(0.8),
        EffectLibrary.pulse_beat_sync(0.5)
    ],
    
    "cinematic_reveal": [
        EffectLibrary.smooth_fade_in(1.5),
        EffectLibrary.cinematic_zoom_in(3.0),
        EffectLibrary.color_shift_rainbow(4.0)
    ],
    
    "dramatic_impact": [
        EffectLibrary.camera_shake_intense(0.3),
        EffectLibrary.brightness_strobe(0.2),
        EffectLibrary.elastic_entrance(1.0)
    ],
    
    "smooth_storytelling": [
        EffectLibrary.smooth_fade_in(1.0),
        EffectLibrary.pan_follow_motion(3.0),
        EffectLibrary.dramatic_fade_out(1.5)
    ],
    
    "electronic_vibe": [
        EffectLibrary.wave_distortion(2.0),
        EffectLibrary.motion_blur_fast(0.5),
        EffectLibrary.color_shift_rainbow(3.0),
        EffectLibrary.pulse_beat_sync(0.4)
    ],
    
    "classic_slide": [
        EffectLibrary.sliding_text_right(1.2),
        EffectLibrary.smooth_fade_in(0.8),
        EffectLibrary.dramatic_fade_out(1.0)
    ],
    
    # BOLD NEW COMBINATIONS
    "cyberpunk_assault": [
        EffectLibrary.digital_glitch_intense(0.3),
        EffectLibrary.neon_cyberpunk_glow(2.0),
        EffectLibrary.hologram_sci_fi(1.5),
        EffectLibrary.energy_explosion(0.8)
    ],
    
    "psychedelic_trip": [
        EffectLibrary.liquid_dream_warp(3.0),
        EffectLibrary.kaleidoscope_trip(4.0),
        EffectLibrary.portal_dimensional_rift(2.5),
        EffectLibrary.color_shift_rainbow(3.0)
    ],
    
    "glass_shatter_impact": [
        EffectLibrary.shatter_glass_break(0.8),
        EffectLibrary.camera_shake_intense(0.5),
        EffectLibrary.energy_explosion(1.0),
        EffectLibrary.brightness_strobe(0.3)
    ],
    
    "liquid_metal_dream": [
        EffectLibrary.liquid_dream_warp(2.5),
        EffectLibrary.neon_cyberpunk_glow(2.0),
        EffectLibrary.elastic_entrance(1.0),
        EffectLibrary.motion_blur_fast(0.5)
    ],
    
    "portal_dimension_shift": [
        EffectLibrary.portal_dimensional_rift(2.0),
        EffectLibrary.energy_explosion(1.2),
        EffectLibrary.hologram_sci_fi(1.5),
        EffectLibrary.digital_glitch_intense(0.4)
    ]
}


# Main effect library registry
EFFECT_LIBRARY = {
    # Traditional effects
    "cinematic_zoom_in": EffectLibrary.cinematic_zoom_in,
    "dramatic_zoom_out": EffectLibrary.dramatic_zoom_out,
    "sliding_text_left": EffectLibrary.sliding_text_left,
    "sliding_text_right": EffectLibrary.sliding_text_right,
    "bouncy_entrance": EffectLibrary.bouncy_entrance,
    "elastic_entrance": EffectLibrary.elastic_entrance,
    "smooth_fade_in": EffectLibrary.smooth_fade_in,
    "dramatic_fade_out": EffectLibrary.dramatic_fade_out,
    "pulse_beat_sync": EffectLibrary.pulse_beat_sync,
    "camera_shake_intense": EffectLibrary.camera_shake_intense,
    "rotate_spin_in": EffectLibrary.rotate_spin_in,
    "wave_distortion": EffectLibrary.wave_distortion,
    "motion_blur_fast": EffectLibrary.motion_blur_fast,
    "color_shift_rainbow": EffectLibrary.color_shift_rainbow,
    "brightness_strobe": EffectLibrary.brightness_strobe,
    "pan_follow_motion": EffectLibrary.pan_follow_motion,
    
    # BOLD NEW EFFECTS
    "digital_glitch_intense": EffectLibrary.digital_glitch_intense,
    "neon_cyberpunk_glow": EffectLibrary.neon_cyberpunk_glow,
    "energy_explosion": EffectLibrary.energy_explosion,
    "liquid_dream_warp": EffectLibrary.liquid_dream_warp,
    "portal_dimensional_rift": EffectLibrary.portal_dimensional_rift,
    "hologram_sci_fi": EffectLibrary.hologram_sci_fi,
    "shatter_glass_break": EffectLibrary.shatter_glass_break,
    "kaleidoscope_trip": EffectLibrary.kaleidoscope_trip,
}


def get_effect_by_name(name: str, duration: float = 1.0) -> MotionEffect:
    """Get effect by name from library."""
    if name in EFFECT_LIBRARY:
        return EFFECT_LIBRARY[name](duration)
    else:
        # Default to smooth fade in
        return EffectLibrary.smooth_fade_in(duration)


def get_effect_combination(name: str) -> List[MotionEffect]:
    """Get pre-built effect combination."""
    return EFFECT_COMBINATIONS.get(name, [EffectLibrary.smooth_fade_in(1.0)])