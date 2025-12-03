#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能启动器 - 专用发票OCR识别工具
提供现代化启动台UI和传统命令行界面选择
"""

import sys
import os

def add_src_to_path():
    """添加src目录到Python路径"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(current_dir, 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    return src_path

def show_startup_choice():
    """显示启动选择界面"""
    print("\n" + "="*70)
    print("    🚀 发票OCR识别工具 - 智能启动器")
    print("="*70)
    print("\n💡 请选择启动方式：\n")
    print("1. 🎛️ 专业启动台UI (推荐)")
    print("   - 现代化图形界面")
    print("   - 实时服务状态监控")
    print("   - 独立模块管理")
    print("   - 可视化操作控制")
    print("")
    print("2. 💻 传统命令行界面")
    print("   - 轻量级控制台操作")
    print("   - 直接快速启动")
    print("   - 资源占用少")
    print("")
    print("3. 🚪 退出程序")
    print("-"*70)

def get_user_choice():
    """获取用户选择"""
    try:
        choice = input("\n请输入选择 (1-3): ").strip()
        return choice
    except (EOFError, KeyboardInterrupt):
        print("\n\n👋 程序已退出")
        sys.exit(0)

def start_launcher_gui():
    """启动现代化启动台UI"""
    try:
        print("\n🎨 正在启动专业启动台UI...")
        add_src_to_path()

        # 导入并启动启动台GUI
        from src.launcher_gui import LauncherGUI

        # 创建并运行启动台
        launcher = LauncherGUI()
        launcher.run()

        return True

    except ImportError as e:
        print(f"❌ 导入启动台失败: {e}")
        print("请检查启动台文件是否存在: src/launcher_gui.py")
        return False
    except Exception as e:
        print(f"❌ 启动台启动失败: {e}")
        print("\n请确保:")
        print("1. 所有依赖库已安装 (tkinter)")
        print("2. 启动台文件完整无损坏")
        return False

def start_traditional_launcher():
    """启动传统命令行启动器"""
    try:
        print("\n💻 正在启动传统命令行启动器...")

        # 导入并启动传统启动器
        import 启动工具
        启动工具.main()

        return True

    except ImportError as e:
        print(f"❌ 导入传统启动器失败: {e}")
        print("请检查传统启动器文件是否存在: 启动工具.py")
        return False
    except Exception as e:
        print(f"❌ 传统启动器启动失败: {e}")
        print("\n请确保:")
        print("1. 所有依赖库已安装")
        print("2. 传统启动器文件完整无损坏")
        return False

def main():
    """主启动函数"""
    add_src_to_path()

    # 检查启动台GUI是否可用
    launcher_available = False
    try:
        from src.launcher_gui import LauncherGUI
        launcher_available = True
    except ImportError:
        pass

    print("🎉 欢迎使用专用发票OCR识别工具！")

    while True:
        show_startup_choice()

        # 如果启动台不可用，显示提示
        if not launcher_available:
            print("\n⚠️ 专业启动台UI暂不可用，建议使用传统命令行界面")

        choice = get_user_choice()

        if choice == "1":
            if launcher_available:
                if start_launcher_gui():
                    break
                else:
                    input("\n按 Enter 返回选择界面...")
            else:
                print("\n❌ 专业启动台UI不可用，请选择其他选项")
                input("按 Enter 继续...")

        elif choice == "2":
            if start_traditional_launcher():
                break
            else:
                input("\n按 Enter 返回选择界面...")

        elif choice == "3":
            print("\n👋 正在退出...")
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