"""Entry point for running metaframe as a module."""

import os
import sys

# Fix Qt initialization on macOS when running from PyInstaller bundle
# Must be done BEFORE any Qt imports
if sys.platform == 'darwin':
    # Enable layer-backed views for Qt on macOS
    os.environ.setdefault('QT_MAC_WANTS_LAYER', '1')

    # When running from PyInstaller bundle, set up Qt paths
    if hasattr(sys, '_MEIPASS'):
        # Set the plugin path explicitly
        plugin_path = os.path.join(sys._MEIPASS, 'PyQt6', 'Qt6', 'plugins')
        if os.path.exists(plugin_path):
            os.environ['QT_PLUGIN_PATH'] = plugin_path

        # Help Qt find the correct bundle
        # The _MEIPASS is inside Contents/Frameworks, we need Contents/MacOS
        bundle_contents = os.path.dirname(sys._MEIPASS)
        macos_dir = os.path.join(bundle_contents, 'MacOS')
        if os.path.exists(macos_dir):
            os.environ.setdefault('PYINSTALLER_MACOS_DIR', macos_dir)


def main():
    """Main entry point - launches GUI by default, CLI if arguments provided."""
    if len(sys.argv) > 1:
        from metaframe.cli.main import cli
        cli()
    else:
        from metaframe.gui.main_window import main as gui_main
        gui_main()


if __name__ == "__main__":
    main()
