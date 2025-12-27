"""Runtime hook to fix Qt bundle initialization on macOS.

This hook runs before the main script to set up Qt environment variables
that help Qt find its resources when running from a PyInstaller bundle.
"""
import os
import sys

if sys.platform == 'darwin':
    # Enable layer-backed views - required for modern macOS
    os.environ['QT_MAC_WANTS_LAYER'] = '1'

    # Disable problematic Qt plugins that can crash on startup
    # The location permission plugin causes crashes when bundle isn't found
    os.environ['QT_DISABLE_PERMISSION_PLUGINS'] = '1'

    if hasattr(sys, '_MEIPASS'):
        # Running from PyInstaller bundle
        meipass = sys._MEIPASS

        # Set up Qt plugin path
        for plugin_subpath in [
            os.path.join('PyQt6', 'Qt6', 'plugins'),
            os.path.join('PyQt6', 'Qt', 'plugins'),
            'plugins',
        ]:
            plugin_path = os.path.join(meipass, plugin_subpath)
            if os.path.exists(plugin_path):
                os.environ['QT_PLUGIN_PATH'] = plugin_path
                break

        # Set QT_QPA_PLATFORM_PLUGIN_PATH for platform plugins
        for platform_subpath in [
            os.path.join('PyQt6', 'Qt6', 'plugins', 'platforms'),
            os.path.join('PyQt6', 'Qt', 'plugins', 'platforms'),
            os.path.join('plugins', 'platforms'),
        ]:
            platform_path = os.path.join(meipass, platform_subpath)
            if os.path.exists(platform_path):
                os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = platform_path
                break

        # Help Qt find resources
        os.environ['QTWEBENGINEPROCESS_PATH'] = meipass
        os.environ['QT_RESOURCES_PATH'] = meipass
