"""Core wallpaper generation logic."""

from typing import Tuple, Optional, Callable, List
from PIL import Image, ImageDraw, ImageFont
import os

try:
    from .quote_parser import Quote
    from .utils import ColorScheme, get_font_size_for_resolution, sanitize_filename
except ImportError:
    from src.quote_parser import Quote
    from src.utils import ColorScheme, get_font_size_for_resolution, sanitize_filename


class WallpaperGenerator:
    """Generates wallpapers from quotes."""

    def __init__(
        self,
        width: int = 3840,
        height: int = 2160,
        color_scheme: Optional[ColorScheme] = None,
        text_position: str = "center"
    ):
        """
        Initialize wallpaper generator.
        
        Args:
            width: Image width in pixels (default: 3840 for 4K)
            height: Image height in pixels (default: 2160 for 4K)
            color_scheme: Color scheme to use (default: first scheme)
            text_position: Text position - "center", "bottom-left", "bottom-right", "top-left", "top-right"
        """
        self.width = width
        self.height = height
        self.text_position = text_position
        
        from .utils import COLOR_SCHEMES
        self.color_scheme = color_scheme or COLOR_SCHEMES[0]
        
        # Try to load a nice font, fallback to default
        self.quote_font = self._load_font("quote", width, height)
        self.author_font = self._load_font("author", width, height)
        self.source_font = self._load_font("source", width, height)

    def _load_font(self, font_type: str, width: int, height: int) -> ImageFont.FreeTypeFont:
        """Load appropriate font for text type."""
        # Base font sizes
        if font_type == "quote":
            size = get_font_size_for_resolution(width, height, base_size=120)
        elif font_type == "author":
            size = get_font_size_for_resolution(width, height, base_size=60)
        else:  # source
            size = get_font_size_for_resolution(width, height, base_size=40)
        
        # Try to use system fonts, fallback to default
        try:
            # Try common system fonts
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
                "C:/Windows/Fonts/arial.ttf",
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, size)
        except Exception:
            pass
        
        # Fallback to default font
        return ImageFont.load_default()

    def _wrap_text(
        self,
        text: str,
        font: ImageFont.FreeTypeFont,
        max_width: int,
        max_lines: int = 10
    ) -> List[str]:
        """Wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Word is too long, add it anyway
                    lines.append(word)
                    current_line = []
                
                if len(lines) >= max_lines:
                    break
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines

    def _draw_text(
        self,
        draw: ImageDraw.Draw,
        text: str,
        font: ImageFont.FreeTypeFont,
        position: Tuple[int, int],
        color: Tuple[int, int, int],
        max_width: Optional[int] = None,
        align: str = "center"
    ):
        """Draw text on image with optional wrapping."""
        if max_width:
            lines = self._wrap_text(text, font, max_width)
            y_offset = position[1]
            line_height = int(font.size * 1.3)
            
            for line in lines:
                bbox = font.getbbox(line)
                text_width = bbox[2] - bbox[0]
                
                if align == "center":
                    x = position[0] - text_width // 2
                elif align == "right":
                    x = position[0] - text_width
                else:
                    x = position[0]
                
                draw.text((x, y_offset), line, fill=color, font=font)
                y_offset += line_height
        else:
            draw.text(position, text, fill=color, font=font)

    def create_base_image(self) -> Image.Image:
        """Create base image with background color."""
        img = Image.new('RGB', (self.width, self.height), self.color_scheme.background)
        return img

    def add_quote_text(
        self,
        img: Image.Image,
        quote: Quote,
        style_callback: Optional[Callable[[Image.Image, ImageDraw.Draw], None]] = None
    ) -> Image.Image:
        """
        Add quote text to image.
        
        Args:
            img: Base image
            quote: Quote object
            style_callback: Optional function to add style elements before text
        """
        draw = ImageDraw.Draw(img)
        
        # Apply style elements if provided
        if style_callback:
            style_callback(img, draw)
        
        # Calculate text area (leave margins)
        margin_x = self.width // 8
        margin_y = self.height // 6
        text_area_width = self.width - (2 * margin_x)
        
        # Wrap quote text once
        quote_lines = self._wrap_text(quote.text, self.quote_font, text_area_width)
        quote_height = len(quote_lines) * int(self.quote_font.size * 1.3)
        author_height = int(self.author_font.size * 1.3)
        source_height = int(self.source_font.size * 1.3) if quote.source else 0
        spacing = 20
        total_height = quote_height + author_height + source_height + spacing * 2
        
        # Determine position based on text_position setting
        if self.text_position == "bottom-left":
            start_x = margin_x
            start_y = self.height - margin_y
            align = "left"
            quote_y = start_y - total_height
        elif self.text_position == "bottom-right":
            start_x = self.width - margin_x
            start_y = self.height - margin_y
            align = "right"
            quote_y = start_y - total_height
        elif self.text_position == "top-left":
            start_x = margin_x
            start_y = margin_y
            align = "left"
            quote_y = start_y
        elif self.text_position == "top-right":
            start_x = self.width - margin_x
            start_y = margin_y
            align = "right"
            quote_y = start_y
        else:  # center (default)
            start_x = self.width // 2
            start_y = self.height // 2
            align = "center"
            quote_y = start_y - quote_height // 2 - 80
        
        # Draw quote text
        for line in quote_lines:
            bbox = self.quote_font.getbbox(line)
            text_width = bbox[2] - bbox[0]
            
            if align == "center":
                x = start_x - text_width // 2
            elif align == "right":
                x = start_x - text_width
            else:  # left
                x = start_x
            
            draw.text((x, quote_y), line, fill=self.color_scheme.text, font=self.quote_font)
            quote_y += int(self.quote_font.size * 1.3)
        
        # Draw author (below quote)
        author_text = f"— {quote.author}"
        bbox = self.author_font.getbbox(author_text)
        author_width = bbox[2] - bbox[0]
        
        if align == "center":
            author_x = start_x - author_width // 2
        elif align == "right":
            author_x = start_x - author_width
        else:  # left
            author_x = start_x
        
        author_y = quote_y + spacing
        draw.text(
            (author_x, author_y),
            author_text,
            fill=self.color_scheme.accent,
            font=self.author_font
        )
        
        # Draw source if available (below author)
        if quote.source:
            source_y = author_y + int(self.author_font.size * 1.5)
            source_text = quote.source
            bbox = self.source_font.getbbox(source_text)
            source_width = bbox[2] - bbox[0]
            
            if align == "center":
                source_x = start_x - source_width // 2
            elif align == "right":
                source_x = start_x - source_width
            else:  # left
                source_x = start_x
            
            draw.text(
                (source_x, source_y),
                source_text,
                fill=self.color_scheme.secondary,
                font=self.source_font
            )
        
        return img

    def generate(
        self,
        quote: Quote,
        style_callback: Optional[Callable[[Image.Image, ImageDraw.Draw], None]] = None
    ) -> Image.Image:
        """
        Generate complete wallpaper.
        
        Args:
            quote: Quote object
            style_callback: Optional function to add style elements
        
        Returns:
            PIL Image object
        """
        img = self.create_base_image()
        img = self.add_quote_text(img, quote, style_callback)
        return img

    def save(
        self,
        img: Image.Image,
        quote: Quote,
        output_path: str,
        number: int = 1
    ):
        """Save wallpaper to file with naming: author_number.png"""
        author_name = sanitize_filename(quote.author)
        filename = f"{author_name}_{number}.png"
        filepath = os.path.join(output_path, filename)
        img.save(filepath, 'PNG', quality=95)
        return filepath

