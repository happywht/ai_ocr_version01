#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一启动脚本 - 专用发票OCR识别工具
支持GUI和命令行两种模式
"""

import sys
import os


def main():
    """主启动函数"""
    print("=" * 50)
    print("    专用发票OCR识别工具 - AI增强版")
    print("=" * 50)

    # 检查依赖
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

    try:
        import anthropic
    except ImportError:
        missing_deps.append("anthropic")

    try:
        import openpyxl
    except ImportError:
        missing_deps.append("openpyxl")

    if missing_deps:
        print(f"\n⚠️  缺少依赖库: {', '.join(missing_deps)}")
        response = input("\n是否自动安装缺失的依赖? (y/n): ").lower().strip()

        if response in ['y', 'yes', '是']:
            import subprocess
            for dep in missing_deps:
                print(f"正在安装 {dep}...")
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
                    print(f"✅ {dep} 安装成功")
                except subprocess.CalledProcessError:
                    print(f"❌ {dep} 安装失败，请手动运行: pip install {dep}")
            print("\n依赖安装完成！")
        else:
            print("请手动安装缺失的依赖后重试")
            print(f"命令: pip install {' '.join(missing_deps)}")
            return

    # 检测是否为打包环境（exe文件）
    is_packaged = hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS')

    if is_packaged:
        # 打包环境：直接启动GUI
        print("🚀 启动图形界面...")
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
            from src.invoice_gui import InvoiceOCRGUI
            app = InvoiceOCRGUI()
            app.run()
        except Exception as e:
            print(f"❌ GUI启动失败: {e}")
            print("请检查依赖是否正确安装")
            input("\n按任意键退出...")
    else:
        # 开发环境：显示选择菜单
        print("\n请选择启动模式:")
        print("1. 图形界面 (GUI) - 推荐")
        print("2. 命令行界面 (CLI)")
        print("3. 运行测试")
        print("4. 查看帮助")
        print("5. 退出")

        try:
            choice = input("\n请输入选择 (1-5): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n默认启动图形界面...")
            choice = "1"

        if choice == "1":
            try:
                print("\n🚀 启动图形界面...")
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
                from src.invoice_gui import InvoiceOCRGUI
                app = InvoiceOCRGUI()
                app.run()
            except Exception as e:
                print(f"❌ GUI启动失败: {e}")
                print("请检查依赖是否正确安装")

        elif choice == "2":
            if len(sys.argv) < 2:
                print("\n📝 命令行使用方法:")
                print("python start.py cli <图片文件路径> [选项]")
                print("\n选项:")
                print("  -f <格式>    导出格式: json/txt/csv/xlsx")
                print("  -o <文件>    输出文件路径")
                print("  --no-ai      禁用AI智能解析")
                print("  --debug      开启调试模式")
                print("\n示例:")
                print("python start.py cli 发票.jpg -f xlsx -o 结果.xlsx")
                print("python start.py cli 发票.pdf --no-ai")
            else:
                # 转换为命令行模式
                sys.argv[0] = "invoice_ocr_tool.py"
                sys.argv.insert(1, "cli")

                try:
                    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
                    from src.invoice_ocr_tool import main as cli_main
                    cli_main()
                except Exception as e:
                    print(f"❌ CLI模式失败: {e}")

        elif choice == "3":
            print("\n🧪 运行功能测试...")
            try:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tests'))
                import test_tool
                print("运行手动测试...")
                test_tool.main()
            except Exception as e:
                print(f"❌ 测试运行失败: {e}")

        elif choice == "4":
            print("\n📚 查看帮助信息...")
            try:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
                from src.invoice_ocr_tool import main as cli_main
                sys.argv = ["invoice_ocr_tool.py", "--help"]
                cli_main()
            except Exception as e:
                print(f"❌ 帮助信息获取失败: {e}")

        elif choice == "5":
            print("\n👋 再见！")
            return

        else:
            print("\n❌ 无效选择，请输入 1-5")


if __name__ == "__main__":
    main()
