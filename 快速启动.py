#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动脚本 - 直接启动专业启动台UI
"""

import sys
import os

def add_src_to_path():
    """添加src目录到Python路径"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(current_dir, 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

def main():
    """直接启动专业启动台"""
    try:
        print("🚀 正在启动专业发票OCR识别工具...")

        # 添加路径
        add_src_to_path()

        # 导入并启动启动台GUI
        from launcher_gui import LauncherGUI

        # 创建并运行启动台
        launcher = LauncherGUI()
        launcher.run()

    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("请检查以下文件是否存在:")
        print("- src/launcher_gui.py")
        input("按 Enter 退出...")

    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("\n请确保:")
        print("1. Python依赖库已安装")
        print("2. 图形界面支持可用")
        input("按 Enter 退出...")

if __name__ == "__main__":
    main()