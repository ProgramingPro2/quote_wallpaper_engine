"""Wallpaper cycler daemon for Ubuntu Wayland."""

import os
import sys
import json
import random
import time
import subprocess
import logging
from pathlib import Path
from typing import List, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class WallpaperDirectoryHandler(FileSystemEventHandler):
    """Handler for directory monitoring events."""
    
    def __init__(self, cycler):
        self.cycler = cycler
        super().__init__()
    
    def on_created(self, event):
        """Handle new file creation."""
        if not event.is_directory and event.src_path.lower().endswith('.png'):
            self.cycler.refresh_wallpaper_list()
    
    def on_deleted(self, event):
        """Handle file deletion."""
        if not event.is_directory and event.src_path.lower().endswith('.png'):
            self.cycler.refresh_wallpaper_list()


class WallpaperCycler:
    """Main wallpaper cycling daemon."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the wallpaper cycler."""
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
        self.wallpapers: List[str] = []
        self.current_index = 0
        self.observer: Optional[Observer] = None
        self.running = False
        
        # Setup logging
        self._setup_logging()
        
        # PID file path
        config_dir = Path(self.config_path).parent
        self.pid_file = config_dir / 'cycler.pid'
        
        # Initialize wallpaper list
        self.refresh_wallpaper_list()
        
        # Detect desktop environment
        self.desktop_env = self._detect_desktop_environment()
        
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        config_dir = Path.home() / '.config' / 'quote_wallpaper_cycler'
        config_dir.mkdir(parents=True, exist_ok=True)
        return str(config_dir / 'config.json')
    
    def _setup_logging(self):
        """Setup logging to file."""
        log_dir = Path.home() / '.local' / 'share' / 'quote_wallpaper_cycler'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / 'cycler.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _load_config(self) -> dict:
        """Load configuration from JSON file."""
        default_config = {
            'cycle_interval_minutes': 30,
            'random_mode': True,
            'wallpaper_directory': str(Path(__file__).parent.parent / 'output'),
            'desktop_environment': 'auto'
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except (json.JSONDecodeError, IOError) as e:
                self.logger.warning(f"Error loading config: {e}. Using defaults.")
        else:
            # Create default config file
            self._save_config(default_config)
        
        return default_config
    
    def _save_config(self, config: Optional[dict] = None):
        """Save configuration to JSON file."""
        config = config or self.config
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except IOError as e:
            self.logger.error(f"Error saving config: {e}")
    
    def _detect_desktop_environment(self) -> str:
        """Detect the desktop environment."""
        # Check if running on Wayland
        wayland_display = os.environ.get('WAYLAND_DISPLAY')
        xdg_desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        
        if wayland_display:
            # Wayland session detected
            if 'gnome' in xdg_desktop or 'unity' in xdg_desktop:
                return 'gnome-wayland'
            elif 'kde' in xdg_desktop:
                return 'kde-wayland'
            elif 'sway' in xdg_desktop or os.environ.get('SWAYSOCK'):
                return 'sway'
            else:
                return 'wayland-unknown'
        else:
            # X11 session
            if 'gnome' in xdg_desktop or 'unity' in xdg_desktop:
                return 'gnome-x11'
            elif 'kde' in xdg_desktop:
                return 'kde-x11'
            else:
                return 'x11-unknown'
    
    def refresh_wallpaper_list(self):
        """Refresh the list of available wallpapers."""
        wallpaper_dir = Path(self.config['wallpaper_directory'])
        
        if not wallpaper_dir.exists():
            self.logger.error(f"Wallpaper directory does not exist: {wallpaper_dir}")
            self.wallpapers = []
            return
        
        # Find all PNG files
        self.wallpapers = sorted([
            str(p) for p in wallpaper_dir.glob('*.png')
            if p.is_file()
        ])
        
        self.logger.info(f"Found {len(self.wallpapers)} wallpapers in {wallpaper_dir}")
        
        if not self.wallpapers:
            self.logger.warning("No wallpapers found in directory!")
    
    def _set_wallpaper_gnome_wayland(self, wallpaper_path: str) -> bool:
        """Set wallpaper for GNOME on Wayland (both light and dark themes)."""
        try:
            uri = f"file://{wallpaper_path}"
            
            # Set wallpaper for light theme
            result1 = subprocess.run(
                ['gsettings', 'set', 'org.gnome.desktop.background', 'picture-uri', uri],
                check=True,
                capture_output=True
            )
            
            # Set wallpaper for dark theme
            result2 = subprocess.run(
                ['gsettings', 'set', 'org.gnome.desktop.background', 'picture-uri-dark', uri],
                check=True,
                capture_output=True
            )
            
            self.logger.info("Set wallpaper for both light and dark themes")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.error(f"Failed to set GNOME wallpaper: {e}")
            # Try to set at least one if the other fails
            try:
                uri = f"file://{wallpaper_path}"
                subprocess.run(
                    ['gsettings', 'set', 'org.gnome.desktop.background', 'picture-uri', uri],
                    check=True,
                    capture_output=True
                )
                self.logger.warning("Only set light theme wallpaper (dark theme setting failed)")
                return True
            except:
                return False
    
    def _set_wallpaper_gnome_x11(self, wallpaper_path: str) -> bool:
        """Set wallpaper for GNOME on X11."""
        return self._set_wallpaper_gnome_wayland(wallpaper_path)
    
    def _set_wallpaper_kde_wayland(self, wallpaper_path: str) -> bool:
        """Set wallpaper for KDE on Wayland."""
        try:
            # Try plasma-apply-wallpaperimage first
            result = subprocess.run(
                ['plasma-apply-wallpaperimage', wallpaper_path],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Fallback to qdbus
        try:
            subprocess.run(
                ['qdbus', 'org.kde.plasmashell', '/PlasmaShell',
                 'org.kde.PlasmaShell.evaluateScript',
                 f'var allDesktops = desktops();for (i=0;i<allDesktops.length;i++) {{'
                 f'd = allDesktops[i];d.wallpaperPlugin = "org.kde.image";'
                 f'd.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General");'
                 f'd.writeConfig("Image", "file://{wallpaper_path}")}}'],
                check=True,
                capture_output=True,
                timeout=5
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.error(f"Failed to set KDE wallpaper: {e}")
            return False
    
    def _set_wallpaper_sway(self, wallpaper_path: str) -> bool:
        """Set wallpaper for Sway."""
        try:
            subprocess.run(
                ['swaybg', '-i', wallpaper_path, '-m', 'fill'],
                check=True,
                capture_output=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.error(f"Failed to set Sway wallpaper: {e}")
            return False
    
    def set_wallpaper(self, wallpaper_path: str) -> bool:
        """Set wallpaper using the appropriate method for the desktop environment."""
        if not os.path.exists(wallpaper_path):
            self.logger.error(f"Wallpaper file does not exist: {wallpaper_path}")
            return False
        
        desktop_env = self.config.get('desktop_environment', 'auto')
        if desktop_env == 'auto':
            desktop_env = self.desktop_env
        
        self.logger.info(f"Setting wallpaper: {os.path.basename(wallpaper_path)} (using {desktop_env})")
        
        # Try desktop-specific methods
        if desktop_env in ('gnome-wayland', 'gnome-x11'):
            return self._set_wallpaper_gnome_wayland(wallpaper_path)
        elif desktop_env == 'kde-wayland':
            return self._set_wallpaper_kde_wayland(wallpaper_path)
        elif desktop_env == 'sway':
            return self._set_wallpaper_sway(wallpaper_path)
        else:
            # Try common methods in order
            methods = [
                ('GNOME', self._set_wallpaper_gnome_wayland),
                ('KDE', self._set_wallpaper_kde_wayland),
                ('Sway', self._set_wallpaper_sway),
            ]
            
            for name, method in methods:
                if method(wallpaper_path):
                    self.logger.info(f"Successfully set wallpaper using {name} method")
                    return True
            
            self.logger.error("Failed to set wallpaper with any method")
            return False
    
    def get_next_wallpaper(self) -> Optional[str]:
        """Get the next wallpaper based on random or sequential mode."""
        if not self.wallpapers:
            return None
        
        if self.config.get('random_mode', True):
            return random.choice(self.wallpapers)
        else:
            wallpaper = self.wallpapers[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.wallpapers)
            return wallpaper
    
    def change_wallpaper(self):
        """Change to the next wallpaper."""
        if not self.wallpapers:
            self.logger.warning("No wallpapers available to change")
            return
        
        wallpaper = self.get_next_wallpaper()
        if wallpaper:
            self.set_wallpaper(wallpaper)
    
    def start_monitoring(self):
        """Start monitoring the wallpaper directory for changes."""
        wallpaper_dir = Path(self.config['wallpaper_directory'])
        
        if not wallpaper_dir.exists():
            self.logger.error(f"Cannot monitor non-existent directory: {wallpaper_dir}")
            return
        
        if self.observer is None:
            event_handler = WallpaperDirectoryHandler(self)
            self.observer = Observer()
            self.observer.schedule(event_handler, str(wallpaper_dir), recursive=False)
            self.observer.start()
            self.logger.info(f"Started monitoring directory: {wallpaper_dir}")
    
    def stop_monitoring(self):
        """Stop monitoring the wallpaper directory."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            self.logger.info("Stopped monitoring directory")
    
    def _get_last_change_time_file(self) -> Path:
        """Get path to file storing last wallpaper change time."""
        config_dir = Path(self.config_path).parent
        return config_dir / 'last_change_time.txt'
    
    def _get_last_change_time(self) -> Optional[float]:
        """Get the timestamp of the last wallpaper change."""
        time_file = self._get_last_change_time_file()
        if time_file.exists():
            try:
                with open(time_file, 'r') as f:
                    return float(f.read().strip())
            except (ValueError, IOError):
                return None
        return None
    
    def _save_change_time(self):
        """Save the current time as the last change time."""
        time_file = self._get_last_change_time_file()
        try:
            with open(time_file, 'w') as f:
                f.write(str(time.time()))
        except IOError:
            pass
    
    def run(self):
        """Run the wallpaper cycler daemon."""
        self.running = True
        
        # Write PID file
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
        except IOError as e:
            self.logger.warning(f"Failed to write PID file: {e}")
        
        self.logger.info("Starting wallpaper cycler daemon")
        self.logger.info(f"Desktop environment: {self.desktop_env}")
        self.logger.info(f"Cycle interval: {self.config['cycle_interval_minutes']} minutes")
        self.logger.info(f"Random mode: {self.config.get('random_mode', True)}")
        
        # Start monitoring directory
        self.start_monitoring()
        
        # Check if we need to catch up on missed cycles
        cycle_interval = self.config['cycle_interval_minutes'] * 60  # Convert to seconds
        last_change_time = self._get_last_change_time()
        current_time = time.time()
        
        if last_change_time:
            elapsed = current_time - last_change_time
            if elapsed >= cycle_interval:
                # Enough time has passed, change wallpaper immediately
                cycles_missed = int(elapsed / cycle_interval)
                self.logger.info(f"System was off/sleeping. {cycles_missed} cycle(s) missed. Changing wallpaper now.")
                if self.wallpapers:
                    self.change_wallpaper()
                    self._save_change_time()
            else:
                # Not enough time has passed, wait for the remainder
                wait_time = cycle_interval - elapsed
                self.logger.info(f"Last change was {int(elapsed/60)} minutes ago. Waiting {int(wait_time/60)} more minutes.")
        else:
            # First run or no previous time recorded, set initial wallpaper
            if self.wallpapers:
                self.change_wallpaper()
                self._save_change_time()
        
        # Main loop - check every 5 seconds instead of sleeping for full interval
        check_interval = 5  # Check every 5 seconds
        try:
            while self.running:
                time.sleep(check_interval)
                
                if not self.running:
                    break
                
                # Reload config in case it changed
                new_config = self._load_config()
                if new_config != self.config:
                    self.logger.info("Configuration changed, reloading...")
                    self.config = new_config
                    cycle_interval = self.config['cycle_interval_minutes'] * 60
                    self.refresh_wallpaper_list()
                
                # Check if enough time has passed since last change
                last_change_time = self._get_last_change_time()
                if last_change_time:
                    elapsed = time.time() - last_change_time
                    if elapsed >= cycle_interval:
                        # Enough time has passed, change wallpaper
                        cycles_missed = int(elapsed / cycle_interval)
                        if cycles_missed > 1:
                            self.logger.info(f"Detected {cycles_missed} missed cycle(s). Changing wallpaper now.")
                        self.change_wallpaper()
                        self._save_change_time()
                else:
                    # No previous time recorded, set initial wallpaper
                    if self.wallpapers:
                        self.change_wallpaper()
                        self._save_change_time()
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal, shutting down...")
        finally:
            self.stop_monitoring()
            # Remove PID file
            if self.pid_file.exists():
                try:
                    self.pid_file.unlink()
                except IOError:
                    pass
            self.running = False
            self.logger.info("Wallpaper cycler daemon stopped")
    
    def stop(self):
        """Stop the daemon."""
        self.running = False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Wallpaper cycler daemon for Ubuntu Wayland')
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test wallpaper setting and exit'
    )
    
    args = parser.parse_args()
    
    cycler = WallpaperCycler(config_path=args.config)
    
    if args.test:
        # Test mode: just change wallpaper once and exit
        if cycler.wallpapers:
            wallpaper = cycler.get_next_wallpaper()
            if wallpaper:
                success = cycler.set_wallpaper(wallpaper)
                sys.exit(0 if success else 1)
        else:
            print("No wallpapers found!")
            sys.exit(1)
    else:
        # Daemon mode: run continuously
        cycler.run()


if __name__ == '__main__':
    main()

