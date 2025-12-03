#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF处理流程测试脚本
测试PDF文件从预览到识别的完整流程
"""

import sys
import os

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

def test_pdf_api_fix():
    """测试pypdfium2 API修复"""
    print("=" * 50)
    print("pypdfium2 API修复验证")
    print("=" * 50)

    try:
        import pypdfium2 as pdfium
        print("✅ pypdfium2导入成功")

        # 检查新的API
        if hasattr(pdfium, 'PdfColorScheme'):
            print("✅ PdfColorScheme API可用")
            print(f"   可用颜色方案: {dir(pdfium.PdfColorScheme)}")
        else:
            print("❌ PdfColorScheme API不可用")
            return False

        return True
    except Exception as e:
        print(f"❌ pypdfium2测试失败: {e}")
        return False

def test_pdf_rendering():
    """测试PDF渲染功能"""
    print("\n" + "=" * 50)
    print("PDF渲染功能测试")
    print("=" * 50)

    # 查找PDF文件
    pdf_files = [f for f in os.listdir('.') if f.lower().endswith('.pdf')]
    if not pdf_files:
        print("⚠️ 未找到PDF测试文件")
        return True  # 没有PDF文件不算失败

    try:
        import pypdfium2 as pdfium
        from PIL import Image

        for pdf_file in pdf_files[:1]:  # 只测试第一个
            print(f"\n测试文件: {pdf_file}")

            # 1. 测试预览分辨率渲染
            print("1. 测试预览分辨率渲染...")
            try:
                pdf = pdfium.PdfDocument(pdf_file)
                page = pdf[0]
                bitmap = page.render(
                    scale=0.8,
                    color_scheme=pdfium.PdfColorScheme.rgb,
                )
                image = bitmap.to_pil()
                print(f"   ✅ 预览渲染成功，尺寸: {image.size}")

                # 清理资源
                bitmap = None
                page = None
                pdf.close()
            except Exception as e:
                print(f"   ❌ 预览渲染失败: {e}")
                return False

            # 2. 测试OCR分辨率渲染
            print("2. 测试OCR分辨率渲染...")
            try:
                pdf = pdfium.PdfDocument(pdf_file)
                page = pdf[0]
                bitmap = page.render(
                    scale=2.0,
                    color_scheme=pdfium.PdfColorScheme.rgb,
                    crop=(0, 0, 0, 0),
                )
                image = bitmap.to_pil()
                print(f"   ✅ OCR渲染成功，尺寸: {image.size}")

                # 清理资源
                bitmap = None
                page = None
                pdf.close()
            except Exception as e:
                print(f"   ❌ OCR渲染失败: {e}")
                return False

        return True
    except Exception as e:
        print(f"❌ PDF渲染测试失败: {e}")
        return False

def test_ocr_pdf_workflow():
    """测试OCR工具处理PDF的完整流程"""
    print("\n" + "=" * 50)
    print("OCR工具PDF处理流程测试")
    print("=" * 50)

    try:
        from invoice_ocr_tool import InvoiceOCRTool

        # 初始化OCR工具（不启用AI，专注测试PDF处理）
        ocr_tool = InvoiceOCRTool(use_ai=False)
        print("✅ OCR工具初始化成功")

        # 查找PDF文件
        pdf_files = [f for f in os.listdir('.') if f.lower().endswith('.pdf')]
        if not pdf_files:
            print("⚠️ 未找到PDF测试文件，跳过OCR流程测试")
            return True

        # 测试第一个PDF文件
        pdf_file = pdf_files[0]
        print(f"\n测试OCR处理: {pdf_file}")

        # 1. 测试PDF图片识别
        print("1. 测试PDF图片识别...")
        ocr_result = ocr_tool.recognize_image(pdf_file)
        if ocr_result:
            print("   ✅ PDF图片识别成功")
            print(f"   OCR状态码: {ocr_result.get('code', 'N/A')}")
            if 'data' in ocr_result:
                data = ocr_result['data']
                if isinstance(data, str):
                    print(f"   识别文本长度: {len(data)} 字符")
                elif isinstance(data, list):
                    print(f"   识别文本块数: {len(data)}")
        else:
            print("   ❌ PDF图片识别失败")
            return False

        # 2. 测试完整PDF处理流程
        print("2. 测试完整PDF处理流程...")
        result = ocr_tool.process_invoice(pdf_file)
        if result:
            print("   ✅ PDF处理流程成功")
            print(f"   解析方式: {result.get('解析方式', '未知')}")
            print(f"   提取字段数: {len([v for v in result.get('提取字段', {}).values() if v])}")
        else:
            print("   ❌ PDF处理流程失败")
            return False

        return True
    except Exception as e:
        print(f"❌ OCR流程测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("PDF处理完整流程验证")
    print("=" * 60)

    # 1. API修复验证
    if not test_pdf_api_fix():
        print("❌ API修复验证失败")
        return

    # 2. PDF渲染测试
    if not test_pdf_rendering():
        print("❌ PDF渲染测试失败")
        return

    # 3. OCR流程测试
    if not test_ocr_pdf_workflow():
        print("❌ OCR流程测试失败")
        return

    print("\n" + "=" * 60)
    print("🎉 PDF处理流程验证全部通过！")
    print("现在PDF文件应该可以正常预览和识别了")
    print("=" * 60)

if __name__ == "__main__":
    main()