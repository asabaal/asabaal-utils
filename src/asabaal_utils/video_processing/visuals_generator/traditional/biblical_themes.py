from typing import Dict, List, Tuple
import random


BIBLICAL_THEMES = {
    "divine_calling": {
        "keywords": ["called", "chosen", "appointed", "commissioned", "anointed"],
        "visual_elements": ["divine light", "heavenly glow", "sacred illumination", "golden rays"],
        "atmosphere": ["reverent", "majestic", "awe-inspiring", "holy"]
    },
    "craftsmanship": {
        "keywords": ["skill", "work", "craft", "build", "create", "artisan", "hands"],
        "visual_elements": ["skilled hands", "intricate detail", "masterful technique", "ancient tools"],
        "atmosphere": ["focused", "dedicated", "precise", "industrious"]
    },
    "community": {
        "keywords": ["together", "united", "congregation", "assembly", "people", "gathered"],
        "visual_elements": ["unified movement", "coordinated effort", "shared purpose", "collective harmony"],
        "atmosphere": ["collaborative", "harmonious", "synchronized", "communal"]
    },
    "worship": {
        "keywords": ["worship", "praise", "offering", "sacrifice", "prayer", "holy"],
        "visual_elements": ["raised hands", "bowed heads", "sacred smoke", "altar flames"],
        "atmosphere": ["reverent", "devotional", "spiritual", "transcendent"]
    },
    "divine_presence": {
        "keywords": ["glory", "presence", "dwelling", "tabernacle", "sanctuary", "holy"],
        "visual_elements": ["divine cloud", "sacred fire", "glowing presence", "ethereal light"],
        "atmosphere": ["supernatural", "otherworldly", "magnificent", "overwhelming"]
    },
    "generosity": {
        "keywords": ["bring", "offer", "give", "willing", "heart", "gift", "abundance"],
        "visual_elements": ["overflowing gifts", "joyful giving", "abundant offerings", "treasures presented"],
        "atmosphere": ["generous", "joyful", "abundant", "selfless"]
    },
    "wisdom": {
        "keywords": ["wisdom", "understanding", "knowledge", "insight", "teach", "instruction"],
        "visual_elements": ["thoughtful contemplation", "divine inspiration", "enlightened understanding", "sage guidance"],
        "atmosphere": ["contemplative", "enlightened", "insightful", "profound"]
    }
}


VISUAL_STYLE_ELEMENTS = {
    "lighting": [
        "golden hour desert light",
        "divine rays breaking through clouds",
        "warm candlelight glow",
        "ethereal heavenly illumination",
        "dramatic chiaroscuro lighting"
    ],
    "camera": [
        "epic wide establishing shot",
        "intimate close-up detail",
        "slow dolly movement",
        "majestic crane shot",
        "reverent low angle"
    ],
    "color_palette": [
        "rich earth tones with gold accents",
        "deep blues and purples with silver",
        "warm desert hues",
        "sacred crimson and white",
        "bronze and copper metallic tones"
    ],
    "texture": [
        "rough-hewn stone and wood",
        "fine linen and silk fabrics",
        "polished bronze and gold",
        "weathered leather and parchment",
        "desert sand and ancient stone"
    ]
}


ANIMATION_STYLES = {
    "subtle": [
        "gentle swaying movement",
        "soft breathing rhythm",
        "delicate fabric flutter",
        "slow turning reveal",
        "gradual light shift"
    ],
    "dynamic": [
        "rhythmic hammering motion",
        "coordinated workflow",
        "sweeping camera movement",
        "dynamic tool handling",
        "energetic collaboration"
    ],
    "spiritual": [
        "ascending particles of light",
        "ethereal smoke rising",
        "divine presence manifestation",
        "heavenly light pulsing",
        "sacred energy flowing"
    ]
}


def identify_themes(text: str) -> List[str]:
    """Identify biblical themes in the text."""
    text_lower = text.lower()
    identified_themes = []
    
    for theme, details in BIBLICAL_THEMES.items():
        for keyword in details["keywords"]:
            if keyword in text_lower:
                identified_themes.append(theme)
                break
    
    return list(set(identified_themes)) if identified_themes else ["craftsmanship"]  # Default


def get_visual_elements(themes: List[str]) -> Dict[str, List[str]]:
    """Get visual elements for identified themes."""
    visual_elements = {
        "primary_elements": [],
        "atmosphere": [],
        "style_descriptors": []
    }
    
    for theme in themes:
        if theme in BIBLICAL_THEMES:
            visual_elements["primary_elements"].extend(BIBLICAL_THEMES[theme]["visual_elements"])
            visual_elements["atmosphere"].extend(BIBLICAL_THEMES[theme]["atmosphere"])
    
    # Add style elements
    visual_elements["style_descriptors"] = [
        random.choice(VISUAL_STYLE_ELEMENTS["lighting"]),
        random.choice(VISUAL_STYLE_ELEMENTS["camera"]),
        random.choice(VISUAL_STYLE_ELEMENTS["color_palette"])
    ]
    
    return visual_elements


def get_animation_style(themes: List[str], duration: float) -> str:
    """Determine appropriate animation style based on themes and duration."""
    if "divine_presence" in themes or "worship" in themes:
        style_type = "spiritual"
    elif "craftsmanship" in themes or "community" in themes:
        style_type = "dynamic"
    else:
        style_type = "subtle"
    
    return random.choice(ANIMATION_STYLES[style_type])


def enhance_prompt_with_biblical_style(base_prompt: str) -> str:
    """Enhance a prompt with biblical visual style markers."""
    style_markers = [
        "biblical epic cinematography",
        "ancient Hebrew aesthetic",
        "sacred artistic tradition",
        "divinely inspired imagery",
        "Old Testament visual narrative"
    ]
    
    technical_specs = [
        "photorealistic detail",
        "cinematic composition",
        "8K resolution",
        "volumetric lighting",
        "--ar 16:9 --style raw"
    ]
    
    enhanced = f"{base_prompt}, {random.choice(style_markers)}, "
    enhanced += ", ".join(random.sample(technical_specs, 3))
    
    return enhanced