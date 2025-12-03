#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI解析调试脚本
检查AI解析过程中的每一步，找出问题所在
"""

import sys
import os

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

def debug_ai_parsing():
    """调试AI解析过程"""
    print("="*60)
    print("    AI解析过程调试")
    print("="*60)

    try:
        from ai_invoice_parser import AIInvoiceParser

        print("✅ AI解析器导入成功")

        # 创建AI解析器实例
        parser = AIInvoiceParser()
        print("✅ AI解析器初始化成功")

        # 模拟真实的OCR文本
        test_ocr_text = """
        增值税专用发票

        发票号码：1100224150
        开票日期：2024年01月15日
        校验码：12345678901234567890

        购买方信息
        名称：北京示例科技有限公司
        纳税人识别号：91110108MA01234567
        地址、电话：北京市海淀区测试路123号 010-12345678
        开户行及账号：工商银行海淀支行 6222021234567890123

        货物或应税劳务、服务名称
        *信息技术服务*软件开发服务
        规格型号：V1.0
        单位：项
        数量：1
        单价：9433.96
        金额：9433.96
        税率：13%
        税额：1226.41
        价税合计：10660.37

        销售方信息
        名称：上海技术服务有限公司
        纳税人识别号：91310120MA98765432
        地址、电话：上海市浦东新区开发路456号 021-87654321
        开户行及账号：建设银行浦东支行 6217009876543210987

        备注：软件开发项目第一期款项
        """

        print(f"\n📝 原始OCR文本长度: {len(test_ocr_text)} 字符")
        print("原始OCR文本内容（前200字符）:")
        print(test_ocr_text[:200] + "...")

        # 步骤1: 生成AI提示词
        print("\n🤖 步骤1: 生成AI提示词")
        prompt = parser.create_extraction_prompt(test_ocr_text)
        print(f"提示词长度: {len(prompt)} 字符")
        print("提示词内容（前500字符）:")
        print(prompt[:500] + "...")
        print("提示词内容（包含OCR文本部分）:")

        # 查找OCR文本在提示词中的位置
        ocr_start = prompt.find("# OCR识别文本")
        if ocr_start != -1:
            print("提示词中的OCR部分:")
            print(prompt[ocr_start:ocr_start+300] + "...")
        else:
            print("❌ 未找到OCR文本在提示词中的位置!")

        # 步骤2: 调用AI API
        print("\n🔗 步骤2: 调用AI API")
        try:
            # 手动调用API并打印详细信息
            print("正在发送请求到AI服务...")

            response = parser.client.messages.create(
                model=parser.model,
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1
            )

            print("✅ API调用成功")
            print(f"响应类型: {type(response)}")
            print(f"响应内容长度: {len(response.content) if hasattr(response, 'content') else 'N/A'}")

            if hasattr(response, 'content') and response.content:
                ai_response = response.content[0].text.strip()
                print(f"AI原始响应长度: {len(ai_response)} 字符")
                print("AI原始响应内容:")
                print(ai_response)

                # 步骤3: 解析AI响应
                print("\n📊 步骤3: 解析AI响应")
                parsed_result = parser.parse_ai_response(ai_response)
                print("解析后的结果:")
                for key, value in parsed_result.items():
                    print(f"  {key}: {value}")

                # 步骤4: 验证和清理字段
                print("\n✅ 步骤4: 验证和清理字段")
                try:
                    from field_config import field_config_manager
                    validated_fields = {}
                    for field_name, field_value in parsed_result.items():
                        validated_value = field_config_manager.validate_field_value(field_name, field_value)
                        validated_fields[field_name] = validated_value
                        print(f"  {field_name}: '{field_value}' → '{validated_value}'")
                except Exception as e:
                    print(f"  字段验证失败: {e}")
                    validated_fields = parsed_result

                return {
                    'prompt': prompt,
                    'ai_response': ai_response,
                    'parsed_result': parsed_result,
                    'validated_fields': validated_fields
                }

            else:
                print("❌ AI响应为空")
                return None

        except Exception as api_error:
            print(f"❌ API调用失败: {api_error}")
            import traceback
            traceback.print_exc()
            return None

    except Exception as e:
        print(f"❌ 调试过程失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def compare_with_expected(actual_result):
    """对比实际结果与预期结果"""
    print("\n" + "="*60)
    print("    结果对比分析")
    print("="*60)

    expected_patterns = {
        "发票号码": r"1100224150",
        "开票日期": r"2024.*01.*15",
        "销售方名称": r"上海技术服务有限公司",
        "购买方名称": r"北京示例科技有限公司",
        "合计金额": r"10660\.37",
        "税额": r"1226\.41"
    }

    print("预期结果 vs 实际结果:")
    print("-" * 50)

    if actual_result and 'validated_fields' in actual_result:
        actual_fields = actual_result['validated_fields']

        for field_name, expected_pattern in expected_patterns.items():
            actual_value = actual_fields.get(field_name, "未找到")

            import re
            match = re.search(expected_pattern, str(actual_value)) if actual_value != "未找到" else False

            status = "✅ 正确" if match else "❌ 错误"
            print(f"{field_name:12}: 预期模式=[{expected_pattern}] 实际值=[{actual_value}] {status}")

        # 检查是否有意外字段
        print(f"\n字段数量检查:")
        print(f"  预期字段数: {len(expected_patterns)}")
        print(f"  实际字段数: {len(actual_fields)}")

        unexpected_fields = set(actual_fields.keys()) - set(expected_patterns.keys())
        if unexpected_fields:
            print(f"  意外字段: {list(unexpected_fields)}")

        missing_fields = set(expected_patterns.keys()) - set(actual_fields.keys())
        if missing_fields:
            print(f"  缺失字段: {list(missing_fields)}")
    else:
        print("❌ 没有有效的实际结果可供对比")


def main():
    """主调试函数"""
    print("开始AI解析调试...\n")

    # 执行调试
    debug_result = debug_ai_parsing()

    # 对比结果
    if debug_result:
        compare_with_expected(debug_result)

        print(f"\n📋 调试总结:")
        print(f"  AI提示词生成: ✅ 正常")
        print(f"  API调用: ✅ 成功")
        print(f"  响应解析: ✅ 正常")
        print(f"  数据准确性: ❌ 需要检查")
        print(f"\n💡 建议:")
        print(f"  1. 检查AI模型是否正确处理OCR文本")
        print(f"  2. 验证提示词是否包含完整的OCR内容")
        print(f"  3. 确认AI响应是否基于实际内容而非模板")
    else:
        print(f"\n❌ 调试失败，无法获取完整结果")


if __name__ == "__main__":
    main()