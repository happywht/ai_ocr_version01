# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

# 项目路径
project_path = Path(SPECPATH)
src_path = project_path / 'src'

# 添加src目录到Python路径
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# 分析主程序
a = Analysis(
    ['start_exe.py'],
    pathex=[str(project_path), str(src_path)],
    binaries=[],
    datas=[
        # 包含src目录下的所有Python文件
        (str(src_path / '*.py'), 'src'),
    ],
    hiddenimports=[
        # GUI相关
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        # 图像处理
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        # HTTP请求
        'requests',
        # AI API
        'anthropic',
        # PDF处理
        'pypdfium2',
        'pypdfium2._helpers',
        'pypdfium2._helpers.page',
        'pypdfium2._helpers.bitmap',
        'pypdfium2._helpers.document',
        # Excel处理
        'openpyxl',
        'openpyxl.workbook',
        'openpyxl.worksheet',
        'openpyxl.styles',
        'openpyxl.utils',
        # 数据类型
        'dataclasses',
        'typing',
        'json',
        'base64',
        'datetime',
        'logging',
        'threading',
        # 系统相关
        'pathlib',
        'os',
        'sys',
        're',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块以减小文件大小
        'numpy',
        'scipy',
        'matplotlib',
        'jupyter',
        'IPython',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 处理PYZ
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# 处理EXE
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='发票OCR识别工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 设置为False创建窗口应用
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 如果有图标文件，可以在这里指定
)
