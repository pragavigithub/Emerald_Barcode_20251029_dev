# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(SPEC))

# Define paths
templates_dir = os.path.join(current_dir, 'templates')
static_dir = os.path.join(current_dir, 'static')
modules_dir = os.path.join(current_dir, 'modules')

# Collect all template files
template_files = []
for root, dirs, files in os.walk(templates_dir):
    for file in files:
        if file.endswith('.html'):
            src = os.path.join(root, file)
            # Maintain directory structure in the executable
            rel_path = os.path.relpath(src, current_dir)
            template_files.append((src, os.path.dirname(rel_path)))

# Collect all static files
static_files = []
for root, dirs, files in os.walk(static_dir):
    for file in files:
        src = os.path.join(root, file)
        rel_path = os.path.relpath(src, current_dir)
        static_files.append((src, os.path.dirname(rel_path)))

# Collect module template files
module_template_files = []
for root, dirs, files in os.walk(modules_dir):
    for file in files:
        if file.endswith('.html'):
            src = os.path.join(root, file)
            rel_path = os.path.relpath(src, current_dir)
            module_template_files.append((src, os.path.dirname(rel_path)))

# Combine all data files
all_data_files = template_files + static_files + module_template_files

# Hidden imports for Flask and related packages
hidden_imports = [
    'flask',
    'flask_sqlalchemy',
    'flask_login',
    'werkzeug.security',
    'jinja2',
    'sqlalchemy',
    'psycopg2',
    'pymysql',
    'mysql.connector',
    'pyodbc',
    'requests',
    'qrcode',
    'PIL',
    'barcode',
    'logging.config',
    'json',
    'datetime',
    'os',
    'sys',
]

a = Analysis(
    ['main.py'],
    pathex=[current_dir],
    binaries=[],
    datas=all_data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WMS_Application',
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
)