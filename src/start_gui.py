#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI启动脚本 - 专用发票OCR识别工具
快速启动图形界面版本
"""

import sys
import os

def check_dependencies():
    """检查依赖库"""
    missing_deps = []

    try:
        import requests
    except ImportError:
        missing_deps.append("requests")

    try:
        from PIL import Image, ImageTk
    except ImportError:
        missing_deps.append("Pillow")
    
    try:
        import pypdfium2
    except ImportError:
        missing_deps.append("pypdfium2")

    return missing_deps

def install_dependencies(missing_deps):
    """安装缺失的依赖"""
    import subprocess

    for dep in missing_deps:
        print(f"正在安装 {dep}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✅ {dep} 安装成功")
        except subprocess.CalledProcessError:
            print(f"❌ {dep} 安装失败")
            return False

    return True

def main():
    """主函数"""
    print("=== 专用发票OCR识别工具 ===")
    print("正在检查依赖库...")

    missing_deps = check_dependencies()

    if missing_deps:
        print(f"发现缺失的依赖库: {', '.join(missing_deps)}")

        response = input("是否自动安装缺失的依赖? (y/n): ").lower().strip()
        if response in ['y', 'yes', '是']:
            if not install_dependencies(missing_deps):
                print("依赖安装失败，请手动运行以下命令:")
                print(f"pip install {' '.join(missing_deps)}")
                input("按任意键退出...")
                return
        else:
            print("请手动安装缺失的依赖后再运行:")
            print(f"pip install {' '.join(missing_deps)}")
            input("按任意键退出...")
            return

    print("✅ 依赖检查完成，正在启动GUI...")

    try:
        from invoice_gui import InvoiceOCRGUI
        app = InvoiceOCRGUI()
        app.run()
    except Exception as e:
        print(f"启动GUI失败: {e}")
        input("按任意键退出...")

if __name__ == "__main__":
    main()