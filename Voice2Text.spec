# -*- mode: python ; coding: utf-8 -*-


import os
import importlib.util

vosk_spec = importlib.util.find_spec('vosk')
if vosk_spec and vosk_spec.origin:
    vosk_path = os.path.dirname(vosk_spec.origin)
else:
    raise RuntimeError('Could not find vosk module path')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[(vosk_path, 'vosk'), ('assets', 'assets')],
    hiddenimports=['vosk'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Voice2Text',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Voice2Text',
)
