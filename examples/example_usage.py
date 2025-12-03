#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用示例：演示如何使用发票OCR识别工具
"""

import os
import sys
from invoice_ocr_tool import InvoiceOCRTool

def example_basic_usage():
    """基本使用示例"""
    # 创建OCR工具实例
    ocr_tool = InvoiceOCRTool()

    # 测试连接
    if not ocr_tool.test_ocr_connection():
        print("无法连接到OCR服务，请确保服务已启动")
        return

    # 处理发票图片（需要准备一张发票图片）
    image_path = "example_invoice.jpg"  # 替换为实际的发票图片路径

    if not os.path.exists(image_path):
        print(f"示例图片不存在: {image_path}")
        print("请准备一张发票图片并替换该路径")
        return

    # 处理发票
    result = ocr_tool.process_invoice(image_path, "json")

    if result:
        # 显示结果
        print("=== 发票识别结果 ===")
        extracted_fields = result.get('提取字段', {})

        for key, value in extracted_fields.items():
            print(f"{key}: {value}")

        # 保存结果
        output_path = "invoice_result.json"
        ocr_tool.save_result(result, output_path, "json")
        print(f"\n结果已保存到: {output_path}")
    else:
        print("发票识别失败")

def example_batch_processing():
    """批量处理示例"""
    ocr_tool = InvoiceOCRTool()

    # 图片目录
    image_dir = "invoices"  # 包含多个发票图片的目录

    if not os.path.exists(image_dir):
        print(f"图片目录不存在: {image_dir}")
        return

    # 获取所有图片文件
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    image_files = [
        f for f in os.listdir(image_dir)
        if any(f.lower().endswith(ext) for ext in image_extensions)
    ]

    if not image_files:
        print("目录中没有找到图片文件")
        return

    print(f"找到 {len(image_files)} 个图片文件")

    # 批量处理
    results = []
    for image_file in image_files:
        image_path = os.path.join(image_dir, image_file)
        print(f"\n处理: {image_file}")

        result = ocr_tool.process_invoice(image_path)
        if result:
            results.append(result)
            print("✅ 处理成功")
        else:
            print("❌ 处理失败")

    # 保存批量结果
    if results:
        import json
        batch_result = {
            '处理时间': results[0]['处理时间'],
            '处理总数': len(image_files),
            '成功数量': len(results),
            '失败数量': len(image_files) - len(results),
            '识别结果': results
        }

        with open("batch_results.json", 'w', encoding='utf-8') as f:
            json.dump(batch_result, f, ensure_ascii=False, indent=2)

        print(f"\n批量处理完成，结果已保存到: batch_results.json")
        print(f"成功: {len(results)}/{len(image_files)}")

def example_custom_extraction():
    """自定义字段提取示例"""
    ocr_tool = InvoiceOCRTool()

    image_path = "example_invoice.jpg"
    if not os.path.exists(image_path):
        print(f"示例图片不存在: {image_path}")
        return

    # 获取OCR原始结果
    ocr_result = ocr_tool.recognize_image(image_path)
    if ocr_result:
        # 使用自定义逻辑提取字段
        extracted = ocr_tool.extract_invoice_fields(ocr_result)

        # 添加自定义字段处理
        print("=== 自定义字段提取结果 ===")
        for field, value in extracted.items():
            print(f"{field}: {value}")

        # 可以在这里添加更多的自定义处理逻辑
        # 例如：验证税额计算、格式化日期等

if __name__ == "__main__":
    print("=== 发票OCR工具使用示例 ===\n")

    print("1. 基本使用示例")
    print("2. 批量处理示例")
    print("3. 自定义字段提取示例")

    choice = input("\n请选择要运行的示例 (1-3): ")

    if choice == "1":
        example_basic_usage()
    elif choice == "2":
        example_batch_processing()
    elif choice == "3":
        example_custom_extraction()
    else:
        print("无效选择")
        sys.exit(1)