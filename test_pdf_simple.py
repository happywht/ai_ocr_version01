#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF简化处理测试
使用最基本的pypdfium2 API调用
"""

import sys
import os

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

def test_pdf_basic():
    """测试PDF基本处理"""
    print("=" * 50)
    print("PDF基本处理测试")
    print("=" * 50)

    # 查找PDF文件
    pdf_files = [f for f in os.listdir('.') if f.lower().endswith('.pdf')]
    if not pdf_files:
        print("⚠️ 未找到PDF测试文件")
        return True

    try:
        import pypdfium2 as pdfium
        print("✅ pypdfium2导入成功")

        for pdf_file in pdf_files[:1]:  # 只测试第一个
            print(f"\n测试文件: {pdf_file}")

            # 1. 打开PDF
            try:
                pdf = pdfium.PdfDocument(pdf_file)
                print(f"   ✅ PDF打开成功，共 {len(pdf)} 页")
            except Exception as e:
                print(f"   ❌ PDF打开失败: {e}")
                return False

            # 2. 基本渲染测试
            try:
                page = pdf[0]
                print("   开始渲染页面...")

                # 最简单的渲染调用
                bitmap = page.render(scale=1.0)
                print("   ✅ 基本渲染成功")

                # 转换为PIL Image
                image = bitmap.to_pil()
                print(f"   ✅ 转换为PIL Image成功，尺寸: {image.size}")

                # 清理资源
                bitmap = None
                page = None
                pdf.close()

            except Exception as e:
                print(f"   ❌ 渲染失败: {e}")
                if pdf:
                    pdf.close()
                return False

        return True
    except Exception as e:
        print(f"❌ PDF测试失败: {e}")
        return False

def test_ocr_pdf_simple():
    """测试OCR工具的PDF处理"""
    print("\n" + "=" * 50)
    print("OCR工具PDF处理测试")
    print("=" * 50)

    try:
        from invoice_ocr_tool import InvoiceOCRTool

        # 初始化OCR工具
        ocr_tool = InvoiceOCRTool(use_ai=False)
        print("✅ OCR工具初始化成功")

        # 查找PDF文件
        pdf_files = [f for f in os.listdir('.') if f.lower().endswith('.pdf')]
        if not pdf_files:
            print("⚠️ 未找到PDF测试文件，跳过OCR测试")
            return True

        # 测试PDF处理
        pdf_file = pdf_files[0]
        print(f"\n测试OCR处理: {pdf_file}")

        result = ocr_tool.process_invoice(pdf_file)
        if result:
            print("✅ PDF OCR处理成功")
            print(f"   解析方式: {result.get('解析方式', '未知')}")
            extracted = result.get('提取字段', {})
            field_count = len([v for v in extracted.values() if v])
            print(f"   提取字段数: {field_count}/6")
            return True
        else:
            print("❌ PDF OCR处理失败")
            return False

    except Exception as e:
        print(f"❌ OCR测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("PDF简化处理测试")
    print("=" * 60)

    # 1. 基本PDF处理测试
    if not test_pdf_basic():
        print("\n❌ 基本PDF处理失败")
        print("建议：移除PDF支持，专注图片处理")
        return False

    # 2. OCR PDF处理测试
    if not test_ocr_pdf_simple():
        print("\n❌ OCR PDF处理失败")
        print("建议：移除PDF支持，专注图片处理")
        return False

    print("\n" + "=" * 60)
    print("🎉 PDF处理测试全部通过！")
    print("PDF支持可以保留")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)