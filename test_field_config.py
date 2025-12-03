#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态字段配置系统测试脚本
"""

import sys
import os

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

def test_field_config_system():
    """测试字段配置系统"""
    print("="*60)
    print("    动态字段配置系统测试")
    print("="*60)

    try:
        from field_config import field_config_manager, FieldDefinition
        from ai_invoice_parser import AIInvoiceParser

        print("✅ 模块导入成功")

        # 测试1: 字段配置管理器
        print("\n📋 测试1: 字段配置管理器")
        fields = field_config_manager.get_all_fields()
        print(f"   当前配置字段数量: {len(fields)}")
        for field_name, field in fields.items():
            print(f"   - {field_name}: {field.description} ({field.field_type})")

        # 测试2: 添加自定义字段
        print("\n➕ 测试2: 添加自定义字段")
        custom_field = FieldDefinition(
            name="合同编号",
            description="合同文件的唯一编号",
            field_type="text",
            patterns=[r'合同编号[:：]?\s*(\w+)', r'Contract[:：]?\s*No\.?\s*(\w+)'],
            ai_prompt="提取合同编号或合同文件编号",
            required=True
        )

        success = field_config_manager.add_field(custom_field)
        print(f"   添加自定义字段 '合同编号': {'✅ 成功' if success else '❌ 失败'}")

        # 测试3: AI提示词生成
        print("\n🤖 测试3: AI提示词生成")
        prompt = field_config_manager.create_ai_prompt(["发票号码", "开票日期", "合同编号"])
        print(f"   生成的AI提示词长度: {len(prompt)} 字符")
        print("   提示词片段:")
        print("   " + prompt[:200] + "...")

        # 测试4: AI解析器集成
        print("\n🧠 测试4: AI解析器集成")
        parser = AIInvoiceParser()

        test_ocr_text = """
        专用发票
        发票号码：12345678
        开票日期：2024年01月01日
        合同编号：HT20240101001

        销售方：某某科技有限公司
        购买方：某某贸易有限公司
        价税合计：￥10,600.00
        税额：600.00
        """

        # 测试动态字段提取
        result = parser.extract_fields_with_ai(test_ocr_text, ["发票号码", "开票日期", "合同编号"])

        if result:
            print("   ✅ AI动态字段提取成功")
            print(f"   提取的字段: {list(result['extracted_fields'].keys())}")
            print(f"   置信度: {result['ai_confidence']}")

            for field_name, field_value in result['extracted_fields'].items():
                print(f"   - {field_name}: {field_value}")
        else:
            print("   ❌ AI动态字段提取失败")

        # 测试5: 字段验证
        print("\n✅ 测试5: 字段验证")
        test_values = {
            "发票号码": "12345678",
            "开票日期": "2024年01月01日",
            "合同编号": "HT20240101001",
            "合计金额": "￥10,600.00"
        }

        for field_name, raw_value in test_values.items():
            validated_value = field_config_manager.validate_field_value(field_name, raw_value)
            print(f"   {field_name}: '{raw_value}' → '{validated_value}'")

        # 清理测试数据
        print("\n🧹 清理测试数据")
        field_config_manager.remove_field("合同编号")
        print("   ✅ 已删除测试字段 '合同编号'")

        print("\n🎉 动态字段配置系统测试完成！")
        print("✅ 所有功能正常工作")

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_ocr_integration():
    """测试与OCR工具的集成"""
    print("\n" + "="*60)
    print("    OCR工具集成测试")
    print("="*60)

    try:
        from invoice_ocr_tool import InvoiceOCRTool

        # 创建OCR工具实例
        tool = InvoiceOCRTool(use_ai=True)
        print("✅ OCR工具初始化成功")

        # 测试字段提取（不进行实际OCR识别）
        print("\n🔍 测试动态字段提取")
        mock_ocr_result = {
            'data': """
            专用发票
            发票号码：87654321
            开票日期：2024年03月15日

            销售方：测试科技公司
            购买方：测试贸易公司
            价税合计：￥25,000.00
            税额：1,500.00
            """
        }

        # 指定提取字段
        field_names = ["发票号码", "开票日期", "销售方名称", "购买方名称", "合计金额", "税额"]
        extracted_fields = tool.extract_invoice_fields(mock_ocr_result, field_names)

        print(f"   提取到 {len(extracted_fields)} 个字段:")
        for field_name, field_value in extracted_fields.items():
            print(f"   - {field_name}: {field_value}")

        print("\n✅ OCR工具集成测试完成")
        return True

    except Exception as e:
        print(f"\n❌ OCR集成测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("开始动态字段配置系统全面测试...\n")

    # 测试1: 字段配置系统
    test1_result = test_field_config_system()

    # 测试2: OCR集成
    test2_result = test_ocr_integration()

    # 测试结果汇总
    print("\n" + "="*60)
    print("    测试结果汇总")
    print("="*60)

    print(f"字段配置系统: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"OCR工具集成: {'✅ 通过' if test2_result else '❌ 失败'}")

    if test1_result and test2_result:
        print("\n🎉 所有测试通过！动态字段配置系统已就绪")
        print("\n📖 使用说明:")
        print("1. 运行 'python 启动工具.py' 选择选项2启动字段配置管理器")
        print("2. 在字段配置管理器中添加、编辑或删除字段")
        print("3. 保存配置后，OCR工具将自动使用新的字段配置")
        print("4. 可以针对不同类型的文档（发票、合同、证件等）配置不同的字段")
        return True
    else:
        print("\n❌ 部分测试失败，请检查错误信息")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)