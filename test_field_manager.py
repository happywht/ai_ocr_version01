#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试字段管理器的独立功能
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_field_config_basic():
    """测试字段配置基本功能"""
    print("=== 测试字段配置基本功能 ===")

    try:
        from field_config import field_config_manager

        # 测试获取字段
        fields = field_config_manager.get_all_fields()
        print(f"✅ 当前共有 {len(fields)} 个字段配置")

        # 显示字段列表
        for field_name, field_def in fields.items():
            status = "必需" if field_def.required else "可选"
            print(f"  - {field_name}: {field_def.description} ({status})")

        # 测试新增字段
        print("\n=== 测试新增字段 ===")
        from field_config import FieldDefinition

        test_field = FieldDefinition(
            name="测试字段",
            description="这是一个测试字段",
            field_type="text",
            patterns=[r'测试[:：]\s*(.+)'],
            ai_prompt="提取测试信息",
            required=False
        )

        if field_config_manager.add_field(test_field):
            print("✅ 新增字段成功")
        else:
            print("❌ 新增字段失败")

        # 保存配置
        if field_config_manager.save_config():
            print("✅ 配置保存成功")
        else:
            print("❌ 配置保存失败")

        # 删除测试字段
        if field_config_manager.remove_field("测试字段"):
            print("✅ 删除测试字段成功")
        else:
            print("❌ 删除测试字段失败")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_field_config_gui():
    """测试字段配置GUI"""
    print("\n=== 测试字段配置GUI ===")

    try:
        from field_config_gui import FieldConfigGUI
        import tkinter as tk

        # 创建测试根窗口（但不显示）
        test_root = tk.Tk()
        test_root.withdraw()  # 隐藏测试窗口

        # 创建字段配置GUI实例
        config_gui = FieldConfigGUI(parent_window=test_root)

        print("✅ 字段配置GUI创建成功")

        # 销毁测试窗口
        test_root.destroy()

        return True

    except Exception as e:
        print(f"❌ GUI测试失败: {str(e)}")
        return False

def test_field_config_persistence():
    """测试字段配置持久化"""
    print("\n=== 测试字段配置持久化 ===")

    try:
        from field_config import FieldConfigManager
        import tempfile
        import json

        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            temp_config_path = f.name

        # 创建临时配置管理器
        temp_manager = FieldConfigManager(config_path=temp_config_path)

        # 添加测试字段
        from field_config import FieldDefinition
        test_field = FieldDefinition(
            name="持久化测试",
            description="测试持久化功能",
            field_type="text",
            patterns=[r'测试[:：]\s*(.+)'],
            ai_prompt="提取测试信息",
            required=True
        )

        temp_manager.add_field(test_field)

        # 保存配置
        if temp_manager.save_config():
            print("✅ 配置保存成功")
        else:
            print("❌ 配置保存失败")
            return False

        # 重新加载配置
        new_manager = FieldConfigManager(config_path=temp_config_path)

        # 验证字段是否存在
        loaded_field = new_manager.get_field("持久化测试")
        if loaded_field and loaded_field.description == "测试持久化功能":
            print("✅ 配置持久化测试成功")
        else:
            print("❌ 配置持久化测试失败")
            return False

        # 清理临时文件
        os.unlink(temp_config_path)

        return True

    except Exception as e:
        print(f"❌ 持久化测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试字段管理器功能...")

    success_count = 0
    total_tests = 3

    # 基本功能测试
    if test_field_config_basic():
        success_count += 1

    # GUI测试
    if test_field_config_gui():
        success_count += 1

    # 持久化测试
    if test_field_config_persistence():
        success_count += 1

    print(f"\n=== 测试完成 ===")
    print(f"✅ 成功: {success_count}/{total_tests} 项测试")

    if success_count == total_tests:
        print("🎉 所有测试通过！字段管理器功能正常")
        return True
    else:
        print("⚠️ 部分测试失败，请检查相关功能")
        return False

if __name__ == "__main__":
    main()