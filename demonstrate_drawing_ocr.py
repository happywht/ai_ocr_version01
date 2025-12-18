#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图纸OCR识别演示脚本
展示新的图片优化和图签检测功能
"""

import os
import sys
import logging
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def demonstrate_image_optimization():
    """演示图片优化功能"""
    print("=" * 60)
    print("🖼️  图纸图片优化演示")
    print("=" * 60)

    try:
        from image_optimizer import ImageOptimizer
        optimizer = ImageOptimizer()

        # 查找测试图片
        test_files = []
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                    test_files.append(os.path.join(root, file))

        if not test_files:
            print("⚠️ 没有找到测试图片，请添加图片文件到项目目录")
            return None

        test_image = test_files[0]
        print(f"📁 测试图片: {test_image}")

        # 获取原图信息
        original_info = optimizer.get_image_info(test_image)
        print(f"📏 原图尺寸: {original_info['size']}")
        print(f"💾 原图大小: {original_info['file_size'] / 1024:.1f} KB")

        # 执行图片优化
        print("\n🔄 开始图片优化...")
        optimized_path = optimizer.optimize_image_for_drawing(test_image)

        if optimized_path != test_image:
            print(f"✅ 图片优化成功: {optimized_path}")

            # 获取优化后信息
            optimized_info = optimizer.get_image_info(optimized_path)
            print(f"📏 优化后尺寸: {optimized_info['size']}")
            print(f"💾 优化后大小: {optimized_info['file_size'] / 1024:.1f} KB")

            # 计算压缩比
            compression_ratio = (original_info['file_size'] - optimized_info['file_size']) / original_info['file_size']
            print(f"📊 文件大小减少: {compression_ratio * 100:.1f}%")
        else:
            print("⚠️ 未进行图片优化（可能未检测到图签区域）")

        return optimized_path

    except Exception as e:
        print(f"❌ 图片优化演示失败: {e}")
        return None

def demonstrate_drawing_ocr(image_path):
    """演示图纸OCR识别"""
    print("\n" + "=" * 60)
    print("🔍 图纸OCR识别演示")
    print("=" * 60)

    try:
        from drawing_ocr_tool import DrawingOCRTool

        # 创建OCR工具
        ocr_tool = DrawingOCRTool()

        # 显示配置信息
        print(f"🔧 OCR服务: {ocr_tool.ocr_service_url}")

        if ocr_tool.drawing_config and 'fields' in ocr_tool.drawing_config:
            fields_count = len(ocr_tool.drawing_config['fields'])
            required_fields = [k for k, v in ocr_tool.drawing_config['fields'].items() if v.get('required', False)]

            print(f"📋 配置字段数: {fields_count}")
            print(f"⭐ 必填字段数: {len(required_fields)}")

            # 显示部分字段
            sample_fields = list(ocr_tool.drawing_config['fields'].keys())[:5]
            print(f"🏷️  示例字段: {', '.join(sample_fields)}...")

        # 执行OCR识别
        print(f"\n🎯 开始识别图片: {image_path}")
        start_time = datetime.now()

        result = ocr_tool.process_drawing(image_path)

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        print(f"⏱️  处理时间: {processing_time:.2f}秒")

        # 显示识别结果
        if result:
            print(f"📊 解析方式: {result.get('解析方式', '未知')}")
            print(f"🎯 AI置信度: {result.get('AI置信度', 0):.1%}")
            print(f"📈 OCR状态: {result.get('OCR状态', '未知')}")
            print(f"🤖 AI状态: {result.get('AI状态', '未知')}")

            # 显示处理统计
            if '处理统计' in result:
                stats = result['处理统计']
                print(f"\n📈 处理统计:")
                print(f"   - 图片优化: {'是' if stats.get('图片优化') else '否'}")
                print(f"   - 图签检测: {stats.get('图签检测', '未执行')}")
                print(f"   - 字段数量: {stats.get('字段数量', 0)}")
                print(f"   - 必填字段: {stats.get('必填字段', 0)}")
                print(f"   - 可选字段: {stats.get('可选字段', 0)}")

            # 显示提取的字段
            extracted_fields = result.get('提取字段', {})
            if extracted_fields:
                print(f"\n🎯 提取字段 ({len(extracted_fields)}个):")
                for field_name, field_value in extracted_fields.items():
                    status = "✅" if field_value else "❌"
                    value_display = field_value if field_value else "未识别"
                    print(f"   {field_name}: {value_display} {status}")
            else:
                print("\n⚠️ 未提取到任何字段")

            # 测试导出功能
            export_path = f"drawing_ocr_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            print(f"\n📤 测试Excel导出: {export_path}")

            export_success = ocr_tool.export_drawing_result(result, export_path)
            if export_success and os.path.exists(export_path):
                file_size = os.path.getsize(export_path) / 1024
                print(f"✅ 导出成功 ({file_size:.1f} KB)")
            else:
                print("❌ 导出失败")

            return result
        else:
            print("❌ OCR识别失败，返回空结果")
            return None

    except Exception as e:
        print(f"❌ OCR演示失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主演示函数"""
    print("🚀 图纸OCR识别工具演示")
    print("📅 演示时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("🌟 新功能亮点:")
    print("   • 智能图签区域检测")
    print("   • 图片定向优化裁剪")
    print("   • 专门针对工程图纸设计")
    print("   • 支持动态字段配置")

    # 演示图片优化
    optimized_image = demonstrate_image_optimization()

    # 演示OCR识别
    if optimized_image:
        result = demonstrate_drawing_ocr(optimized_image)
    else:
        # 如果没有优化的图片，使用原图
        test_files = [f for f in os.listdir('.') if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))]
        if test_files:
            result = demonstrate_drawing_ocr(test_files[0])
        else:
            print("⚠️ 没有找到可用于演示的图片文件")

    print("\n" + "=" * 60)
    print("🎉 演示完成！")
    print("💡 提示: 可以将此功能集成到主GUI中，实现图纸专用OCR识别")
    print("=" * 60)

if __name__ == "__main__":
    main()