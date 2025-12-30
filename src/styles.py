"""Style variations for wallpapers."""

import random
import math
from typing import Callable, Tuple, List, Optional
from PIL import Image, ImageDraw

try:
    from .utils import ColorScheme, COLOR_SCHEMES
except ImportError:
    from src.utils import ColorScheme, COLOR_SCHEMES


def style_dots_scattered(img: Image.Image, draw: ImageDraw.Draw) -> None:
    """Scattered dots pattern."""
    width, height = img.size
    color_scheme = COLOR_SCHEMES[0]
    
    num_dots = random.randint(50, 150)
    dot_size = random.randint(2, 8)
    
    for _ in range(num_dots):
        x = random.randint(0, width)
        y = random.randint(0, height)
        # Use accent color with varying opacity
        opacity = random.randint(30, 100)
        color = (*color_scheme.accent[:3], opacity) if len(color_scheme.accent) == 3 else color_scheme.accent
        
        # Draw circle
        bbox = [x - dot_size, y - dot_size, x + dot_size, y + dot_size]
        draw.ellipse(bbox, fill=color_scheme.accent)


def style_dots_grid(img: Image.Image, draw: ImageDraw.Draw) -> None:
    """Grid of dots pattern."""
    width, height = img.size
    color_scheme = COLOR_SCHEMES[0]
    
    spacing = random.randint(80, 150)
    dot_size = random.randint(3, 6)
    
    for x in range(spacing, width, spacing):
        for y in range(spacing, height, spacing):
            # Randomly skip some dots
            if random.random() > 0.3:
                bbox = [x - dot_size, y - dot_size, x + dot_size, y + dot_size]
                draw.ellipse(bbox, fill=color_scheme.accent)


def style_lines_geometric(img: Image.Image, draw: ImageDraw.Draw) -> None:
    """Geometric lines pattern."""
    width, height = img.size
    color_scheme = COLOR_SCHEMES[1]
    
    num_lines = random.randint(5, 15)
    line_width = random.randint(1, 3)
    
    for _ in range(num_lines):
        # Random line from edge to edge
        if random.random() > 0.5:
            # Horizontal
            y = random.randint(0, height)
            draw.line([(0, y), (width, y)], fill=color_scheme.accent, width=line_width)
        else:
            # Vertical
            x = random.randint(0, width)
            draw.line([(x, 0), (x, height)], fill=color_scheme.accent, width=line_width)


def style_lines_diagonal(img: Image.Image, draw: ImageDraw.Draw) -> None:
    """Diagonal lines pattern."""
    width, height = img.size
    color_scheme = COLOR_SCHEMES[1]
    
    num_lines = random.randint(8, 20)
    line_width = random.randint(1, 2)
    angle = random.uniform(-45, 45)
    
    center_x, center_y = width // 2, height // 2
    length = math.sqrt(width**2 + height**2)
    
    for _ in range(num_lines):
        offset = random.randint(-int(length//2), int(length//2))
        x1 = center_x + offset * math.cos(math.radians(angle))
        y1 = center_y + offset * math.sin(math.radians(angle))
        x2 = x1 + length * math.cos(math.radians(angle + 90))
        y2 = y1 + length * math.sin(math.radians(angle + 90))
        
        draw.line([(x1, y1), (x2, y2)], fill=color_scheme.accent, width=line_width)


def style_gradient_radial(img: Image.Image, draw: ImageDraw.Draw) -> None:
    """Radial gradient background."""
    width, height = img.size
    color_scheme = COLOR_SCHEMES[2]
    
    # Convert to RGBA for alpha blending
    if img.mode != 'RGBA':
        img_rgba = img.convert('RGBA')
    else:
        img_rgba = img
    
    # Create gradient overlay
    center_x = random.randint(width // 4, 3 * width // 4)
    center_y = random.randint(height // 4, 3 * height // 4)
    max_radius = int(math.sqrt(width**2 + height**2))
    
    # Draw concentric circles with decreasing opacity
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    for radius in range(max_radius, 0, -max_radius // 20):
        opacity = int(255 * (1 - radius / max_radius) * 0.3)
        if opacity > 0:
            color = (*color_scheme.accent[:3], min(opacity, 255))
            bbox = [center_x - radius, center_y - radius, center_x + radius, center_y + radius]
            overlay_draw.ellipse(bbox, fill=color)
    
    # Blend overlay with base image
    blended = Image.alpha_composite(img_rgba, overlay)
    # Convert back to RGB and update original image
    rgb_data = blended.convert('RGB')
    img.paste(rgb_data)


def style_gradient_linear(img: Image.Image, draw: ImageDraw.Draw) -> None:
    """Linear gradient overlay."""
    width, height = img.size
    color_scheme = COLOR_SCHEMES[2]
    
    # Convert to RGBA for alpha blending
    if img.mode != 'RGBA':
        img_rgba = img.convert('RGBA')
    else:
        img_rgba = img
    
    # Create gradient from one corner
    direction = random.choice(['top-left', 'top-right', 'bottom-left', 'bottom-right'])
    
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    steps = 50
    for i in range(steps):
        opacity = int(255 * (i / steps) * 0.2)
        if opacity > 0:
            if direction == 'top-left':
                x = int(width * i / steps)
                y = int(height * i / steps)
                overlay_draw.ellipse([x-100, y-100, x+100, y+100], fill=(*color_scheme.accent[:3], opacity))
            elif direction == 'top-right':
                x = int(width * (1 - i / steps))
                y = int(height * i / steps)
                overlay_draw.ellipse([x-100, y-100, x+100, y+100], fill=(*color_scheme.accent[:3], opacity))
            elif direction == 'bottom-left':
                x = int(width * i / steps)
                y = int(height * (1 - i / steps))
                overlay_draw.ellipse([x-100, y-100, x+100, y+100], fill=(*color_scheme.accent[:3], opacity))
            else:  # bottom-right
                x = int(width * (1 - i / steps))
                y = int(height * (1 - i / steps))
                overlay_draw.ellipse([x-100, y-100, x+100, y+100], fill=(*color_scheme.accent[:3], opacity))
    
    # Blend overlay with base image
    blended = Image.alpha_composite(img_rgba, overlay)
    # Convert back to RGB and update original image
    rgb_data = blended.convert('RGB')
    img.paste(rgb_data)


def style_shapes_circles(img: Image.Image, draw: ImageDraw.Draw) -> None:
    """Simple circle shapes."""
    width, height = img.size
    color_scheme = COLOR_SCHEMES[3]
    
    num_shapes = random.randint(3, 8)
    
    for _ in range(num_shapes):
        x = random.randint(0, width)
        y = random.randint(0, height)
        radius = random.randint(50, 200)
        
        # Draw outline only
        bbox = [x - radius, y - radius, x + radius, y + radius]
        draw.ellipse(bbox, outline=color_scheme.accent, width=random.randint(2, 5))


def style_shapes_geometric(img: Image.Image, draw: ImageDraw.Draw) -> None:
    """Geometric shapes (circles, squares, triangles)."""
    width, height = img.size
    color_scheme = COLOR_SCHEMES[3]
    
    num_shapes = random.randint(4, 10)
    shapes = ['circle', 'square', 'triangle']
    
    for _ in range(num_shapes):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(40, 150)
        shape_type = random.choice(shapes)
        
        if shape_type == 'circle':
            bbox = [x - size, y - size, x + size, y + size]
            draw.ellipse(bbox, outline=color_scheme.accent, width=random.randint(2, 4))
        elif shape_type == 'square':
            bbox = [x - size, y - size, x + size, y + size]
            draw.rectangle(bbox, outline=color_scheme.accent, width=random.randint(2, 4))
        else:  # triangle
            points = [
                (x, y - size),
                (x - size, y + size),
                (x + size, y + size)
            ]
            draw.polygon(points, outline=color_scheme.accent, width=random.randint(2, 4))


def style_patterns_minimal(img: Image.Image, draw: ImageDraw.Draw) -> None:
    """Minimal repeating pattern."""
    width, height = img.size
    color_scheme = COLOR_SCHEMES[4]
    
    pattern_size = random.randint(100, 200)
    element_size = random.randint(3, 8)
    
    for x in range(0, width, pattern_size):
        for y in range(0, height, pattern_size):
            if random.random() > 0.7:  # Sparse pattern
                offset_x = random.randint(-20, 20)
                offset_y = random.randint(-20, 20)
                bbox = [x + offset_x - element_size, y + offset_y - element_size,
                       x + offset_x + element_size, y + offset_y + element_size]
                draw.ellipse(bbox, fill=color_scheme.accent)


def style_patterns_wave(img: Image.Image, draw: ImageDraw.Draw) -> None:
    """Wave-like pattern."""
    width, height = img.size
    color_scheme = COLOR_SCHEMES[4]
    
    num_waves = random.randint(2, 5)
    wave_amplitude = random.randint(20, 80)
    wave_frequency = random.uniform(0.01, 0.05)
    
    for wave_num in range(num_waves):
        y_base = height // (num_waves + 1) * (wave_num + 1)
        points = []
        
        for x in range(0, width, 5):
            y = y_base + wave_amplitude * math.sin(x * wave_frequency + wave_num * math.pi / 2)
            points.append((x, int(y)))
        
        if len(points) > 1:
            draw.line(points, fill=color_scheme.accent, width=random.randint(1, 3))


# Style registry
STYLE_VARIATIONS: List[Tuple[str, str, Callable]] = [
    # (category, name, function)
    ('dots', 'scattered', style_dots_scattered),
    ('dots', 'grid', style_dots_grid),
    ('lines', 'geometric', style_lines_geometric),
    ('lines', 'diagonal', style_lines_diagonal),
    ('gradients', 'radial', style_gradient_radial),
    ('gradients', 'linear', style_gradient_linear),
    ('shapes', 'circles', style_shapes_circles),
    ('shapes', 'geometric', style_shapes_geometric),
    ('patterns', 'minimal', style_patterns_minimal),
    ('patterns', 'wave', style_patterns_wave),
]


def get_all_styles() -> List[Tuple[str, str, Callable]]:
    """Get all available style variations."""
    return STYLE_VARIATIONS


def get_styles_by_category(category: str) -> List[Tuple[str, str, Callable]]:
    """Get styles filtered by category."""
    return [s for s in STYLE_VARIATIONS if s[0] == category]


def get_style_function(category: str, name: str) -> Optional[Callable]:
    """Get style function by category and name."""
    for cat, n, func in STYLE_VARIATIONS:
        if cat == category and n == name:
            return func
    return None

