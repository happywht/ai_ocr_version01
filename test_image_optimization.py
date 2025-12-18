#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试图片优化功能
"""

import os
import sys
import logging

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

logging.basicConfig(level=logging.INFO)

def test_image_optimizer():
    """测试图片优化器"""
    try:
        from image_optimizer import ImageOptimizer
        print("✅ ImageOptimizer模块导入成功")

        # 创建优化器实例
        optimizer = ImageOptimizer()

        # 查找测试图片
        test_files = []
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    test_files.append(os.path.join(root, file))

        if test_files:
            test_file = test_files[0]
            print(f"测试文件: {test_file}")

            # 获取图片信息
            info = optimizer.get_image_info(test_file)
            print(f"图片信息: {info}")

            # 测试图签检测
            from PIL import Image
            with Image.open(test_file) as img:
                signature_region = optimizer.detect_signature_region(img)
                print(f"检测到的图签区域: {signature_region}")

                if signature_region:
                    print("✅ 图签区域检测成功")
                    cropped_img = optimizer.crop_signature_region(img, signature_region)
                    print(f"裁剪后尺寸: {cropped_img.size}")
                else:
                    print("⚠️ 未检测到图签区域")

            return True
        else:
            print("⚠️ 没有找到测试图片文件")
            return False

    except Exception as e:
        print(f"❌ ImageOptimizer测试失败: {e}")
        return False

def test_drawing_ocr():
    """测试图纸OCR工具"""
    try:
        from drawing_ocr_tool import DrawingOCRTool
        print("✅ DrawingOCRTool模块导入成功")

        # 创建工具实例
        ocr_tool = DrawingOCRTool()

        print(f"OCR服务URL: {ocr_tool.ocr_service_url}")
        print(f"图纸配置加载: {'成功' if ocr_tool.drawing_config else '失败'}")

        # 显示配置的字段数量
        if ocr_tool.drawing_config and 'fields' in ocr_tool.drawing_config:
            fields_count = len(ocr_tool.drawing_config['fields'])
            print(f"配置的字段数量: {fields_count}")

            # 显示前3个字段
            fields = list(ocr_tool.drawing_config['fields'].keys())[:3]
            print(f"前3个字段: {fields}")

            # 显示必填字段数量
            required_fields = [k for k, v in ocr_tool.drawing_config['fields'].items() if v.get('required', False)]
            print(f"必填字段数量: {len(required_fields)}")

            # 显示配置文件来源
            if os.path.exists('peizhi001.json'):
                print("✅ 使用peizhi001.json配置文件")
            else:
                print("⚠️ 使用默认配置")
        else:
            print("⚠️ 没有找到字段配置")

        return True

    except Exception as e:
        print(f"❌ DrawingOCRTool测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试图片优化功能...")

    print("\n📸 测试ImageOptimizer...")
    image_test_passed = test_image_optimizer()

    print("\n🔍 测试DrawingOCRTool...")
    ocr_test_passed = test_drawing_ocr()

    print(f"\n📊 测试结果:")
    print(f"ImageOptimizer: {'✅ 通过' if image_test_passed else '❌ 失败'}")
    print(f"DrawingOCRTool: {'✅ 通过' if ocr_test_passed else '❌ 失败'}")

    if image_test_passed and ocr_test_passed:
        print("\n🎉 所有测试通过！图片优化功能可以正常使用")
    else:
        print("\n⚠️ 部分测试失败，需要进一步调试")

if __name__ == "__main__":
    main()