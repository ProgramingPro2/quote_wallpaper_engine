"""GUI configuration window for wallpaper cycler."""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional

# Check for tkinter availability
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except ImportError:
    print("Error: tkinter is not available.")
    print("\nTo install tkinter on Ubuntu, run:")
    print("  sudo apt-get install python3-tk")
    print("\nNote: tkinter is a system package and cannot be installed via pip.")
    sys.exit(1)


class WallpaperCyclerGUI:
    """GUI for configuring and controlling the wallpaper cycler."""
    
    def __init__(self, root):
        """Initialize the GUI."""
        self.root = root
        self.root.title("Wallpaper Cycler Configuration")
        self.root.geometry("500x450")
        self.root.resizable(False, False)
        
        # Configuration paths
        self.config_dir = Path.home() / '.config' / 'quote_wallpaper_cycler'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.config_dir / 'config.json'
        self.pid_file = self.config_dir / 'cycler.pid'
        
        # Load configuration
        self.config = self._load_config()
        
        # Variables
        self.cycle_interval_var = tk.StringVar(value=str(self.config.get('cycle_interval_minutes', 30)))
        self.random_mode_var = tk.BooleanVar(value=self.config.get('random_mode', True))
        self.directory_var = tk.StringVar(value=self.config.get('wallpaper_directory', ''))
        self.status_var = tk.StringVar(value="Stopped")
        
        # Check if daemon is running
        self.daemon_running = self._check_daemon_running()
        if self.daemon_running:
            self.status_var.set("Running")
        
        # Build UI
        self._build_ui()
        
        # Update status periodically
        self._update_status()
    
    def _load_config(self) -> dict:
        """Load configuration from file."""
        default_config = {
            'cycle_interval_minutes': 30,
            'random_mode': True,
            'wallpaper_directory': str(Path(__file__).parent.parent / 'output'),
            'desktop_environment': 'auto'
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except (json.JSONDecodeError, IOError):
                pass
        
        return default_config
    
    def _save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except IOError as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
            return False
    
    def _check_daemon_running(self) -> bool:
        """Check if the daemon is currently running."""
        if not self.pid_file.exists():
            return False
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process is still running
            try:
                os.kill(pid, 0)  # Signal 0 just checks if process exists
                return True
            except OSError:
                # Process doesn't exist, remove stale PID file
                self.pid_file.unlink()
                return False
        except (ValueError, IOError):
            return False
    
    def _get_script_path(self) -> str:
        """Get the absolute path to the wallpaper_cycler.py script."""
        script_path = Path(__file__).parent / 'wallpaper_cycler.py'
        return str(script_path.absolute())
    
    def _get_python_path(self) -> str:
        """Get the Python interpreter path, checking for venv first."""
        # Check if we're in a virtual environment
        venv_python = Path(__file__).parent.parent / '.venv' / 'bin' / 'python'
        if venv_python.exists():
            return str(venv_python.absolute())
        
        # Use system Python
        return sys.executable
    
    def _start_daemon(self):
        """Start the wallpaper cycler daemon."""
        if self.daemon_running:
            messagebox.showwarning("Already Running", "The wallpaper cycler is already running.")
            return
        
        # Validate configuration before starting
        if not self._validate_config():
            return
        
        # Save current configuration
        if not self._save_config():
            return
        
        # Start daemon
        python_path = self._get_python_path()
        script_path = self._get_script_path()
        
        try:
            # Start daemon in background
            process = subprocess.Popen(
                [python_path, script_path, '--config', str(self.config_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            # Save PID
            with open(self.pid_file, 'w') as f:
                f.write(str(process.pid))
            
            self.daemon_running = True
            self.status_var.set("Running")
            messagebox.showinfo("Success", "Wallpaper cycler started successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start daemon: {e}")
    
    def _stop_daemon(self):
        """Stop the wallpaper cycler daemon."""
        if not self.daemon_running:
            messagebox.showwarning("Not Running", "The wallpaper cycler is not running.")
            return
        
        if not self.pid_file.exists():
            self.daemon_running = False
            self.status_var.set("Stopped")
            return
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Try graceful shutdown first (SIGTERM)
            try:
                os.kill(pid, 15)  # SIGTERM
                # Wait a bit for graceful shutdown
                import time
                time.sleep(1)
                
                # Check if still running
                try:
                    os.kill(pid, 0)
                    # Still running, force kill
                    os.kill(pid, 9)  # SIGKILL
                except OSError:
                    pass  # Process already stopped
            except OSError:
                pass  # Process doesn't exist
            
            # Remove PID file
            if self.pid_file.exists():
                self.pid_file.unlink()
            
            self.daemon_running = False
            self.status_var.set("Stopped")
            messagebox.showinfo("Success", "Wallpaper cycler stopped successfully!")
        except (ValueError, IOError) as e:
            messagebox.showerror("Error", f"Failed to stop daemon: {e}")
    
    def _validate_config(self) -> bool:
        """Validate the current configuration."""
        # Validate cycle interval
        try:
            interval = int(self.cycle_interval_var.get())
            if interval < 1 or interval > 1440:
                messagebox.showerror("Validation Error", 
                                   "Cycle interval must be between 1 and 1440 minutes (24 hours).")
                return False
        except ValueError:
            messagebox.showerror("Validation Error", "Cycle interval must be a valid number.")
            return False
        
        # Validate directory
        directory = self.directory_var.get().strip()
        if not directory:
            messagebox.showerror("Validation Error", "Wallpaper directory is required.")
            return False
        
        dir_path = Path(directory)
        if not dir_path.exists():
            messagebox.showerror("Validation Error", f"Directory does not exist: {directory}")
            return False
        
        if not dir_path.is_dir():
            messagebox.showerror("Validation Error", f"Path is not a directory: {directory}")
            return False
        
        # Check for PNG files
        png_files = list(dir_path.glob('*.png'))
        if not png_files:
            response = messagebox.askyesno(
                "Warning",
                f"No PNG files found in {directory}. Continue anyway?"
            )
            if not response:
                return False
        
        return True
    
    def _apply_config(self):
        """Apply configuration changes."""
        if not self._validate_config():
            return
        
        # Update config dict
        self.config['cycle_interval_minutes'] = int(self.cycle_interval_var.get())
        self.config['random_mode'] = self.random_mode_var.get()
        self.config['wallpaper_directory'] = self.directory_var.get().strip()
        
        # Save to file
        if self._save_config():
            messagebox.showinfo("Success", "Configuration saved successfully!")
            
            # If daemon is running, it will pick up the changes on next cycle
            if self.daemon_running:
                messagebox.showinfo("Note", 
                                 "Configuration saved. The running daemon will use the new settings on the next cycle.")
    
    def _browse_directory(self):
        """Open directory browser."""
        initial_dir = self.directory_var.get() or str(Path.home())
        directory = filedialog.askdirectory(initialdir=initial_dir, title="Select Wallpaper Directory")
        
        if directory:
            self.directory_var.set(directory)
    
    def _setup_autostart(self):
        """Set up autostart desktop entry."""
        autostart_dir = Path.home() / '.config' / 'autostart'
        autostart_dir.mkdir(parents=True, exist_ok=True)
        
        desktop_file = autostart_dir / 'quote-wallpaper-cycler.desktop'
        
        python_path = self._get_python_path()
        script_path = self._get_script_path()
        config_path = str(self.config_path)
        
        desktop_entry = f"""[Desktop Entry]
Type=Application
Name=Quote Wallpaper Cycler
Comment=Automatically cycle through quote wallpapers
Exec={python_path} {script_path} --config {config_path}
Icon=preferences-desktop-wallpaper
Terminal=false
Categories=Utility;
StartupNotify=false
"""
        
        try:
            with open(desktop_file, 'w') as f:
                f.write(desktop_entry)
            
            # Make executable
            os.chmod(desktop_file, 0o755)
            
            messagebox.showinfo("Success", 
                              "Autostart has been configured!\n"
                              "The wallpaper cycler will start automatically on login.")
        except IOError as e:
            messagebox.showerror("Error", f"Failed to create autostart entry: {e}")
    
    def _remove_autostart(self):
        """Remove autostart desktop entry."""
        desktop_file = Path.home() / '.config' / 'autostart' / 'quote-wallpaper-cycler.desktop'
        
        if desktop_file.exists():
            try:
                desktop_file.unlink()
                messagebox.showinfo("Success", "Autostart has been removed.")
            except IOError as e:
                messagebox.showerror("Error", f"Failed to remove autostart entry: {e}")
        else:
            messagebox.showinfo("Info", "Autostart is not configured.")
    
    def _get_log_path(self) -> Path:
        """Get the path to the log file."""
        return Path.home() / '.local' / 'share' / 'quote_wallpaper_cycler' / 'cycler.log'
    
    def _view_logs(self):
        """Open a window to view logs."""
        log_path = self._get_log_path()
        
        if not log_path.exists():
            messagebox.showinfo("Info", "No log file found. The daemon hasn't run yet.")
            return
        
        # Create a new window for log viewing
        log_window = tk.Toplevel(self.root)
        log_window.title("Wallpaper Cycler Logs")
        log_window.geometry("800x600")
        
        # Create frame with scrollbar
        log_frame = ttk.Frame(log_window, padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Text widget with scrollbar
        scrollbar = ttk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        log_text = tk.Text(log_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set, 
                          font=('monospace', 9))
        log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=log_text.yview)
        
        # Read and display log file
        try:
            with open(log_path, 'r') as f:
                content = f.read()
                log_text.insert('1.0', content)
                # Scroll to bottom
                log_text.see(tk.END)
        except IOError as e:
            log_text.insert('1.0', f"Error reading log file: {e}")
        
        # Make text read-only
        log_text.config(state=tk.DISABLED)
        
        # Button frame
        button_frame = ttk.Frame(log_window, padding="10")
        button_frame.pack(fill=tk.X)
        
        def refresh_logs():
            """Refresh the log display."""
            log_text.config(state=tk.NORMAL)
            log_text.delete('1.0', tk.END)
            try:
                with open(log_path, 'r') as f:
                    content = f.read()
                    log_text.insert('1.0', content)
                    log_text.see(tk.END)
            except IOError as e:
                log_text.insert('1.0', f"Error reading log file: {e}")
            log_text.config(state=tk.DISABLED)
        
        def open_in_editor():
            """Open log file in system default text editor."""
            try:
                # Try to open with system default editor
                subprocess.Popen(['xdg-open', str(log_path)])
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open log file: {e}")
        
        refresh_btn = ttk.Button(button_frame, text="Refresh", command=refresh_logs)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        open_btn = ttk.Button(button_frame, text="Open in Editor", command=open_in_editor)
        open_btn.pack(side=tk.LEFT, padx=5)
        
        close_btn = ttk.Button(button_frame, text="Close", command=log_window.destroy)
        close_btn.pack(side=tk.RIGHT, padx=5)
    
    def _update_status(self):
        """Update daemon status periodically."""
        self.daemon_running = self._check_daemon_running()
        if self.daemon_running:
            self.status_var.set("Running")
        else:
            self.status_var.set("Stopped")
        
        # Schedule next update
        self.root.after(2000, self._update_status)
    
    def _build_ui(self):
        """Build the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Wallpaper Cycler Configuration", 
                               font=('', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Status
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        ttk.Label(status_frame, text="Status:").grid(row=0, column=0, padx=(0, 10))
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                font=('', 10, 'bold'))
        status_label.grid(row=0, column=1)
        
        # Cycle interval
        ttk.Label(main_frame, text="Cycle Interval (minutes):").grid(row=2, column=0, sticky=tk.W, pady=5)
        interval_entry = ttk.Entry(main_frame, textvariable=self.cycle_interval_var, width=10)
        interval_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(main_frame, text="(1-1440)").grid(row=2, column=2, sticky=tk.W, padx=5)
        
        # Random mode
        random_check = ttk.Checkbutton(main_frame, text="Random Mode", 
                                      variable=self.random_mode_var)
        random_check.grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # Directory
        ttk.Label(main_frame, text="Wallpaper Directory:").grid(row=4, column=0, sticky=tk.W, pady=5)
        directory_entry = ttk.Entry(main_frame, textvariable=self.directory_var, width=40)
        directory_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        browse_btn = ttk.Button(main_frame, text="Browse...", command=self._browse_directory)
        browse_btn.grid(row=4, column=2, padx=5, pady=5)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=20)
        
        # Control buttons
        start_btn = ttk.Button(button_frame, text="Start", command=self._start_daemon)
        start_btn.grid(row=0, column=0, padx=5)
        
        stop_btn = ttk.Button(button_frame, text="Stop", command=self._stop_daemon)
        stop_btn.grid(row=0, column=1, padx=5)
        
        apply_btn = ttk.Button(button_frame, text="Apply Settings", command=self._apply_config)
        apply_btn.grid(row=0, column=2, padx=5)
        
        view_logs_btn = ttk.Button(button_frame, text="View Logs", command=self._view_logs)
        view_logs_btn.grid(row=0, column=3, padx=5)
        
        # Autostart frame
        autostart_frame = ttk.LabelFrame(main_frame, text="Autostart", padding="10")
        autostart_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        autostart_desc = ttk.Label(autostart_frame, 
                                   text="Configure the wallpaper cycler to start automatically on login.")
        autostart_desc.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        setup_autostart_btn = ttk.Button(autostart_frame, text="Enable Autostart", 
                                        command=self._setup_autostart)
        setup_autostart_btn.grid(row=1, column=0, padx=5)
        
        remove_autostart_btn = ttk.Button(autostart_frame, text="Disable Autostart", 
                                         command=self._remove_autostart)
        remove_autostart_btn.grid(row=1, column=1, padx=5)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)


def main():
    """Main entry point."""
    root = tk.Tk()
    app = WallpaperCyclerGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()

