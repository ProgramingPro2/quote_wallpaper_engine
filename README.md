# Quote Wallpaper Generator

A Python application that generates minimalistic 4K wallpapers from quotes with a dark theme and sparse dot pattern background.

## Features

- Generate high-resolution wallpapers (4K default, customizable)
- Minimalistic design with dark theme
- Bottom-left text positioning
- Batch processing from CSV/JSON files
- Auto-detection of quote, author, and source/occupation/role fields
- Automatic numbering by author (e.g., `Steve_Jobs_1.png`, `Steve_Jobs_2.png`)
- **Wallpaper Cycler**: Automatically cycle through generated wallpapers with configurable intervals
- **GUI Configuration**: Easy-to-use interface for managing wallpaper cycling settings
- **Autostart Support**: Configure to start automatically on system login

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

4. Install system dependencies (for GUI):
```bash
sudo apt-get install python3-tk
```
Note: `python3-tk` is required for the wallpaper cycler GUI and must be installed via the system package manager.

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

## Wallpaper Cycler

The wallpaper cycler automatically changes your desktop wallpaper from the generated wallpapers at configurable intervals.

### GUI Configuration

Launch the GUI to configure and control the wallpaper cycler:

```bash
python src/wallpaper_cycler_gui.py
```

**Features:**
- Configure cycle interval (1-1440 minutes)
- Toggle random or sequential wallpaper selection
- Start/Stop the daemon
- View logs
- Enable/disable autostart on login
- Browse and select wallpaper directory

### Command Line Usage

Run the cycler daemon directly:

```bash
python src/wallpaper_cycler.py
```

**Test wallpaper setting:**
```bash
python src/wallpaper_cycler.py --test
```

### Configuration

Configuration is stored in `~/.config/quote_wallpaper_cycler/config.json`:

```json
{
  "cycle_interval_minutes": 30,
  "random_mode": true,
  "wallpaper_directory": "/path/to/output",
  "desktop_environment": "auto"
}
```

### Desktop Environment Support

The cycler supports multiple desktop environments:
- **GNOME (Wayland/X11)**: Sets wallpaper for both light and dark themes
- **KDE (Wayland)**: Uses Plasma wallpaper management
- **Sway**: Uses swaybg

The script auto-detects your desktop environment, or you can set it manually in the config.

### Logs

View logs at: `~/.local/share/quote_wallpaper_cycler/cycler.log`

**Command line:**
```bash
# View entire log
cat ~/.local/share/quote_wallpaper_cycler/cycler.log

# View last 50 lines
tail -n 50 ~/.local/share/quote_wallpaper_cycler/cycler.log

# Follow log in real-time
tail -f ~/.local/share/quote_wallpaper_cycler/cycler.log
```

**GUI:** Click the "View Logs" button in the configuration window.

### Autostart

Enable autostart from the GUI using the "Enable Autostart" button. This creates a desktop entry at `~/.config/autostart/quote-wallpaper-cycler.desktop` that launches the cycler on login.

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
│   ├── main.py                  # CLI entry point for wallpaper generation
│   ├── quote_parser.py          # CSV/JSON parsing
│   ├── wallpaper_generator.py  # Core generation logic
│   ├── styles.py                # Style variations
│   ├── utils.py                 # Utilities (colors, fonts)
│   ├── wallpaper_cycler.py      # Wallpaper cycling daemon
│   └── wallpaper_cycler_gui.py  # GUI configuration interface
├── output/                      # Generated wallpapers
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Example

See `example_quotes.csv` for a sample input file format.

## License

See LICENSE file for details.
