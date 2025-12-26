# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for MetaFrame."""

import sys
from pathlib import Path

block_cipher = None

# Get the project root
project_root = Path(SPECPATH)

a = Analysis(
    [str(project_root / 'src' / 'metaframe' / '__main__.py')],
    pathex=[str(project_root / 'src')],
    binaries=[],
    datas=[
        # Include bundled fonts if any
        (str(project_root / 'src' / 'metaframe' / 'gui' / 'resources'), 'metaframe/gui/resources'),
    ],
    hiddenimports=[
        'PyQt6.sip',
        'PIL._tkinter_finder',
        'exifread',
        'click',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='metaframe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for CLI-only builds
    disable_windowed_traceback=False,
    argv_emulation=True,  # For macOS
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if desired
)

# macOS app bundle (optional)
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='MetaFrame.app',
        icon=None,  # Add .icns file path here if desired
        bundle_identifier='com.metaframe.app',
        info_plist={
            'CFBundleShortVersionString': '0.1.0',
            'CFBundleVersion': '0.1.0',
            'NSHighResolutionCapable': True,
            'NSPrincipalClass': 'NSApplication',
            'CFBundleDocumentTypes': [
                {
                    'CFBundleTypeName': 'Image',
                    'CFBundleTypeRole': 'Viewer',
                    'LSItemContentTypes': [
                        'public.jpeg',
                        'public.png',
                        'public.tiff',
                    ],
                }
            ],
        },
    )
