#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专用发票OCR识别工具 - 独立可执行版本启动脚本
自动检测打包环境，直接启动GUI界面
"""

import sys
import os

def main():
    """主启动函数"""
    print("=" * 60)
    print("    专用发票OCR识别工具 - AI增强版 (独立可执行版)")
    print("=" * 60)
    print("🚀 正在启动图形界面...")

    # 添加src目录到Python路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(current_dir, 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    try:
        from invoice_gui import InvoiceOCRGUI
        app = InvoiceOCRGUI()
        app.run()
    except Exception as e:
        print(f"❌ GUI启动失败: {e}")
        print("\n请确保:")
        print("1. 所有依赖库已正确打包")
        print("2. umi-OCR服务正在运行 (127.0.0.1:1224)")
        print("3. 系统满足最低要求")
        print("\n按任意键退出...")
        try:
            input()
        except:
            pass

if __name__ == "__main__":
    main()