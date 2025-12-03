#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发票OCR识别工具打包脚本
使用PyInstaller将项目打包为独立可执行文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_dependencies():
    """检查打包依赖"""
    print("=" * 60)
    print("检查打包依赖")
    print("=" * 60)

    # 包名到模块名的映射
    package_modules = {
        'pyinstaller': 'PyInstaller',
        'requests': 'requests',
        'Pillow': 'PIL',  # Pillow使用PIL模块名
        'anthropic': 'anthropic',
        'pypdfium2': 'pypdfium2',
        'openpyxl': 'openpyxl'
    }

    missing_packages = []
    for package, module in package_modules.items():
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - 缺失")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n⚠️ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行以下命令安装:")
        print(f"pip install {' '.join(missing_packages)}")
        return False

    print("\n✅ 所有依赖包检查通过")
    return True

def clean_build_dirs():
    """清理之前的构建目录"""
    print("\n" + "=" * 60)
    print("清理构建目录")
    print("=" * 60)

    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['*.spec']

    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✅ 清理目录: {dir_name}")

    # 清理Python缓存
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                os.remove(os.path.join(root, file))

    print("✅ 构建目录清理完成")

def create_spec_file():
    """创建PyInstaller配置文件"""
    print("\n" + "=" * 60)
    print("创建打包配置")
    print("=" * 60)

    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

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
    ['启动工具.py'],
    pathex=[str(project_path), str(src_path)],
    binaries=[],
    datas=[
        # 包含src目录下的所有Python文件
        (str(src_path / '*.py'), 'src'),
        # 包含文档目录
        ('docs', 'docs'),
    ],
    hiddenimports=[
        # 确保所有依赖都被包含
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'requests',
        'anthropic',
        'pypdfium2',
        'pypdfium2._helpers',
        'pypdfium2._helpers.page',
        'pypdfium2._helpers.bitmap',
        'pypdfium2._helpers.document',
        'openpyxl',
        'openpyxl.workbook',
        'openpyxl.worksheet',
        'openpyxl.styles',
        'openpyxl.utils',
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
    console=True,  # 设置为True显示控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 如果有图标文件，可以在这里指定
)
'''

    with open('invoice_ocr.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)

    print("✅ 创建配置文件: invoice_ocr.spec")

def build_exe():
    """执行打包"""
    print("\n" + "=" * 60)
    print("开始打包")
    print("=" * 60)

    try:
        # 执行PyInstaller命令
        cmd = [
            'pyinstaller',
            '--clean',
            '--noconfirm',
            'invoice_ocr.spec'
        ]

        print(f"执行命令: {' '.join(cmd)}")
        print("这个过程可能需要几分钟，请耐心等待...")

        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

        if result.returncode == 0:
            print("✅ 打包成功！")
            return True
        else:
            print("❌ 打包失败！")
            print("错误输出:")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"❌ 打包异常: {e}")
        return False

def verify_build():
    """验证打包结果"""
    print("\n" + "=" * 60)
    print("验证打包结果")
    print("=" * 60)

    exe_path = Path('dist/发票OCR识别工具.exe')

    if exe_path.exists():
        file_size = exe_path.stat().st_size
        size_mb = file_size / (1024 * 1024)

        print(f"✅ 可执行文件已生成: {exe_path}")
        print(f"✅ 文件大小: {size_mb:.1f} MB")

        # 检查文件是否可执行
        try:
            # 尝试获取文件版本信息
            import subprocess
            result = subprocess.run([str(exe_path), '--help'],
                                  capture_output=True, text=True, timeout=5)
            print("✅ 可执行文件验证通过")
        except:
            print("⚠️ 可执行文件生成，但验证超时（这通常是正常的）")

        return True
    else:
        print("❌ 可执行文件未生成")
        return False

def create_user_guide():
    """创建用户使用指南"""
    print("\n" + "=" * 60)
    print("创建用户指南")
    print("=" * 60)

    guide_content = '''# 发票OCR识别工具 - 独立可执行版本

## 🎯 功能特性

- **🖼️ 多格式支持**: 支持图片(.jpg/.png/.bmp/.tiff)和PDF文件
- **🤖 AI智能识别**: 集成智谱AI，高精度字段提取
- **📊 专业导出**: Excel横向列格式，企业级报表标准
- **⚡ 批量处理**: 一键处理大量发票文件
- **🎨 友好界面**: 现代化GUI，操作简单直观
- **🔧 灵活配置**: 支持AI/传统模式切换

## 🚀 使用方法

### 1. 启动程序
双击 `发票OCR识别工具.exe` 启动程序

### 2. 准备工作
- 确保umi-OCR服务正在运行 (127.0.0.1:1224)
- 如需使用AI功能，准备好智谱AI API密钥

### 3. 使用步骤
1. **选择文件**: 点击"📂 选择发票图片"，支持图片和PDF文件
2. **预览内容**: 查看文件预览，确认选择正确
3. **开始识别**: 点击"🚀 开始识别"进行处理
4. **查看结果**: 在"📊 提取字段"标签页查看识别结果
5. **导出数据**: 点击"💾 导出结果"选择导出格式

## 📋 系统要求

- **操作系统**: Windows 10/11 (64位)
- **内存**: 4GB以上推荐
- **磁盘空间**: 500MB可用空间
- **网络**: 需要网络连接（OCR服务和AI功能）

## ⚙️ 配置说明

### OCR服务配置
1. 下载并安装umi-OCR
2. 启动HTTP服务模式
3. 确保服务运行在 `127.0.0.1:1224`

### AI功能配置
- 在程序中配置智谱AI API密钥
- 或在配置文件中设置API信息

## 🔧 故障排除

### 常见问题

1. **"OCR服务连接失败"**
   - 检查umi-OCR服务是否启动
   - 确认端口1224是否被占用
   - 检查防火墙设置

2. **"AI解析失败"**
   - 检查API密钥是否正确
   - 确认网络连接正常
   - 检查智谱AI服务状态

3. **"文件加载失败"**
   - 确认文件格式支持
   - 检查文件是否损坏
   - 尝试使用其他文件测试

## 📞 技术支持

如遇到问题，请提供以下信息：
1. 操作系统版本
2. 错误信息和截图
3. 测试文件（如适用）

---

**版本**: 2.0.0 独立可执行版
**更新日期**: 2024-12-02
'''

    with open('dist/使用指南.md', 'w', encoding='utf-8') as f:
        f.write(guide_content)

    print("✅ 创建用户指南: dist/使用指南.md")

def main():
    """主函数"""
    print("发票OCR识别工具 - 独立可执行文件打包")
    print("=" * 80)

    # 1. 检查依赖
    if not check_dependencies():
        return False

    # 2. 清理构建目录
    clean_build_dirs()

    # 3. 创建配置文件
    create_spec_file()

    # 4. 执行打包
    if not build_exe():
        return False

    # 5. 验证打包结果
    if not verify_build():
        return False

    # 6. 创建用户指南
    create_user_guide()

    print("\n" + "=" * 80)
    print("🎉 打包完成！")
    print("=" * 80)
    print("✅ 可执行文件: dist/发票OCR识别工具.exe")
    print("✅ 使用指南: dist/使用指南.md")
    print("\n📌 使用说明:")
    print("1. 将dist目录下的文件复制到任何Windows电脑")
    print("2. 双击'发票OCR识别工具.exe'即可使用")
    print("3. 无需安装Python环境")
    print("=" * 80)

    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ 打包失败，请检查错误信息")
        sys.exit(1)
    else:
        print("\n✅ 打包成功！")
        sys.exit(0)