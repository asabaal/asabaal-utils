"""Text rendering and animation module."""

from .renderer import TextRenderer, TextStyle, AnimationConfig
from .animations import TextAnimation, AnimationType, AnimationEasing
from .fonts import FontManager
from .professional_renderer import (
    ProfessionalTextRenderer, ProfessionalTextStyle,
    KineticTypography, PrecisionSyncSystem, TextPath,
    AdvancedTextLayout, Transform3D, Timeline,
    create_professional_config
)

__all__ = [
    "TextRenderer", "TextStyle", "AnimationConfig", 
    "TextAnimation", "AnimationType", "AnimationEasing", 
    "FontManager",
    "ProfessionalTextRenderer", "ProfessionalTextStyle",
    "KineticTypography", "PrecisionSyncSystem", "TextPath",
    "AdvancedTextLayout", "Transform3D", "Timeline",
    "create_professional_config"
]