#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单启动脚本 - 专用发票OCR识别工具
"""

import sys
import os
import threading

# 全局变量，跟踪运行的实例
gui_instance = None
field_config_instance = None

def add_src_to_path():
    """添加src目录到Python路径"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(current_dir, 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    return src_path

def start_gui():
    """启动图形界面（单实例）"""
    global gui_instance
    if gui_instance is not None:
        print("\n⚠️ 图形界面已在运行中，不允许启动多个实例")
        return False

    try:
        print("\n🚀 启动图形界面...")
        add_src_to_path()
        from src.invoice_gui import InvoiceOCRGUI

        # 标记实例正在运行
        gui_instance = True

        def run_gui():
            try:
                app = InvoiceOCRGUI()
                app.run()
            finally:
                # 确保在任何情况下都重置实例状态
                global gui_instance
                gui_instance = None

        # 在新线程中启动GUI
        gui_thread = threading.Thread(target=run_gui, daemon=True)
        gui_thread.start()

        print("✅ 图形界面已启动")
        return True

    except Exception as e:
        print(f"❌ GUI启动失败: {e}")
        print("\n请确保:")
        print("1. 所有依赖库已安装")
        print("2. umi-OCR服务正在运行 (127.0.0.1:1224)")
        gui_instance = None  # 重置实例状态
        return False

def start_field_config():
    """启动字段配置管理器（单实例）"""
    global field_config_instance
    if field_config_instance is not None:
        print("\n⚠️ 字段配置管理器已在运行中，不允许启动多个实例")
        return False

    try:
        print("\n🔧 启动字段配置管理器...")
        add_src_to_path()
        from src.field_config_gui import FieldConfigGUI

        # 标记实例正在运行
        field_config_instance = True

        def run_field_config():
            try:
                app = FieldConfigGUI()
                app.run()
            finally:
                # 确保在任何情况下都重置实例状态
                global field_config_instance
                field_config_instance = None

        # 在新线程中启动字段配置管理器
        config_thread = threading.Thread(target=run_field_config, daemon=True)
        config_thread.start()

        print("✅ 字段配置管理器已启动")
        return True

    except Exception as e:
        print(f"❌ 字段配置管理器启动失败: {e}")
        print("\n请确保所有依赖库已安装")
        field_config_instance = None  # 重置实例状态
        return False

def show_menu():
    """显示主菜单"""
    print("\n" + "="*60)
    print("    专用发票OCR识别工具 - AI增强版")
    print("="*60)

    # 显示当前运行状态
    print("当前运行状态:")
    print(f"  图形界面: {'🟢 运行中' if gui_instance else '🔴 未运行'}")
    print(f"  字段配置: {'🟢 运行中' if field_config_instance else '🔴 未运行'}")

    print("\n请选择启动模式:")
    print("1. 图形界面 (GUI) - 推荐")
    print("2. 字段配置管理器")
    print("3. 退出")

def get_user_choice():
    """获取用户选择"""
    try:
        choice = input("\n请输入选择 (1-3): ").strip()
        return choice
    except EOFError:
        print("\n🔄 按 Enter 继续...")
        return ""

def main():
    """主启动函数"""
    add_src_to_path()

    print("🎉 欢迎使用专用发票OCR识别工具！")
    print("💡 提示：控制台会持续运行，选择3退出程序")

    while True:
        show_menu()
        choice = get_user_choice()

        if choice == "1":
            start_gui()
        elif choice == "2":
            start_field_config()
        elif choice == "3":
            print("\n👋 正在退出...")
            # 等待所有实例结束
            if gui_instance is not None:
                print("⏳ 等待图形界面关闭...")
            if field_config_instance is not None:
                print("⏳ 等待字段配置管理器关闭...")
            print("✅ 程序已退出")
            break
        elif choice == "":
            # 空输入，重新显示菜单
            continue
        else:
            print("\n❌ 无效选择，请重新输入")
            input("按 Enter 继续...")

if __name__ == "__main__":
    main()