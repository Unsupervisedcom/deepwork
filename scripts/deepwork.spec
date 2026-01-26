# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for building DeepWork Windows executable.

Build with: pyinstaller scripts/deepwork.spec

This creates a standalone Windows executable that can be distributed
without requiring Python to be installed.
"""

import sys
from pathlib import Path

# Get the project root (parent of scripts/)
project_root = Path(SPECPATH).parent
src_path = project_root / 'src'

block_cipher = None

a = Analysis(
    [str(src_path / 'deepwork' / 'cli' / 'main.py')],
    pathex=[str(src_path)],
    binaries=[],
    datas=[
        # Include templates and standard jobs
        (str(src_path / 'deepwork' / 'templates'), 'deepwork/templates'),
        (str(src_path / 'deepwork' / 'standard_jobs'), 'deepwork/standard_jobs'),
        (str(src_path / 'deepwork' / 'schemas'), 'deepwork/schemas'),
        (str(src_path / 'deepwork' / 'hooks'), 'deepwork/hooks'),
    ],
    hiddenimports=[
        'deepwork',
        'deepwork.cli',
        'deepwork.cli.main',
        'deepwork.cli.install',
        'deepwork.cli.sync',
        'deepwork.cli.hook',
        'deepwork.cli.rules',
        'deepwork.core',
        'deepwork.core.adapters',
        'deepwork.core.detector',
        'deepwork.core.hooks_syncer',
        'deepwork.core.job',
        'deepwork.core.registry',
        'deepwork.core.skill',
        'deepwork.hooks',
        'deepwork.hooks.wrapper',
        'deepwork.hooks.rules_check',
        'deepwork.utils',
        'deepwork.utils.fs',
        'deepwork.utils.git',
        'click',
        'rich',
        'rich.console',
        'rich.table',
        'rich.panel',
        'jinja2',
        'yaml',
        'jsonschema',
        'git',
    ],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='deepwork',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # TODO: Add icon when available
)
