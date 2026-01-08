"""GUI application for wallpaper generation with presets and configuration."""

import os
import sys
import json
from pathlib import Path

# Handle both module and script execution
if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Check for tkinter availability
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext
except ImportError:
    print("Error: tkinter is not available.")
    print("\nTo install tkinter on Ubuntu, run:")
    print("  sudo apt-get install python3-tk")
    print("\nNote: tkinter is a system package and cannot be installed via pip.")
    sys.exit(1)

from typing import Optional, Dict, List, Tuple
from PIL import Image, ImageTk

# Handle imports
try:
    from .quote_parser import Quote, QuoteParser
    from .wallpaper_generator import WallpaperGenerator
    from .styles import get_all_styles, get_style_function
    from .utils import COLOR_SCHEMES, get_dark_color_schemes
except ImportError:
    from src.quote_parser import Quote, QuoteParser
    from src.wallpaper_generator import WallpaperGenerator
    from src.styles import get_all_styles, get_style_function
    from src.utils import COLOR_SCHEMES, get_dark_color_schemes


class PresetManager:
    """Manages preset loading and saving."""
    
    def __init__(self):
        """Initialize preset manager."""
        # Built-in presets directory
        script_dir = Path(__file__).parent
        self.builtin_presets_dir = script_dir / 'presets'
        
        # User presets directory
        self.user_presets_dir = Path.home() / '.config' / 'quote_wallpaper_generator' / 'presets'
        self.user_presets_dir.mkdir(parents=True, exist_ok=True)
    
    def load_builtin_presets(self) -> List[Dict]:
        """Load all built-in presets."""
        presets = []
        if self.builtin_presets_dir.exists():
            for preset_file in self.builtin_presets_dir.glob('*.json'):
                try:
                    with open(preset_file, 'r') as f:
                        preset = json.load(f)
                        preset['_builtin'] = True
                        preset['_path'] = str(preset_file)
                        presets.append(preset)
                except (json.JSONDecodeError, IOError):
                    continue
        return presets
    
    def load_user_presets(self) -> List[Dict]:
        """Load all user custom presets."""
        presets = []
        if self.user_presets_dir.exists():
            for preset_file in self.user_presets_dir.glob('*.json'):
                try:
                    with open(preset_file, 'r') as f:
                        preset = json.load(f)
                        preset['_builtin'] = False
                        preset['_path'] = str(preset_file)
                        presets.append(preset)
                except (json.JSONDecodeError, IOError):
                    continue
        return presets
    
    def load_all_presets(self) -> List[Dict]:
        """Load all presets (built-in and user)."""
        builtin = self.load_builtin_presets()
        user = self.load_user_presets()
        return builtin + user
    
    def save_preset(self, preset: Dict) -> bool:
        """Save a custom preset."""
        name = preset.get('name', '')
        if not name:
            return False
        
        # Sanitize filename
        filename = name.lower().replace(' ', '_')
        filename = ''.join(c for c in filename if c.isalnum() or c in ('_', '-'))
        filename = f"{filename}.json"
        
        preset_path = self.user_presets_dir / filename
        
        # Check if name already exists (but allow overwriting)
        existing = self.load_user_presets()
        for existing_preset in existing:
            if existing_preset.get('name') == name and existing_preset.get('_path') != str(preset_path):
                return False  # Duplicate name
        
        # Remove internal fields before saving
        save_preset = {k: v for k, v in preset.items() if not k.startswith('_')}
        
        try:
            with open(preset_path, 'w') as f:
                json.dump(save_preset, f, indent=2)
            return True
        except IOError:
            return False
    
    def delete_preset(self, preset: Dict) -> bool:
        """Delete a user preset."""
        if preset.get('_builtin', False):
            return False  # Cannot delete built-in presets
        
        preset_path = Path(preset.get('_path', ''))
        if preset_path.exists() and preset_path.parent == self.user_presets_dir:
            try:
                preset_path.unlink()
                return True
            except IOError:
                return False
        return False


class WallpaperGeneratorGUI:
    """Main GUI application for wallpaper generation."""
    
    def __init__(self, root):
        """Initialize the GUI."""
        self.root = root
        self.root.title("Quote Wallpaper Generator")
        self.root.geometry("900x700")
        
        self.preset_manager = PresetManager()
        
        # Configuration variables
        self.resolution_var = tk.StringVar(value="3840x2160")
        self.text_position_var = tk.StringVar(value="bottom-left")
        self.color_scheme_var = tk.StringVar()
        self.style_var = tk.StringVar()
        self.output_dir_var = tk.StringVar(value=str(Path(__file__).parent.parent / 'output'))
        
        # Quote input variables
        self.author_var = tk.StringVar()
        self.source_var = tk.StringVar()
        
        # Batch processing variables
        self.input_file_var = tk.StringVar()
        
        # Preset variables
        self.preset_var = tk.StringVar()
        
        # Initialize color scheme and style lists
        self._initialize_options()
        
        # Build UI
        self._build_ui()
        
        # Load first preset as default
        presets = self.preset_manager.load_all_presets()
        if presets:
            self._load_preset(presets[0])
    
    def _initialize_options(self):
        """Initialize dropdown options."""
        # Color scheme names
        self.color_scheme_names = [
            "Dark Gray",
            "Dark Blue-Gray",
            "Dark Blue Accent",
            "Light Gray",
            "Light Blue-Gray",
            "Warm Dark",
            "Cool Dark"
        ]
        
        # Style options
        self.style_options = []
        styles = get_all_styles()
        for category, name, _ in styles:
            display_name = f"{category.capitalize()}: {name.capitalize()}"
            self.style_options.append((display_name, category, name))
    
    def _build_ui(self):
        """Build the user interface."""
        # Main notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Single generation tab
        self.single_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.single_frame, text="Single Generation")
        self._build_single_tab()
        
        # Batch processing tab
        self.batch_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.batch_frame, text="Batch Processing")
        self._build_batch_tab()
    
    def _build_single_tab(self):
        """Build single generation tab."""
        # Left column - Input
        left_frame = ttk.LabelFrame(self.single_frame, text="Quote Input", padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        ttk.Label(left_frame, text="Quote:").grid(row=0, column=0, sticky=tk.W, pady=5)
        quote_text = scrolledtext.ScrolledText(left_frame, width=40, height=8, wrap=tk.WORD)
        quote_text.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        self.quote_text_widget = quote_text
        
        ttk.Label(left_frame, text="Author:").grid(row=2, column=0, sticky=tk.W, pady=5)
        author_entry = ttk.Entry(left_frame, textvariable=self.author_var, width=40)
        author_entry.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(left_frame, text="Source (optional):").grid(row=4, column=0, sticky=tk.W, pady=5)
        source_entry = ttk.Entry(left_frame, textvariable=self.source_var, width=40)
        source_entry.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Right column - Configuration
        right_frame = ttk.LabelFrame(self.single_frame, text="Configuration", padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Preset selection
        preset_frame = ttk.LabelFrame(right_frame, text="Presets", padding="5")
        preset_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.preset_combo = ttk.Combobox(preset_frame, textvariable=self.preset_var, width=30, state='readonly')
        self.preset_combo.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        self._refresh_preset_list()
        self.preset_combo.bind('<<ComboboxSelected>>', self._on_preset_selected)
        
        preset_btn_frame = ttk.Frame(preset_frame)
        preset_btn_frame.grid(row=1, column=0, columnspan=2, pady=5)
        ttk.Button(preset_btn_frame, text="Load Preset", command=self._load_selected_preset).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_btn_frame, text="Save As Preset", command=self._save_current_as_preset).pack(side=tk.LEFT, padx=2)
        
        # Resolution
        ttk.Label(right_frame, text="Resolution:").grid(row=1, column=0, sticky=tk.W, pady=5)
        resolution_combo = ttk.Combobox(right_frame, textvariable=self.resolution_var, width=20, state='readonly')
        resolution_combo['values'] = ('1920x1080', '2560x1440', '3840x2160', 'Custom')
        resolution_combo.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Text position
        ttk.Label(right_frame, text="Text Position:").grid(row=2, column=0, sticky=tk.W, pady=5)
        position_combo = ttk.Combobox(right_frame, textvariable=self.text_position_var, width=20, state='readonly')
        position_combo['values'] = ('center', 'bottom-left', 'bottom-right', 'top-left', 'top-right')
        position_combo.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Color scheme
        ttk.Label(right_frame, text="Color Scheme:").grid(row=3, column=0, sticky=tk.W, pady=5)
        color_combo = ttk.Combobox(right_frame, textvariable=self.color_scheme_var, width=20, state='readonly')
        color_combo['values'] = self.color_scheme_names
        color_combo.current(0)
        color_combo.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Style pattern
        ttk.Label(right_frame, text="Style Pattern:").grid(row=4, column=0, sticky=tk.W, pady=5)
        style_combo = ttk.Combobox(right_frame, textvariable=self.style_var, width=20, state='readonly')
        style_display_names = [opt[0] for opt in self.style_options]
        style_combo['values'] = style_display_names
        style_combo.current(8)  # patterns: minimal
        style_combo.grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # Output directory
        ttk.Label(right_frame, text="Output Directory:").grid(row=5, column=0, sticky=tk.W, pady=5)
        output_frame = ttk.Frame(right_frame)
        output_frame.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5)
        output_entry = ttk.Entry(output_frame, textvariable=self.output_dir_var, width=25)
        output_entry.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(output_frame, text="Browse...", command=self._browse_output_dir).pack(side=tk.LEFT)
        
        # Buttons
        button_frame = ttk.Frame(right_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        ttk.Button(button_frame, text="Preview", command=self._generate_preview).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Generate", command=self._generate_wallpaper).pack(side=tk.LEFT, padx=5)
        
        # Configure grid weights
        self.single_frame.columnconfigure(0, weight=1)
        self.single_frame.columnconfigure(1, weight=1)
        self.single_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(0, weight=1)
        right_frame.columnconfigure(1, weight=1)
    
    def _build_batch_tab(self):
        """Build batch processing tab."""
        # Input file
        input_frame = ttk.LabelFrame(self.batch_frame, text="Input File", padding="10")
        input_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        file_frame = ttk.Frame(input_frame)
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Entry(file_frame, textvariable=self.input_file_var, width=50).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(file_frame, text="Browse...", command=self._browse_input_file).pack(side=tk.LEFT)
        
        # Configuration (reuse same config as single)
        config_frame = ttk.LabelFrame(self.batch_frame, text="Configuration", padding="10")
        config_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Preset selection
        preset_frame = ttk.LabelFrame(config_frame, text="Presets", padding="5")
        preset_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        batch_preset_combo = ttk.Combobox(preset_frame, textvariable=self.preset_var, width=30, state='readonly')
        batch_preset_combo.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        batch_preset_combo['values'] = self.preset_combo['values']
        batch_preset_combo.bind('<<ComboboxSelected>>', self._on_preset_selected)
        
        batch_preset_btn_frame = ttk.Frame(preset_frame)
        batch_preset_btn_frame.grid(row=1, column=0, columnspan=2, pady=5)
        ttk.Button(batch_preset_btn_frame, text="Load Preset", command=self._load_selected_preset).pack(side=tk.LEFT, padx=2)
        ttk.Button(batch_preset_btn_frame, text="Save As Preset", command=self._save_current_as_preset).pack(side=tk.LEFT, padx=2)
        
        # Resolution
        ttk.Label(config_frame, text="Resolution:").grid(row=1, column=0, sticky=tk.W, pady=5)
        batch_resolution_combo = ttk.Combobox(config_frame, textvariable=self.resolution_var, width=20, state='readonly')
        batch_resolution_combo['values'] = ('1920x1080', '2560x1440', '3840x2160', 'Custom')
        batch_resolution_combo.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Text position
        ttk.Label(config_frame, text="Text Position:").grid(row=2, column=0, sticky=tk.W, pady=5)
        batch_position_combo = ttk.Combobox(config_frame, textvariable=self.text_position_var, width=20, state='readonly')
        batch_position_combo['values'] = ('center', 'bottom-left', 'bottom-right', 'top-left', 'top-right')
        batch_position_combo.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Color scheme
        ttk.Label(config_frame, text="Color Scheme:").grid(row=3, column=0, sticky=tk.W, pady=5)
        batch_color_combo = ttk.Combobox(config_frame, textvariable=self.color_scheme_var, width=20, state='readonly')
        batch_color_combo['values'] = self.color_scheme_names
        batch_color_combo.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Style pattern
        ttk.Label(config_frame, text="Style Pattern:").grid(row=4, column=0, sticky=tk.W, pady=5)
        batch_style_combo = ttk.Combobox(config_frame, textvariable=self.style_var, width=20, state='readonly')
        style_display_names = [opt[0] for opt in self.style_options]
        batch_style_combo['values'] = style_display_names
        batch_style_combo.grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # Output directory
        ttk.Label(config_frame, text="Output Directory:").grid(row=5, column=0, sticky=tk.W, pady=5)
        batch_output_frame = ttk.Frame(config_frame)
        batch_output_frame.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Entry(batch_output_frame, textvariable=self.output_dir_var, width=25).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(batch_output_frame, text="Browse...", command=self._browse_output_dir).pack(side=tk.LEFT)
        
        # Process button
        process_frame = ttk.Frame(self.batch_frame)
        process_frame.grid(row=2, column=0, columnspan=2, pady=20)
        ttk.Button(process_frame, text="Process File", command=self._process_batch).pack(side=tk.LEFT, padx=5)
        
        # Progress/Status
        self.batch_status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(self.batch_frame, textvariable=self.batch_status_var)
        status_label.grid(row=3, column=0, columnspan=2, pady=5)
        
        # Configure grid weights
        self.batch_frame.columnconfigure(0, weight=1)
        config_frame.columnconfigure(1, weight=1)
    
    def _refresh_preset_list(self):
        """Refresh the preset dropdown list."""
        presets = self.preset_manager.load_all_presets()
        preset_names = [p.get('name', 'Unknown') for p in presets]
        self.preset_combo['values'] = preset_names
        if preset_names:
            self.preset_var.set(preset_names[0])
    
    def _on_preset_selected(self, event=None):
        """Handle preset selection from dropdown."""
        self._load_selected_preset()
    
    def _load_selected_preset(self):
        """Load the selected preset."""
        preset_name = self.preset_var.get()
        if not preset_name:
            return
        
        presets = self.preset_manager.load_all_presets()
        for preset in presets:
            if preset.get('name') == preset_name:
                self._load_preset(preset)
                return
    
    def _load_preset(self, preset: Dict):
        """Load a preset into the UI."""
        if 'resolution' in preset:
            self.resolution_var.set(preset['resolution'])
        
        if 'text_position' in preset:
            self.text_position_var.set(preset['text_position'])
        
        if 'color_scheme_index' in preset:
            idx = preset['color_scheme_index']
            if 0 <= idx < len(self.color_scheme_names):
                self.color_scheme_var.set(self.color_scheme_names[idx])
        
        if 'style_category' in preset and 'style_name' in preset:
            category = preset['style_category']
            name = preset['style_name']
            for i, (display_name, cat, n) in enumerate(self.style_options):
                if cat == category and n == name:
                    self.style_var.set(display_name)
                    break
    
    def _save_current_as_preset(self):
        """Save current configuration as a preset."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Save Preset")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Preset Name:").pack(pady=5)
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.pack(pady=5)
        name_entry.focus()
        
        ttk.Label(dialog, text="Description (optional):").pack(pady=5)
        desc_text = scrolledtext.ScrolledText(dialog, width=40, height=4, wrap=tk.WORD)
        desc_text.pack(pady=5)
        
        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Preset name is required.")
                return
            
            # Get current configuration
            preset = {
                'name': name,
                'description': desc_text.get('1.0', tk.END).strip(),
                'resolution': self.resolution_var.get(),
                'text_position': self.text_position_var.get(),
                'color_scheme_index': self.color_scheme_names.index(self.color_scheme_var.get()),
                'style_category': self._get_style_category(),
                'style_name': self._get_style_name()
            }
            
            if self.preset_manager.save_preset(preset):
                messagebox.showinfo("Success", f"Preset '{name}' saved successfully!")
                self._refresh_preset_list()
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to save preset. Name may already exist.")
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Save", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _get_style_category(self) -> str:
        """Get selected style category."""
        style_display = self.style_var.get()
        for display_name, category, name in self.style_options:
            if display_name == style_display:
                return category
        return 'patterns'
    
    def _get_style_name(self) -> str:
        """Get selected style name."""
        style_display = self.style_var.get()
        for display_name, category, name in self.style_options:
            if display_name == style_display:
                return name
        return 'minimal'
    
    def _browse_output_dir(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(initialdir=self.output_dir_var.get())
        if directory:
            self.output_dir_var.set(directory)
    
    def _browse_input_file(self):
        """Browse for input file."""
        filename = filedialog.askopenfilename(
            title="Select Quote File",
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.input_file_var.set(filename)
    
    def _get_resolution(self) -> Tuple[int, int]:
        """Get resolution as (width, height) tuple."""
        res_str = self.resolution_var.get()
        if res_str == 'Custom':
            messagebox.showerror("Error", "Custom resolution not yet implemented. Please select a standard resolution.")
            return None, None
        
        try:
            width, height = map(int, res_str.split('x'))
            return width, height
        except (ValueError, AttributeError):
            messagebox.showerror("Error", f"Invalid resolution format: {res_str}. Use format like '3840x2160'")
            return None, None
    
    def _get_color_scheme(self):
        """Get selected color scheme."""
        scheme_name = self.color_scheme_var.get()
        idx = self.color_scheme_names.index(scheme_name)
        return COLOR_SCHEMES[idx]
    
    def _get_style_function(self):
        """Get selected style function."""
        category = self._get_style_category()
        name = self._get_style_name()
        return get_style_function(category, name)
    
    def _generate_preview(self):
        """Generate preview at reduced resolution."""
        # Validate inputs
        quote_text = self.quote_text_widget.get('1.0', tk.END).strip()
        author = self.author_var.get().strip()
        
        if not quote_text or not author:
            messagebox.showerror("Error", "Quote and Author are required.")
            return
        
        # Get resolution (use preview size)
        width, height = 800, 450
        
        # Create quote object
        quote = Quote(
            text=quote_text,
            author=author,
            source=self.source_var.get().strip() or None
        )
        
        # Generate preview
        try:
            color_scheme = self._get_color_scheme()
            style_func = self._get_style_function()
            
            generator = WallpaperGenerator(
                width=width,
                height=height,
                color_scheme=color_scheme,
                text_position=self.text_position_var.get()
            )
            
            img = generator.generate(quote, style_func)
            self._show_preview(img)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate preview: {e}")
    
    def _show_preview(self, img: Image.Image):
        """Show preview window."""
        preview_window = tk.Toplevel(self.root)
        preview_window.title("Preview")
        
        # Convert PIL image to PhotoImage
        img_tk = ImageTk.PhotoImage(img)
        
        # Create label with image
        label = ttk.Label(preview_window, image=img_tk)
        label.image = img_tk  # Keep a reference
        label.pack(padx=10, pady=10)
        
        ttk.Button(preview_window, text="Close", command=preview_window.destroy).pack(pady=5)
    
    def _generate_wallpaper(self):
        """Generate full resolution wallpaper."""
        # Validate inputs
        quote_text = self.quote_text_widget.get('1.0', tk.END).strip()
        author = self.author_var.get().strip()
        
        if not quote_text or not author:
            messagebox.showerror("Error", "Quote and Author are required.")
            return
        
        # Get resolution
        width, height = self._get_resolution()
        if width is None or height is None:
            return
        
        # Validate output directory
        output_dir = self.output_dir_var.get()
        if not output_dir:
            messagebox.showerror("Error", "Output directory is required.")
            return
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Create quote object
        quote = Quote(
            text=quote_text,
            author=author,
            source=self.source_var.get().strip() or None
        )
        
        # Generate wallpaper
        try:
            color_scheme = self._get_color_scheme()
            style_func = self._get_style_function()
            
            generator = WallpaperGenerator(
                width=width,
                height=height,
                color_scheme=color_scheme,
                text_position=self.text_position_var.get()
            )
            
            img = generator.generate(quote, style_func)
            filepath = generator.save(img, quote, output_dir, 1)
            
            messagebox.showinfo("Success", f"Wallpaper generated successfully!\n\nSaved to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate wallpaper: {e}")
    
    def _process_batch(self):
        """Process batch file."""
        input_file = self.input_file_var.get()
        if not input_file or not os.path.exists(input_file):
            messagebox.showerror("Error", "Please select a valid input file.")
            return
        
        # Get resolution
        width, height = self._get_resolution()
        if width is None or height is None:
            return
        
        # Validate output directory
        output_dir = self.output_dir_var.get()
        if not output_dir:
            messagebox.showerror("Error", "Output directory is required.")
            return
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Parse quotes
        try:
            parser = QuoteParser()
            quotes = parser.parse_file(input_file)
            
            if not quotes:
                messagebox.showerror("Error", "No quotes found in file.")
                return
            
            # Get configuration
            color_scheme = self._get_color_scheme()
            style_func = self._get_style_function()
            
            # Process quotes
            self.batch_status_var.set(f"Processing {len(quotes)} quotes...")
            self.root.update()
            
            generator = WallpaperGenerator(
                width=width,
                height=height,
                color_scheme=color_scheme,
                text_position=self.text_position_var.get()
            )
            
            from collections import defaultdict
            author_numbers = defaultdict(int)
            
            for quote in quotes:
                author_numbers[quote.author] += 1
                number = author_numbers[quote.author]
                
                img = generator.generate(quote, style_func)
                generator.save(img, quote, output_dir, number)
            
            self.batch_status_var.set(f"Successfully processed {len(quotes)} quotes!")
            messagebox.showinfo("Success", f"Processed {len(quotes)} quotes successfully!\n\nSaved to:\n{output_dir}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process batch: {e}")
            self.batch_status_var.set("Error occurred")


def main():
    """Main entry point."""
    root = tk.Tk()
    app = WallpaperGeneratorGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
