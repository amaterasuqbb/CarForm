# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['carform.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Use forward slashes for paths
        ('CarForm_amaterasuqbb_icon.ico', '.'),
        ('Darkmode_CarForm_logo.png', '.'),
        ('Lightmode_CarForm_logo.png', '.'),
        ('lgplv3-with-text-154x68.png', '.'),
        ('PySideLogo1.png', '.')
    ],
    hiddenimports=['PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='carform',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='CarForm_amaterasuqbb_icon.ico'
)