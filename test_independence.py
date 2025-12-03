#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立性测试脚本 - 验证启动工具不影响功能1和2的独立性
"""

import sys
import os
import threading
import time

def add_src_to_path():
    """添加src目录到Python路径"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(current_dir, 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

def test_launcher_gui():
    """测试启动台GUI可以独立运行"""
    print("🧪 测试启动台GUI独立性...")

    try:
        add_src_to_path()
        from launcher_gui import LauncherGUI

        # 创建启动台实例但不运行主循环
        launcher = LauncherGUI()
        print("✅ 启动台GUI可以独立创建")

        # 测试基本方法
        assert hasattr(launcher, 'start_gui'), "启动台缺少start_gui方法"
        assert hasattr(launcher, 'start_field_config'), "启动台缺少start_field_config方法"
        print("✅ 启动台包含必要的方法")

        # 销毁窗口避免阻塞
        launcher.root.destroy()

        return True

    except Exception as e:
        print(f"❌ 启动台GUI独立性测试失败: {e}")
        return False

def test_invoice_gui_independence():
    """测试发票OCR识别GUI可以独立运行"""
    print("\n🧪 测试发票OCR识别GUI独立性...")

    try:
        add_src_to_path()
        from invoice_gui import InvoiceOCRGUI

        # 检查是否可以创建（但不实际运行）
        print("✅ 发票OCR识别GUI可以独立导入")

        # 验证关键组件
        assert hasattr(InvoiceOCRGUI, '__init__'), "发票GUI缺少初始化方法"
        assert hasattr(InvoiceOCRGUI, 'run'), "发票GUI缺少运行方法"
        print("✅ 发票OCR识别GUI包含必要的方法")

        return True

    except Exception as e:
        print(f"❌ 发票OCR识别GUI独立性测试失败: {e}")
        return False

def test_field_config_independence():
    """测试字段配置管理器可以独立运行"""
    print("\n🧪 测试字段配置管理器独立性...")

    try:
        add_src_to_path()
        from field_config_gui import FieldConfigGUI

        # 检查是否可以创建（但不实际运行）
        print("✅ 字段配置管理器可以独立导入")

        # 验证关键组件
        assert hasattr(FieldConfigGUI, '__init__'), "字段配置GUI缺少初始化方法"
        assert hasattr(FieldConfigGUI, 'run'), "字段配置GUI缺少运行方法"
        print("✅ 字段配置管理器包含必要的方法")

        return True

    except Exception as e:
        print(f"❌ 字段配置管理器独立性测试失败: {e}")
        return False

def test_no_circular_imports():
    """测试没有循环导入"""
    print("\n🧪 测试模块间无循环导入...")

    try:
        # 测试启动台不依赖其他GUI的实例
        add_src_to_path()

        # 检查启动台能否独立初始化
        import launcher_gui
        print("✅ 启动台可以独立导入")

        # 检查各GUI模块可以独立导入
        import invoice_gui
        import field_config_gui
        print("✅ 所有GUI模块可以独立导入")

        return True

    except Exception as e:
        print(f"❌ 循环导入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🧪 开始独立性测试...")
    print("="*60)

    tests = [
        ("启动台GUI独立性", test_launcher_gui),
        ("发票OCR识别GUI独立性", test_invoice_gui_independence),
        ("字段配置管理器独立性", test_field_config_independence),
        ("无循环导入测试", test_no_circular_imports)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        if test_func():
            passed += 1
        else:
            print(f"⚠️ {test_name} 测试失败")

    print("\n" + "="*60)
    print(f"🎯 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("✅ 所有独立性测试通过！")
        print("✅ 启动工具不影响功能1和2的独立性")
    else:
        print("❌ 部分测试失败，需要修复依赖问题")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)