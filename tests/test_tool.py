#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证发票OCR工具的基本功能
"""

import unittest
import json
import os
from unittest.mock import Mock, patch, mock_open
from invoice_ocr_tool import InvoiceOCRTool

class TestInvoiceOCRTool(unittest.TestCase):
    """发票OCR工具测试类"""

    def setUp(self):
        """测试前准备"""
        self.ocr_tool = InvoiceOCRTool()

    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.ocr_tool.ocr_url, "http://127.0.0.1:1224")
        self.assertIsNotNone(self.ocr_tool.session)

    def test_custom_host_port(self):
        """测试自定义主机和端口"""
        custom_tool = InvoiceOCRTool("192.168.1.100", 8080)
        self.assertEqual(custom_tool.ocr_url, "http://192.168.1.100:8080")

    @patch('requests.Session.get')
    def test_ocr_connection_success(self, mock_get):
        """测试OCR服务连接成功"""
        mock_get.return_value.status_code = 200
        self.assertTrue(self.ocr_tool.test_ocr_connection())

    @patch('requests.Session.get')
    def test_ocr_connection_failure(self, mock_get):
        """测试OCR服务连接失败"""
        mock_get.side_effect = Exception("Connection failed")
        self.assertFalse(self.ocr_tool.test_ocr_connection())

    def test_extract_invoice_fields_with_data(self):
        """测试字段提取功能 - 有数据"""
        # 模拟OCR结果
        ocr_result = {
            "data": [
                {"text": "发票号码：12345678"},
                {"text": "开票日期：2024-01-01"},
                {"text": "销售方：某某科技有限公司"},
                {"text": "购买方：某某贸易有限公司"},
                {"text": "价税合计：￥11,700.00"},
                {"text": "税额：￥1,700.00"}
            ]
        }

        extracted = self.ocr_tool.extract_invoice_fields(ocr_result)

        self.assertEqual(extracted.get('发票号码'), '12345678')
        self.assertEqual(extracted.get('开票日期'), '2024-01-01')
        self.assertEqual(extracted.get('销售方名称'), '某某科技有限公司')
        self.assertEqual(extracted.get('购买方名称'), '某某贸易有限公司')
        self.assertEqual(extracted.get('合计金额'), '11700.00')
        self.assertEqual(extracted.get('税额'), '1700.00')

    def test_extract_invoice_fields_empty_data(self):
        """测试字段提取功能 - 空数据"""
        empty_result = {}
        extracted = self.ocr_tool.extract_invoice_fields(empty_result)
        self.assertEqual(extracted, {})

    def test_extract_invoice_fields_no_data(self):
        """测试字段提取功能 - 无data字段"""
        no_data_result = {"status": "error"}
        extracted = self.ocr_tool.extract_invoice_fields(no_data_result)
        self.assertEqual(extracted, {})

    @patch('builtins.open', new_callable=mock_open, read_data=b'fake_image_data')
    @patch('requests.Session.post')
    def test_recognize_image_success(self, mock_post, mock_file):
        """测试图片识别成功"""
        # 模拟成功响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"text": "测试识别结果"}]
        }
        mock_post.return_value = mock_response

        result = self.ocr_tool.recognize_image("test_image.jpg")

        self.assertIsNotNone(result)
        self.assertIn("data", result)

    def test_recognize_image_file_not_exists(self):
        """测试图片识别 - 文件不存在"""
        result = self.ocr_tool.recognize_image("nonexistent_file.jpg")
        self.assertIsNone(result)

    @patch('builtins.open', new_callable=mock_open)
    def test_save_result_json(self, mock_file):
        """测试保存结果 - JSON格式"""
        result = {
            "图片路径": "test.jpg",
            "提取字段": {"发票号码": "12345"}
        }

        self.ocr_tool.save_result(result, "output.json", "json")

        # 验证文件被打开并写入
        mock_file.assert_called_once_with("output.json", 'w', encoding='utf-8')
        written_data = mock_file().write.call_args[0][0]

        # 验证写入的是有效的JSON
        json_data = json.loads(written_data)
        self.assertEqual(json_data["图片路径"], "test.jpg")

    @patch('builtins.open', new_callable=mock_open)
    def test_save_result_txt(self, mock_file):
        """测试保存结果 - TXT格式"""
        result = {
            "图片路径": "test.jpg",
            "提取字段": {"发票号码": "12345", "开票日期": "2024-01-01"}
        }

        self.ocr_tool.save_result(result, "output.txt", "txt")

        # 验证文件被打开并写入
        mock_file.assert_called_once_with("output.txt", 'w', encoding='utf-8')
        written_data = mock_file().write.call_args[0][0]

        # 验证写入的文本包含预期内容
        self.assertIn("发票号码: 12345", written_data)
        self.assertIn("开票日期: 2024-01-01", written_data)

    def test_process_invoice_no_ocr_result(self):
        """测试处理发票 - OCR识别失败"""
        with patch.object(self.ocr_tool, 'recognize_image', return_value=None):
            result = self.ocr_tool.process_invoice("test.jpg")
            self.assertIsNone(result)

    def test_process_invoice_with_ocr_result(self):
        """测试处理发票 - OCR识别成功"""
        mock_ocr_result = {
            "data": [
                {"text": "发票号码：12345678"},
                {"text": "开票日期：2024-01-01"}
            ]
        }

        with patch.object(self.ocr_tool, 'recognize_image', return_value=mock_ocr_result):
            result = self.ocr_tool.process_invoice("test.jpg", "json")

            self.assertIsNotNone(result)
            self.assertEqual(result["图片路径"], "test.jpg")
            self.assertIn("提取字段", result)
            self.assertEqual(result["提取字段"]["发票号码"], "12345678")


def run_manual_test():
    """手动测试函数"""
    print("=== 发票OCR工具手动测试 ===\n")

    print("1. 测试工具初始化")
    try:
        tool = InvoiceOCRTool()
        print("✅ 工具初始化成功")
    except Exception as e:
        print(f"❌ 工具初始化失败: {e}")
        return

    print("\n2. 测试OCR服务连接")
    if tool.test_ocr_connection():
        print("✅ OCR服务连接正常")
    else:
        print("❌ OCR服务连接失败")
        print("   请确保umi-OCR服务已启动并运行在127.0.0.1:1224")

    print("\n3. 测试字段提取逻辑")
    # 模拟一些发票文本
    test_text = """
    发票号码：12345678
    开票日期：2024-01-01
    销售方：某某科技有限公司
    购买方：某某贸易有限公司
    价税合计：￥11,700.00
    税额：￥1,700.00
    """

    mock_ocr_result = {
        "data": [
            {"text": line.strip()}
            for line in test_text.split('\n')
            if line.strip()
        ]
    }

    extracted = tool.extract_invoice_fields(mock_ocr_result)
    print("提取的字段：")
    for field, value in extracted.items():
        print(f"  {field}: {value}")

    if extracted:
        print("✅ 字段提取测试成功")
    else:
        print("❌ 字段提取测试失败")

    print("\n=== 手动测试完成 ===")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "manual":
        run_manual_test()
    else:
        print("运行单元测试...")
        unittest.main(verbosity=2)