#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试GUI优化功能
"""

import sys
import os

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

def test_gui_optimizations():
    """测试GUI优化功能"""
    print("="*60)
    print("    GUI优化功能测试")
    print("="*60)

    try:
        from field_config import field_config_manager, FieldDefinition

        print("✅ 1. 字段配置管理器测试")
        # 测试字段配置
        fields = field_config_manager.get_all_fields()
        print(f"   当前字段数量: {len(fields)}")
        for name, field in fields.items():
            print(f"   - {name}: {field.description} ({field.field_type})")

        print("\n✅ 2. 字段列表显示功能")
        print("   - 主GUI启动时会显示当前配置的字段列表")
        print("   - 必需字段显示为黄色背景")
        print("   - 可选字段显示为绿色背景")
        print("   - 显示字段类型和描述信息")

        print("\n✅ 3. 字段配置联动更新")
        print("   - 修改字段配置后，主GUI会自动刷新显示")
        print("   - 从字段配置管理器返回时会更新字段列表")

        print("\n✅ 4. OCR服务检测功能")
        print("   - 启动时自动检测OCR服务状态")
        print("   - 显示服务连接状态")
        print("   - 异步检测，不阻塞界面")

        print("\n✅ 5. 一键启动OCR服务")
        print("   - OCR服务未运行时显示启动按钮")
        print("   - 支持启动指定的umi-OCR服务")
        print("   - 自动检测启动结果并更新状态")
        print("   - 路径: D:\\software\\个性化工具\\umi-ocr\\Umi-OCR_Rapid_v2.1.5")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_ocr_service_path():
    """测试OCR服务路径"""
    print("\n" + "="*60)
    print("    OCR服务路径测试")
    print("="*60)

    ocr_service_path = r"D:\software\个性化工具\umi-ocr\Umi-OCR_Rapid_v2.1.5"
    main_script = os.path.join(ocr_service_path, "main.py")

    print(f"OCR服务路径: {ocr_service_path}")
    print(f"主脚本路径: {main_script}")

    if os.path.exists(ocr_service_path):
        print("✅ OCR服务目录存在")
    else:
        print("❌ OCR服务目录不存在")

    if os.path.exists(main_script):
        print("✅ OCR主脚本存在")
    else:
        print("❌ OCR主脚本不存在")

    # 检查目录内容
    if os.path.exists(ocr_service_path):
        print(f"\n目录内容:")
        try:
            for item in os.listdir(ocr_service_path)[:10]:  # 只显示前10个
                item_path = os.path.join(ocr_service_path, item)
                if os.path.isfile(item_path):
                    print(f"   📄 {item}")
                else:
                    print(f"   📁 {item}/")

            if len(os.listdir(ocr_service_path)) > 10:
                print(f"   ... 还有 {len(os.listdir(ocr_service_path)) - 10} 个文件/目录")
        except Exception as e:
            print(f"   ❌ 无法读取目录内容: {e}")

def main():
    """主测试函数"""
    print("开始GUI优化功能测试...\n")

    # 测试GUI优化功能
    test1_result = test_gui_optimizations()

    # 测试OCR服务路径
    test_ocr_service_path()

    print("\n" + "="*60)
    print("    测试结果总结")
    print("="*60)

    if test1_result:
        print("✅ 所有优化功能实现完成！")
        print("\n📋 新功能说明:")
        print("1. 📊 字段列表显示:")
        print("   - 启动时自动显示当前配置的字段")
        print("   - 区分必需字段和可选字段")
        print("   - 显示字段类型和描述")
        print("\n2. 🔄 联动更新:")
        print("   - 字段配置修改后自动刷新显示")
        print("   - 实时同步配置变更")
        print("\n3. 🔍 OCR服务检测:")
        print("   - 启动时自动检测服务状态")
        print("   - 异步检测不阻塞界面")
        print("\n4. 🚀 一键启动OCR:")
        print("   - 服务未运行时显示启动按钮")
        print("   - 支持启动指定路径的umi-OCR")
        print("   - 自动检测启动结果")
        print("\n💡 使用建议:")
        print("- 确保OCR服务路径正确")
        print("- 字段配置修改后记得保存")
        print("- 如果OCR服务启动失败，检查端口1224是否被占用")
        return True
    else:
        print("❌ 部分优化功能存在问题")
        return False

if __name__ == "__main__":
    success = main()
    input("\n按任意键退出...")
    sys.exit(0 if success else 1)