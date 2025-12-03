#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门调试字段配置管理器的GUI问题
模拟真实的用户操作场景
"""

import sys
import os
import tkinter as tk
from tkinter import ttk

# 添加src目录到路径
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

def simulate_main_gui_launch():
    """模拟从主GUI启动字段配置管理器"""
    print("=" * 60)
    print("模拟场景1: 从主GUI启动字段配置管理器")
    print("=" * 60)

    try:
        # 模拟主GUI环境
        print("1. 模拟主GUI初始化...")

        # 首先创建一个模拟的主窗口
        main_root = tk.Tk()
        main_root.title("模拟主GUI")
        main_root.geometry("400x300")
        main_root.withdraw()  # 隐藏，只是模拟

        print("2. 从主GUI启动字段配置管理器...")
        # 模拟invoice_gui.py中的open_field_config方法
        from field_config_gui import FieldConfigGUI

        # 传递父窗口引用（这是关键差异）
        config_gui = FieldConfigGUI(parent_window=main_root)

        print("3. 检查GUI状态...")
        print(f"   - 父窗口引用: {config_gui.parent_window is not None}")
        print(f"   - 字段列表大小: {config_gui.field_listbox.size()}")

        # 检查第一个字段
        if config_gui.field_listbox.size() > 0:
            first_field = config_gui.field_listbox.get(0)
            print(f"   - 第一个字段: {first_field}")

            # 模拟用户选择字段
            config_gui.field_listbox.selection_set(0)
            config_gui.on_field_select(None)

            print(f"   - 选择后表单字段名: '{config_gui.name_var.get()}'")
            print(f"   - 选择后表单描述: '{config_gui.description_var.get()}'")
            print(f"   - 选择后AI提示词长度: {len(config_gui.ai_prompt_text.get(1.0, tk.END).strip())}")

            # 检查是否为空
            if not config_gui.name_var.get():
                print("   ❌ 问题发现: 字段名称为空！")
            if not config_gui.description_var.get():
                print("   ❌ 问题发现: 字段描述为空！")
            if not config_gui.ai_prompt_text.get(1.0, tk.END).strip():
                print("   ❌ 问题发现: AI提示词为空！")
        else:
            print("   ❌ 问题发现: 字段列表为空！")

        print("4. 测试保存功能...")
        # 尝试保存一个新字段
        config_gui.add_field()  # 清空表单
        config_gui.name_var.set("测试字段")
        config_gui.description_var.set("测试描述")
        config_gui.type_var.set("text")
        config_gui.required_var.set(True)
        config_gui.ai_prompt_text.insert(1.0, "测试AI提示词")

        # 检查表单数据
        print(f"   - 待保存字段名: '{config_gui.name_var.get()}'")
        print(f"   - 待保存字段描述: '{config_gui.description_var.get()}'")

        # 模拟保存操作（但不实际保存）
        print("   - 模拟保存操作...")

        # 清理
        config_gui.root.destroy()
        main_root.destroy()

        print("✅ 模拟主GUI启动测试完成")

    except Exception as e:
        print(f"❌ 模拟主GUI启动测试失败: {e}")
        import traceback
        traceback.print_exc()

def simulate_direct_launch():
    """模拟直接启动字段配置管理器"""
    print("\n" + "=" * 60)
    print("模拟场景2: 直接启动字段配置管理器")
    print("=" * 60)

    try:
        print("1. 直接创建字段配置管理器...")
        from field_config_gui import FieldConfigGUI

        # 直接启动，不传递父窗口
        config_gui = FieldConfigGUI(parent_window=None)

        print("2. 检查GUI状态...")
        print(f"   - 父窗口引用: {config_gui.parent_window is not None}")
        print(f"   - 字段列表大小: {config_gui.field_listbox.size()}")

        # 检查第一个字段
        if config_gui.field_listbox.size() > 0:
            first_field = config_gui.field_listbox.get(0)
            print(f"   - 第一个字段: {first_field}")

            # 模拟用户选择字段
            config_gui.field_listbox.selection_set(0)
            config_gui.on_field_select(None)

            print(f"   - 选择后表单字段名: '{config_gui.name_var.get()}'")
            print(f"   - 选择后表单描述: '{config_gui.description_var.get()}'")
            print(f"   - 选择后AI提示词长度: {len(config_gui.ai_prompt_text.get(1.0, tk.END).strip())}")

            # 检查是否为空
            if not config_gui.name_var.get():
                print("   ❌ 问题发现: 字段名称为空！")
            if not config_gui.description_var.get():
                print("   ❌ 问题发现: 字段描述为空！")
            if not config_gui.ai_prompt_text.get(1.0, tk.END).strip():
                print("   ❌ 问题发现: AI提示词为空！")
        else:
            print("   ❌ 问题发现: 字段列表为空！")

        # 清理
        config_gui.root.destroy()

        print("✅ 直接启动测试完成")

    except Exception as e:
        print(f"❌ 直接启动测试失败: {e}")
        import traceback
        traceback.print_exc()

def debug_load_field_to_form():
    """调试load_field_to_form方法"""
    print("\n" + "=" * 60)
    print("调试load_field_to_form方法")
    print("=" * 60)

    try:
        from field_config_gui import FieldConfigGUI
        from field_config import field_config_manager, FieldDefinition

        print("1. 创建GUI实例...")
        config_gui = FieldConfigGUI(parent_window=None)

        print("2. 获取一个测试字段...")
        test_field_name = list(field_config_manager.get_all_fields().keys())[0]
        test_field = field_config_manager.get_field(test_field_name)

        print(f"   - 测试字段: {test_field_name}")
        print(f"   - 字段数据: name='{test_field.name}', description='{test_field.description}', ai_prompt='{test_field.ai_prompt[:50]}...'")

        print("3. 直接调用load_field_to_form...")
        config_gui.load_field_to_form(test_field)

        print("4. 检查表单结果...")
        print(f"   - 表单字段名: '{config_gui.name_var.get()}'")
        print(f"   - 表单字段描述: '{config_gui.description_var.get()}'")
        print(f"   - 表单字段类型: '{config_gui.type_var.get()}'")
        print(f"   - 表单必需状态: {config_gui.required_var.get()}")
        print(f"   - AI提示词文本: '{config_gui.ai_prompt_text.get(1.0, tk.END).strip()[:50]}...'")

        # 检查是否匹配
        if config_gui.name_var.get() != test_field.name:
            print(f"   ❌ 字段名不匹配!")
        if config_gui.description_var.get() != test_field.description:
            print(f"   ❌ 字段描述不匹配!")
        if config_gui.ai_prompt_text.get(1.0, tk.END).strip() != test_field.ai_prompt:
            print(f"   ❌ AI提示词不匹配!")

        print("5. 测试空字段...")
        empty_field = FieldDefinition(
            name="",
            description="",
            field_type="text",
            patterns=[],
            ai_prompt="",
            required=False
        )
        config_gui.load_field_to_form(empty_field)
        print(f"   - 空字段后表单字段名: '{config_gui.name_var.get()}'")

        # 清理
        config_gui.root.destroy()

        print("✅ load_field_to_form调试完成")

    except Exception as e:
        print(f"❌ load_field_to_form调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔍 开始深入调试字段配置管理器GUI问题")

    # 运行三个模拟测试
    simulate_direct_launch()
    simulate_main_gui_launch()
    debug_load_field_to_form()

    print("\n" + "=" * 60)
    print("🎯 问题诊断总结:")
    print("1. 对比直接启动和从主GUI启动的差异")
    print("2. 检查load_field_to_form方法是否正常工作")
    print("3. 分析字段数据加载和表单更新的具体流程")
    print("=" * 60)