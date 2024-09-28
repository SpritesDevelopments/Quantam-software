# main.spec
# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('allinonedevelopertool.ico', '.'),                # Include the icon
        ('resources/*', 'resources'),                      # Include all files in the resources folder
        ('settings_panel.py', '.'),                        # Include additional Python modules
        ('code_editor.py', '.'),
        ('api_tester.py', '.'),
        ('git_manager.py', '.'),
        ('task_list.py', '.'),
        ('ux_ui_designer.py', '.'),
        ('sftp_manager.py', '.'),
        ('info_panel.py', '.'),
        ('discord_bot_runner.py', '.'),                     # Include the updated Discord Bot Runner
    ],
    hiddenimports=collect_submodules('tkinter'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AllInOneDeveloperTool',                          # Set the desired executable name here
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,                                        # Set to False for --windowed
    icon='allinonedevelopertool.ico',                    # Ensure the icon path is correct
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AllInOneDeveloperTool',                          # Final folder name (can be same as exe)
)
