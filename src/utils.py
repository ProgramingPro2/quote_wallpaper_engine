"""Utility functions for color schemes, typography, and file handling."""

from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class ColorScheme:
    """Color scheme for wallpapers."""
    background: Tuple[int, int, int]
    text: Tuple[int, int, int]
    accent: Tuple[int, int, int]
    secondary: Tuple[int, int, int] = None

    def __post_init__(self):
        if self.secondary is None:
            self.secondary = self.accent


# Predefined color schemes
COLOR_SCHEMES: List[ColorScheme] = [
    # Dark schemes
    ColorScheme(
        background=(18, 18, 18),
        text=(255, 255, 255),
        accent=(200, 200, 200),
        secondary=(150, 150, 150)
    ),
    ColorScheme(
        background=(30, 30, 40),
        text=(240, 240, 240),
        accent=(180, 180, 200),
        secondary=(120, 120, 140)
    ),
    ColorScheme(
        background=(25, 25, 35),
        text=(255, 255, 255),
        accent=(100, 150, 200),
        secondary=(70, 100, 150)
    ),
    # Light schemes
    ColorScheme(
        background=(250, 250, 250),
        text=(20, 20, 20),
        accent=(60, 60, 60),
        secondary=(100, 100, 100)
    ),
    ColorScheme(
        background=(245, 245, 248),
        text=(30, 30, 30),
        accent=(80, 80, 100),
        secondary=(120, 120, 140)
    ),
    # Warm schemes
    ColorScheme(
        background=(40, 30, 25),
        text=(255, 245, 235),
        accent=(220, 180, 140),
        secondary=(180, 140, 100)
    ),
    # Cool schemes
    ColorScheme(
        background=(20, 30, 40),
        text=(230, 240, 250),
        accent=(120, 180, 220),
        secondary=(80, 140, 180)
    ),
]


def sanitize_filename(text: str, max_length: int = 100) -> str:
    """Sanitize text for use in filenames."""
    import re
    # Remove or replace invalid characters
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    text = re.sub(r'\s+', '_', text)
    text = text.strip('._')
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]
    return text or "quote"


def get_font_size_for_resolution(width: int, height: int, base_size: int = 72) -> int:
    """Calculate appropriate font size based on resolution."""
    # Scale font size based on 4K (3840x2160) as baseline
    scale_factor = min(width / 3840, height / 2160)
    return int(base_size * scale_factor)


def get_dark_color_schemes() -> List[ColorScheme]:
    """Get only dark color schemes."""
    return [
        COLOR_SCHEMES[0],  # Dark gray
        COLOR_SCHEMES[1],  # Dark blue-gray
        COLOR_SCHEMES[2],  # Dark with blue accent
        COLOR_SCHEMES[5],  # Warm dark
        COLOR_SCHEMES[6],  # Cool dark
    ]

