# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Pentagon Photonic Crystal Simulator
Build standalone executable with: pyinstaller pentagon_simulator.spec

The resulting executables will be in the 'dist' folder.
"""

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'numpy',
        'matplotlib',
        'scipy',
        'PIL',
        'meep',  # Include MEEP if available
        'cupy',  # Include CuPy if available
    ],
    hookspath=[],
    runtime_hooks=[],
    excludedimports=[
        'tcl',
        'tk',
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
    name='PentagonSimulator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)

# For Windows distribution
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PentagonSimulator',
)

# For macOS distribution
app = BUNDLE(
    exe,
    name='PentagonSimulator.app',
    icon=None,
    bundle_identifier=None,
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
    },
)
