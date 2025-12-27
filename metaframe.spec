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
    datas=[],
    hiddenimports=[
        'PyQt6.sip',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PIL._tkinter_finder',
        'exifread',
        'click',
        # RAW image support (optional - imported lazily)
        'rawpy',
        'rawpy._rawpy',
        'numpy',
        # HEIF support (optional - imported lazily)
        'pillow_heif',
        'pillow_heif._pillow_heif',
    ],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=['hooks/hook-qt-macos.py'] if sys.platform == 'darwin' else [],
    excludes=[
        'tkinter',
        'matplotlib',
        'pandas',
        'scipy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if sys.platform == 'darwin':
    # macOS: Create one-folder build, then bundle into .app
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='metaframe',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,  # Disable UPX on macOS to avoid issues
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,  # Disable argv emulation - causes Qt crashes on macOS
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=None,
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=False,  # Disable UPX on macOS
        upx_exclude=[],
        name='metaframe',
    )

    app = BUNDLE(
        coll,
        name='MetaFrame.app',
        icon=None,
        bundle_identifier='com.metaframe.app',
        info_plist={
            'CFBundleShortVersionString': '0.2.0',
            'CFBundleVersion': '0.2.0',
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
else:
    # Windows/Linux: Create one-file executable
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
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=None,
    )
