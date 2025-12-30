"""CLI entry point for quote wallpaper generator."""

import argparse
import os
import sys
from typing import Optional
from collections import defaultdict

# Handle both module and script execution
if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.quote_parser import Quote, QuoteParser
from src.wallpaper_generator import WallpaperGenerator
from src.styles import get_style_function
from src.utils import get_dark_color_schemes


def parse_resolution(resolution_str: str) -> tuple[int, int]:
    """Parse resolution string like '3840x2160' or '1920x1080'."""
    try:
        width, height = map(int, resolution_str.lower().split('x'))
        return width, height
    except ValueError:
        raise ValueError(f"Invalid resolution format: {resolution_str}. Use format like '3840x2160'")


def generate_wallpaper(
    quote: Quote,
    output_dir: str,
    width: int,
    height: int,
    number: int = 1
) -> str:
    """Generate wallpaper using final style (dark theme, patterns_minimal, bottom-left)."""
    dark_schemes = get_dark_color_schemes()
    color_scheme = dark_schemes[0]  # First dark color scheme
    
    style_func = get_style_function('patterns', 'minimal')
    if not style_func:
        print(f"Error: patterns_minimal style not found")
        return None
    
    os.makedirs(output_dir, exist_ok=True)
    
    generator = WallpaperGenerator(
        width=width,
        height=height,
        color_scheme=color_scheme,
        text_position="bottom-left"
    )
    
    img = generator.generate(quote, style_func)
    filepath = generator.save(img, quote, output_dir, number)
    
    print(f"Generated: {os.path.basename(filepath)}")
    return filepath


def process_file(
    input_file: str,
    output_dir: str,
    width: int,
    height: int
):
    """Process quotes from a file, numbering by author."""
    parser = QuoteParser()
    quotes = parser.parse_file(input_file)
    
    if not quotes:
        print(f"Error: No quotes found in {input_file}")
        return
    
    print(f"Processing {len(quotes)} quote(s)...")
    
    # Count quotes per author for numbering
    author_counts = defaultdict(int)
    
    for quote in quotes:
        author_counts[quote.author] += 1
    
    # Reset counters for actual generation
    author_numbers = defaultdict(int)
    
    for quote in quotes:
        author_numbers[quote.author] += 1
        number = author_numbers[quote.author]
        
        print(f"\nProcessing: {quote.text[:50]}... — {quote.author} ({number})")
        generate_wallpaper(quote, output_dir, width, height, number)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Generate minimalistic quote wallpapers'
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--quote',
        type=str,
        help='Quote text'
    )
    input_group.add_argument(
        '--input',
        type=str,
        help='Input CSV or JSON file'
    )
    
    parser.add_argument(
        '--author',
        type=str,
        help='Author name (required with --quote)'
    )
    parser.add_argument(
        '--source',
        type=str,
        help='Source/media/occupation/role (optional)'
    )
    parser.add_argument(
        '--number',
        type=int,
        default=1,
        help='Wallpaper number for this author (default: 1)'
    )
    
    # Output options
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output',
        help='Output directory (default: output)'
    )
    parser.add_argument(
        '--resolution',
        type=str,
        default='3840x2160',
        help='Resolution in format WIDTHxHEIGHT (default: 3840x2160)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.quote and not args.author:
        parser.error("--author is required when using --quote")
    
    # Parse resolution
    try:
        width, height = parse_resolution(args.resolution)
    except ValueError as e:
        parser.error(str(e))
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Process based on input type
    if args.quote:
        quote = Quote(text=args.quote, author=args.author, source=args.source)
        generate_wallpaper(quote, args.output_dir, width, height, args.number)
    elif args.input:
        if not os.path.exists(args.input):
            print(f"Error: Input file not found: {args.input}")
            sys.exit(1)
        
        process_file(args.input, args.output_dir, width, height)
    
    print(f"\nDone! Wallpapers saved to {args.output_dir}")


if __name__ == '__main__':
    main()
