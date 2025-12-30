# Quote Wallpaper Generator

A Python application that generates minimalistic 4K wallpapers from quotes with a dark theme and sparse dot pattern background.

## Features

- Generate high-resolution wallpapers (4K default, customizable)
- Minimalistic design with dark theme
- Bottom-left text positioning
- Batch processing from CSV/JSON files
- Auto-detection of quote, author, and source/occupation/role fields
- Automatic numbering by author (e.g., `Steve_Jobs_1.png`, `Steve_Jobs_2.png`)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd quote_wallpaper_engine
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Process CSV/JSON file
```bash
python src/main.py --input quotes.csv --output-dir output/
```

### Generate at specific resolution
```bash
python src/main.py --input quotes.json --resolution 1920x1080
```

### Single quote
```bash
python src/main.py --quote "Your quote here" --author "Author Name" --source "Source/Occupation" --number 1
```

## Input Format

### CSV Format
```csv
quote,author,source
"Your quote here","Author Name","Media/Book Title"
"Another quote","Person Name","Occupation/Role"
```

### JSON Format
```json
[
  {
    "quote": "Your quote here",
    "author": "Author Name",
    "source": "Media/Book Title"
  }
]
```

The parser auto-detects field names:
- **Quote**: `quote`, `text`, `quotation`, `q`
- **Author**: `author`, `person`, `speaker`, `who`, `by`
- **Source**: `source`, `media`, `from`, `work`, `book`, `movie`, `show`, `occupation`, `role`, `title`, `position`

The source field can contain media titles, book names, or person's occupation/role in history.

## Output

Wallpapers are saved with the naming convention: `[Author]_[Number].png`

For example:
- `Steve_Jobs_1.png`
- `Steve_Jobs_2.png`
- `Albert_Einstein_1.png`

All wallpapers use:
- Dark theme background
- Minimal dot pattern
- Bottom-left text positioning
- High-quality PNG format

## Project Structure

```
quote_wallpaper_engine/
├── src/
│   ├── main.py              # CLI entry point
│   ├── quote_parser.py      # CSV/JSON parsing
│   ├── wallpaper_generator.py  # Core generation logic
│   ├── styles.py            # Style variations
│   └── utils.py             # Utilities (colors, fonts)
├── output/                  # Generated wallpapers
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Example

See `example_quotes.csv` for a sample input file format.

## License

See LICENSE file for details.
