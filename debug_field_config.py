#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试字段配置管理器GUI问题
测试直接启动和从主GUI启动的差异
"""

import sys
import os
import logging

# 添加src目录到路径
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

def test_direct_launch():
    """测试直接启动字段配置管理器"""
    print("=" * 50)
    print("测试1: 直接启动字段配置管理器")
    print("=" * 50)

    try:
        # 导入字段配置管理器
        from field_config_gui import FieldConfigGUI
        from field_config import field_config_manager

        print(f"✅ 导入成功")
        print(f"📋 配置管理器路径: {field_config_manager.config_path}")
        print(f"📋 配置文件是否存在: {os.path.exists(field_config_manager.config_path)}")
        print(f"📋 当前字段数量: {len(field_config_manager.get_all_fields())}")

        # 检查字段数据
        fields = field_config_manager.get_all_fields()
        if fields:
            first_field_name = list(fields.keys())[0]
            first_field = fields[first_field_name]
            print(f"📋 第一个字段示例:")
            print(f"   - 名称: {first_field.name}")
            print(f"   - 描述: {first_field.description}")
            print(f"   - 类型: {first_field.field_type}")
            print(f"   - AI提示词: {first_field.ai_prompt[:50]}...")
            print(f"   - 正则模式数量: {len(first_field.patterns)}")
        else:
            print("⚠️ 没有找到字段配置")

        # 创建GUI实例（但不运行mainloop）
        app = FieldConfigGUI()
        print("✅ GUI实例创建成功")

        # 检查GUI加载的字段
        loaded_fields = []
        for i in range(app.field_listbox.size()):
            loaded_fields.append(app.field_listbox.get(i))

        print(f"📋 GUI加载的字段数量: {len(loaded_fields)}")
        print(f"📋 GUI字段列表: {loaded_fields[:3]}...")  # 只显示前3个

        # 尝试选择第一个字段
        if loaded_fields:
            app.field_listbox.selection_set(0)
            app.on_field_select(None)
            print(f"✅ 字段选择成功")
            print(f"📋 表单中的字段名称: {app.name_var.get()}")
            print(f"📋 表单中的字段描述: {app.description_var.get()}")

        app.root.destroy()  # 清理GUI实例
        print("✅ 直接启动测试完成")

    except Exception as e:
        print(f"❌ 直接启动测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_import_from_main_gui():
    """测试从主GUI导入（模拟主GUI环境）"""
    print("\n" + "=" * 50)
    print("测试2: 模拟从主GUI导入")
    print("=" * 50)

    try:
        # 模拟主GUI的工作目录环境
        print(f"📋 当前工作目录: {os.getcwd()}")
        print(f"📋 Python路径: {sys.path[:3]}...")  # 显示前3个路径

        # 导入主GUI模块（这会改变导入环境）
        import invoice_gui
        print("✅ 主GUI模块导入成功")

        # 现在导入字段配置管理器（模拟主GUI中的导入）
        from field_config_gui import FieldConfigGUI
        from field_config import field_config_manager

        print(f"✅ 从主GUI环境导入字段配置管理器成功")
        print(f"📋 配置管理器路径: {field_config_manager.config_path}")
        print(f"📋 配置文件是否存在: {os.path.exists(field_config_manager.config_path)}")
        print(f"📋 当前字段数量: {len(field_config_manager.get_all_fields())}")

        # 创建带父窗口的GUI实例（模拟从主GUI启动）
        app = FieldConfigGUI(parent_window=None)  # 这里传入None，因为我们的测试环境
        print("✅ 带父窗口的GUI实例创建成功")

        # 检查加载的字段
        loaded_fields = []
        for i in range(app.field_listbox.size()):
            loaded_fields.append(app.field_listbox.get(i))

        print(f"📋 GUI加载的字段数量: {len(loaded_fields)}")

        app.root.destroy()  # 清理GUI实例
        print("✅ 从主GUI导入测试完成")

    except Exception as e:
        print(f"❌ 从主GUI导入测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_field_config_manager_state():
    """测试字段配置管理器的状态"""
    print("\n" + "=" * 50)
    print("测试3: 字段配置管理器状态分析")
    print("=" * 50)

    try:
        from field_config import FieldConfigManager, field_config_manager

        print(f"📋 全局管理器ID: {id(field_config_manager)}")
        print(f"📋 全局管理器字段数: {len(field_config_manager.get_all_fields())}")

        # 创建新的管理器实例
        new_manager = FieldConfigManager()
        print(f"📋 新管理器ID: {id(new_manager)}")
        print(f"📋 新管理器字段数: {len(new_manager.get_all_fields())}")

        # 检查是否是同一个实例
        print(f"📋 是否为同一实例: {field_config_manager is new_manager}")

        # 检查配置文件路径
        print(f"📋 全局管理器配置路径: {field_config_manager.config_path}")
        print(f"📋 新管理器配置路径: {new_manager.config_path}")
        print(f"📋 路径是否相同: {field_config_manager.config_path == new_manager.config_path}")

        print("✅ 状态分析完成")

    except Exception as e:
        print(f"❌ 状态分析失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("🔍 开始调试字段配置管理器GUI问题")

    # 运行三个测试
    test_direct_launch()
    test_import_from_main_gui()
    test_field_config_manager_state()

    print("\n" + "=" * 50)
    print("🎯 调试总结:")
    print("1. 检查直接启动和从主GUI启动的配置加载是否一致")
    print("2. 检查字段配置管理器的实例化和状态")
    print("3. 检查GUI组件的字段加载机制")
    print("=" * 50)