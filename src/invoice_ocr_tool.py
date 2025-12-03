#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专用发票识别工具
使用umi-OCR服务识别发票并提取关键信息
"""

import requests
import json
import argparse
import sys
import re
import os
import base64
from datetime import datetime
from typing import Dict, Optional, List, Any
import logging

# 导入AI智能解析器
try:
    from ai_invoice_parser import AIInvoiceParser
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    logging.warning("AI智能解析功能不可用，请确保安装了anthropic库")


class InvoiceResult:
    """发票识别结果类"""
    def __init__(self, image_path: str, processing_time: str, extracted_fields: Dict[str, str],
                 ocr_result: Dict[str, Any] = None, parsing_method: str = "📝 传统正则解析",
                 ai_confidence: float = None, ai_analysis: str = None, full_text: str = ""):
        self.image_path = image_path
        self.processing_time = processing_time
        self.extracted_fields = extracted_fields
        self.ocr_result = ocr_result
        self.parsing_method = parsing_method
        self.ai_confidence = ai_confidence
        self.ai_analysis = ai_analysis
        self.full_text = full_text

    def get(self, key: str, default=None):
        """字典式访问"""
        mapping = {
            '图片路径': self.image_path,
            '处理时间': self.processing_time,
            '提取字段': self.extracted_fields,
            'OCR原始结果': self.ocr_result,
            '解析方式': self.parsing_method,
            'AI置信度': self.ai_confidence,
            'AI原始响应': self.ai_analysis,
            'AI分析结果': self.ai_analysis,
            '完整文本': self.full_text
        }
        return mapping.get(key, default)

    def __getitem__(self, key: str):
        return self.get(key)

    def __contains__(self, key: str):
        return key in ['图片路径', '处理时间', '提取字段', 'OCR原始结果', '解析方式', 'AI置信度', 'AI原始响应', 'AI分析结果', '完整文本']

# 导入字段配置管理器
try:
    from field_config import field_config_manager
    FIELD_CONFIG_AVAILABLE = True
except ImportError:
    FIELD_CONFIG_AVAILABLE = False
    logging.warning("字段配置管理功能不可用")

# 导入Excel导出器
try:
    from excel_exporter import ExcelExporter
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    logging.warning("Excel导出功能不可用，请确保安装了openpyxl库")


class InvoiceOCRTool:
    """发票OCR识别工具类"""

    def __init__(self, ocr_host: str = "127.0.0.1", ocr_port: int = 1224,
                 use_ai: bool = True, ai_config: Dict[str, Any] = None):
        """
        初始化OCR工具

        Args:
            ocr_host: OCR服务主机地址
            ocr_port: OCR服务端口
            use_ai: 是否使用AI智能解析
            ai_config: AI配置参数
        """
        self.ocr_url = f"http://{ocr_host}:{ocr_port}"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'InvoiceOCRTool/2.0-AI'
        })

        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # AI智能解析器初始化
        self.use_ai = use_ai and AI_AVAILABLE
        self.ai_parser = None

        if self.use_ai:
            try:
                self.ai_parser = AIInvoiceParser(**(ai_config or {}))
                self.logger.info("✅ AI智能解析功能已启用")
            except Exception as e:
                self.logger.warning(f"AI初始化失败，将使用传统解析: {e}")
                self.use_ai = False

        # Excel导出器初始化
        self.excel_exporter = None
        if EXCEL_AVAILABLE:
            try:
                self.excel_exporter = ExcelExporter()
                self.logger.info("✅ Excel导出功能已启用")
            except Exception as e:
                self.logger.warning(f"Excel导出器初始化失败: {e}")
        else:
            self.logger.warning("Excel导出功能不可用")

    def test_ocr_connection(self) -> bool:
        """测试OCR服务连接"""
        try:
            # 先尝试访问根路径检查服务是否运行
            response = self.session.get(f"{self.ocr_url}/", timeout=5)
            if response.status_code == 200:
                return True

            # 如果根路径不可访问，尝试OCR接口（返回405也是正常的）
            response = self.session.post(f"{self.ocr_url}/api/ocr", timeout=5)
            return response.status_code in [200, 405]  # 405表示服务运行但不接受空请求
        except Exception as e:
            self.logger.error(f"OCR服务连接失败: {e}")
            return False

    def recognize_image(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        识别图片或PDF中的文字

        Args:
            image_path: 图片或PDF文件路径

        Returns:
            OCR识别结果
        """
        if not os.path.exists(image_path):
            self.logger.error(f"文件不存在: {image_path}")
            return None

        try:
            # 检查是否为PDF文件
            if image_path.lower().endswith('.pdf'):
                self.logger.info(f"处理PDF文件: {image_path}")

                # 检查pypdfium2是否可用
                try:
                    import pypdfium2 as pdfium
                    import io
                except ImportError as e:
                    self.logger.error("pypdfium2库未安装，无法处理PDF文件")
                    self.logger.info("请运行: pip install pypdfium2")
                    return None

                # 打开PDF文件
                try:
                    pdf = pdfium.PdfDocument(image_path)
                    self.logger.info(f"PDF文件打开成功，共 {len(pdf)} 页")
                except Exception as e:
                    self.logger.error(f"PDF文件打开失败: {e}")
                    self.logger.info("请检查PDF文件是否损坏或加密")
                    return None

                # 处理第一页（目前只支持单页PDF）
                try:
                    page = pdf[0]

                    # 渲染页面为图片
                    bitmap = page.render(
                        scale=2.0,  # 提高分辨率以获得更好的OCR效果
                        crop=(0, 0, 0, 0),  # 不裁剪
                    )

                    # 将渲染的位图转换为PIL Image
                    pil_image = bitmap.to_pil()

                    # 将PIL Image转换为二进制数据
                    image_stream = io.BytesIO()
                    pil_image.save(image_stream, format='PNG')
                    image_data = image_stream.getvalue()

                    self.logger.info("PDF转换为图片成功")

                    # 清理资源
                    bitmap = None
                    page = None
                    pdf.close()

                except Exception as e:
                    self.logger.error(f"PDF页面渲染失败: {e}")
                    return None
            else:
                # 读取图片文件并编码为base64
                try:
                    with open(image_path, 'rb') as f:
                        image_data = f.read()
                    self.logger.info(f"图片文件读取成功: {image_path}")
                except Exception as e:
                    self.logger.error(f"图片文件读取失败: {e}")
                    return None

            # 将图片数据编码为base64
            base64_data = base64.b64encode(image_data).decode('utf-8')

            # 构建JSON请求
            request_data = {
                'base64': base64_data,
                # 可选的OCR参数
                'options': {
                    'det_limit_side_len': 1024,
                    'cls': True,
                    'rec': True
                }
            }

            # 发送JSON请求
            response = self.session.post(
                f"{self.ocr_url}/api/ocr",
                json=request_data,
                timeout=120  # 增加到120秒，适合处理PDF和复杂图片
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 100:  # 成功状态码
                    return result
                else:
                    self.logger.error(f"OCR识别失败: {result.get('data', '未知错误')}")
                    return None
            else:
                self.logger.error(f"OCR请求失败，状态码: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"OCR识别异常: {e}")
            return None

    def extract_invoice_fields(self, ocr_result: Dict[str, Any], field_names: List[str] = None) -> Dict[str, str]:
        """
        从OCR结果中提取发票字段（支持动态字段配置）

        Args:
            ocr_result: OCR识别结果
            field_names: 需要提取的字段名称列表，如果为None则使用所有配置的字段

        Returns:
            提取的发票字段字典
        """
        if not ocr_result or 'data' not in ocr_result:
            return {}

        # 获取识别的文字内容
        full_text = ""

        if isinstance(ocr_result['data'], str):
            # umi-OCR的直接文本格式
            full_text = ocr_result['data']
        elif isinstance(ocr_result['data'], list):
            # umi-OCR的详细格式（包含text字段）
            text_blocks = []
            for item in ocr_result['data']:
                if isinstance(item, dict):
                    if 'text' in item:
                        text_blocks.append(item['text'])
                    elif 'content' in item:
                        text_blocks.append(item['content'])
                elif isinstance(item, str):
                    text_blocks.append(item)
            full_text = '\n'.join(text_blocks)
        elif isinstance(ocr_result['data'], dict):
            # 可能的嵌套字典格式
            if 'res' in ocr_result['data']:
                for item in ocr_result['data']['res']:
                    if isinstance(item, dict):
                        if 'text' in item:
                            full_text += item['text'] + '\n'
                        elif 'content' in item:
                            full_text += item['content'] + '\n'
            elif 'text' in ocr_result['data']:
                full_text = ocr_result['data']['text']
            elif 'content' in ocr_result['data']:
                full_text = ocr_result['data']['content']

        self.logger.debug(f"OCR识别文本:\n{full_text}")

        # 如果没有指定字段，使用所有配置的字段
        if field_names is None:
            if FIELD_CONFIG_AVAILABLE:
                field_names = field_config_manager.get_field_names()
            else:
                # 回退到默认字段列表
                field_names = ['发票号码', '开票日期', '销售方名称', '购买方名称', '合计金额', '税额']

        self.logger.info(f"开始提取字段: {field_names}")

        # 使用AI智能解析或传统正则表达式解析
        if self.use_ai and self.ai_parser:
            self.logger.info("🤖 使用AI智能解析字段...")
            ai_result = self.ai_parser.extract_fields_with_ai(full_text, field_names)

            if ai_result and ai_result.get('extracted_fields'):
                extracted_fields = ai_result['extracted_fields']
                confidence = ai_result.get('ai_confidence', 0)

                # 记录AI解析结果
                self.logger.info(f"✅ AI解析完成，置信度: {confidence:.3f}")

                # 如果AI置信度较低，同时使用传统方法作为补充
                if confidence < 0.7:
                    self.logger.warning("⚠️ AI置信度较低，启用传统解析作为补充")
                    traditional_fields = self.extract_fields_traditional(full_text, field_names)

                    # 合并结果，AI优先，传统方法填补空缺
                    for field, value in traditional_fields.items():
                        if not extracted_fields.get(field) and value:
                            extracted_fields[field] = value
                            self.logger.info(f"传统方法补充字段: {field}")

                return extracted_fields
            else:
                self.logger.warning("⚠️ AI解析失败，回退到传统解析方法")

        # 使用传统正则表达式解析
        self.logger.info("📝 使用传统正则表达式解析字段...")
        return self.extract_fields_traditional(full_text, field_names)

    def extract_fields_traditional(self, full_text: str, field_names: List[str] = None) -> Dict[str, str]:
        """
        使用传统正则表达式方法提取字段（支持动态字段配置）

        Args:
            full_text: OCR识别的完整文本
            field_names: 需要提取的字段名称列表，如果为None则使用所有配置的字段

        Returns:
            提取的字段字典
        """
        extracted_fields = {}

        # 如果没有指定字段，使用所有配置的字段
        if field_names is None:
            if FIELD_CONFIG_AVAILABLE:
                field_names = field_config_manager.get_field_names()
            else:
                # 回退到默认字段列表
                field_names = ['发票号码', '开票日期', '销售方名称', '购买方名称', '合计金额', '税额']

        # 使用动态字段配置进行提取
        if FIELD_CONFIG_AVAILABLE:
            for field_name in field_names:
                field = field_config_manager.get_field(field_name)
                if field and field.patterns:
                    # 使用字段配置中的正则表达式模式
                    for pattern in field.patterns:
                        try:
                            match = re.search(pattern, full_text, re.IGNORECASE)
                            if match:
                                value = match.group(1).strip()
                                # 使用字段配置管理器验证和清理字段值
                                validated_value = field_config_manager.validate_field_value(field_name, value)
                                if validated_value:
                                    extracted_fields[field_name] = validated_value
                                    self.logger.debug(f"传统方法提取成功: {field_name} = {validated_value}")
                                    break  # 找到第一个匹配就停止
                        except re.error as e:
                            self.logger.warning(f"字段 {field_name} 的正则表达式有误: {pattern}, 错误: {e}")
                else:
                    self.logger.warning(f"字段 {field_name} 没有配置或没有提取模式")
        else:
            # 回退到硬编码的字段提取逻辑
            self.logger.warning("字段配置不可用，使用硬编码提取逻辑")
            extracted_fields = self._extract_fields_hardcoded(full_text)

        # 1. 发票号码提取
        invoice_number_patterns = [
            r'发票号码[:：]?\s*(\w+)',
            r'No\.?\s*[:：]?\s*(\w+)',
            r'Invoice\s*No\.?[:：]?\s*(\w+)',
            r'(\d{8,12})',  # 8-12位数字
        ]
        for pattern in invoice_number_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                extracted_fields['发票号码'] = match.group(1)
                break

        # 2. 开票日期提取
        date_patterns = [
            r'开票日期[:：]?\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)',
            r'Date[:：]?\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
            r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, full_text)
            if match:
                extracted_fields['开票日期'] = match.group(1).replace('年', '-').replace('月', '-').replace('日', '')
                break

        # 3. 销售方名称提取
        seller_patterns = [
            r'销售方[:：]?\s*([^开票方购买方收款方付款方\s]{2,20})',
            r'收款人[:：]?\s*([^开票方购买方收款方付款方\s]{2,20})',
            r'Seller[:：]?\s*([^\n]{2,30})',
        ]
        for pattern in seller_patterns:
            match = re.search(pattern, full_text)
            if match:
                extracted_fields['销售方名称'] = match.group(1).strip()
                break

        # 4. 购买方名称提取
        buyer_patterns = [
            r'购买方[:：]?\s*([^开票方购买方收款方付款方\s]{2,20})',
            r'付款人[:：]?\s*([^开票方购买方收款方付款方\s]{2,20})',
            r'Buyer[:：]?\s*([^\n]{2,30})',
        ]
        for pattern in buyer_patterns:
            match = re.search(pattern, full_text)
            if match:
                extracted_fields['购买方名称'] = match.group(1).strip()
                break

        # 5. 金额提取
        amount_patterns = [
            r'价税合计[:：]?\s*￥?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'合计金额[:：]?\s*￥?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'Total[:：]?\s*￥?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'￥(\d+(?:,\d{3})*(?:\.\d{2})?)',
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, full_text)
            if match:
                extracted_fields['合计金额'] = match.group(1).replace(',', '')
                break

        # 6. 税额提取
        tax_patterns = [
            r'税额[:：]?\s*￥?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'增值税[:：]?\s*￥?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'Tax[:：]?\s*￥?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
        ]
        for pattern in tax_patterns:
            match = re.search(pattern, full_text)
            if match:
                extracted_fields['税额'] = match.group(1).replace(',', '')
                break

        # 如果没有找到明确的税额，尝试计算
        if '合计金额' in extracted_fields and '税额' not in extracted_fields:
            # 尝试找到不含税金额
            for pattern in [r'不含税金额[:：]?\s*￥?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)']:
                match = re.search(pattern, full_text)
                if match:
                    try:
                        amount = float(extracted_fields['合计金额'])
                        amount_without_tax = float(match.group(1).replace(',', ''))
                        tax = amount - amount_without_tax
                        extracted_fields['税额'] = f"{tax:.2f}"
                        break
                    except ValueError:
                        continue

        return extracted_fields

    def process_invoice(self, image_path: str, output_format: str = "json") -> Optional[Dict[str, Any]]:
        """
        处理发票图片

        Args:
            image_path: 发票图片路径
            output_format: 输出格式 (json, text)

        Returns:
            处理结果
        """
        self.logger.info(f"开始处理发票图片: {image_path}")

        # OCR识别
        try:
            ocr_result = self.recognize_image(image_path)
            if not ocr_result:
                file_type = "PDF" if image_path.lower().endswith('.pdf') else "图片"
                self.logger.error(f"{file_type}OCR识别失败")
                return None
        except Exception as e:
            file_type = "PDF" if image_path.lower().endswith('.pdf') else "图片"
            self.logger.error(f"{file_type}OCR识别异常: {str(e)}")
            return None

        # 获取OCR识别文本
        full_text = ""
        if isinstance(ocr_result.get('data'), str):
            full_text = ocr_result['data']
        elif isinstance(ocr_result.get('data'), list):
            text_blocks = []
            for item in ocr_result['data']:
                if isinstance(item, dict) and 'text' in item:
                    text_blocks.append(item['text'])
                elif isinstance(item, str):
                    text_blocks.append(item)
            full_text = '\n'.join(text_blocks)

        # 提取字段并记录解析方式
        parsing_method = "📝 传统正则解析"
        ai_confidence = None
        ai_analysis = None

        if self.use_ai and self.ai_parser:
            self.logger.info("🤖 使用AI智能解析字段...")
            ai_result = self.ai_parser.extract_fields_with_ai(full_text)

            if ai_result and ai_result.get('extracted_fields'):
                extracted_fields = ai_result['extracted_fields']
                ai_confidence = ai_result.get('ai_confidence', 0)
                ai_analysis = ai_result.get('raw_ai_response', '')
                parsing_method = "🤖 AI智能解析"

                self.logger.info(f"✅ AI解析完成，置信度: {ai_confidence:.3f}")

                # 如果AI置信度较低，同时使用传统方法作为补充
                if ai_confidence < 0.7:
                    self.logger.warning("⚠️ AI置信度较低，启用传统解析作为补充")
                    traditional_fields = self.extract_fields_traditional(full_text)

                    # 合并结果，AI优先，传统方法填补空缺
                    for field, value in traditional_fields.items():
                        if not extracted_fields.get(field) and value:
                            extracted_fields[field] = value
                            self.logger.info(f"传统方法补充字段: {field}")
            else:
                self.logger.warning("⚠️ AI解析失败，回退到传统解析方法")
                extracted_fields = self.extract_fields_traditional(full_text)
        else:
            self.logger.info("📝 使用传统正则表达式解析字段...")
            extracted_fields = self.extract_fields_traditional(full_text)

        # 创建结果对象
        result = InvoiceResult(
            image_path=image_path,
            processing_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            extracted_fields=extracted_fields,
            ocr_result=ocr_result if output_format == "json" else None,
            parsing_method=parsing_method,
            ai_confidence=ai_confidence,
            ai_analysis=ai_analysis,
            full_text=full_text
        )

        self.logger.info("发票处理完成")
        return result

    def save_result(self, result: Dict[str, Any], output_path: str, format_type: str = "json"):
        """
        保存识别结果

        Args:
            result: 识别结果
            output_path: 输出文件路径
            format_type: 保存格式 (json, txt)
        """
        try:
            if format_type.lower() == "json":
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            elif format_type.lower() == "txt":
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(f"发票识别结果\n")
                    f.write(f"{'='*50}\n")
                    f.write(f"图片路径: {result.get('图片路径', 'N/A')}\n")
                    f.write(f"处理时间: {result.get('处理时间', 'N/A')}\n")
                    f.write(f"\n提取字段:\n")
                    f.write(f"{'-'*30}\n")

                    for key, value in result.get('提取字段', {}).items():
                        f.write(f"{key}: {value}\n")
            elif format_type.lower() == "csv":
                import csv
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['字段名称', '提取内容'])
                    for key, value in result.get('提取字段', {}).items():
                        writer.writerow([key, value])
            elif format_type.lower() == "xlsx":
                if not self.excel_exporter:
                    raise ValueError("Excel导出功能不可用，请确保安装了openpyxl库")

                # 准备Excel数据
                excel_data = {
                    '图片路径': result.get('图片路径', ''),
                    '处理时间': result.get('处理时间', ''),
                    '解析方式': getattr(result, 'parsing_method', '未知'),
                    'AI置信度': getattr(result, 'ai_confidence', None),
                    '提取字段': result.get('提取字段', {})
                }

                # 默认使用横向格式导出
                if not self.excel_exporter.export_single_invoice(output_path, excel_data, "horizontal"):
                    raise ValueError("Excel文件导出失败")
            else:
                raise ValueError(f"不支持的保存格式: {format_type}")

            self.logger.info(f"结果已保存到: {output_path}")

        except Exception as e:
            self.logger.error(f"保存结果失败: {e}")

    def _extract_fields_hardcoded(self, full_text: str) -> Dict[str, str]:
        """
        硬编码的字段提取方法（作为回退方案）

        Args:
            full_text: OCR识别的完整文本

        Returns:
            提取的字段字典
        """
        extracted_fields = {}

        # 1. 发票号码提取
        invoice_number_patterns = [
            r'发票号码[:：]?\s*(\w+)',
            r'No\.?\s*[:：]?\s*(\w+)',
            r'Invoice\s*No\.?[:：]?\s*(\w+)',
            r'(\d{8,12})',  # 8-12位数字
        ]
        for pattern in invoice_number_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                extracted_fields['发票号码'] = match.group(1)
                break

        # 2. 开票日期提取
        date_patterns = [
            r'开票日期[:：]?\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)',
            r'Date[:：]?\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
            r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, full_text)
            if match:
                date_str = match.group(1).replace('年', '-').replace('月', '-').replace('日', '')
                extracted_fields['开票日期'] = date_str
                break

        # 3. 销售方名称提取
        seller_patterns = [
            r'销售方[:：]?\s*([^开票方购买方收款方付款方\s]{2,20})',
            r'收款人[:：]?\s*([^开票方购买方收款方付款方\s]{2,20})',
            r'Seller[:：]?\s*([^\n]{2,30})',
        ]
        for pattern in seller_patterns:
            match = re.search(pattern, full_text)
            if match:
                extracted_fields['销售方名称'] = match.group(1).strip()
                break

        # 4. 购买方名称提取
        buyer_patterns = [
            r'购买方[:：]?\s*([^开票方购买方收款方付款方\s]{2,20})',
            r'付款人[:：]?\s*([^开票方购买方收款方付款方\s]{2,20})',
            r'Buyer[:：]?\s*([^\n]{2,30})',
        ]
        for pattern in buyer_patterns:
            match = re.search(pattern, full_text)
            if match:
                extracted_fields['购买方名称'] = match.group(1).strip()
                break

        # 5. 金额提取
        amount_patterns = [
            r'价税合计[:：]?\s*￥?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'合计金额[:：]?\s*￥?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'Total[:：]?\s*￥?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'￥(\d+(?:,\d{3})*(?:\.\d{2})?)',
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, full_text)
            if match:
                extracted_fields['合计金额'] = match.group(1).replace(',', '')
                break

        # 6. 税额提取
        tax_patterns = [
            r'税额[:：]?\s*￥?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'增值税[:：]?\s*￥?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'Tax[:：]?\s*￥?\s*(\d+(?:,\d{3}*(?:\.\d{2})?)',
        ]
        for pattern in tax_patterns:
            match = re.search(pattern, full_text)
            if match:
                extracted_fields['税额'] = match.group(1).replace(',', '')
                break

        return extracted_fields


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="专用发票OCR识别工具 - AI增强版")
    parser.add_argument("image_path", help="发票图片文件路径")
    parser.add_argument("-o", "--output", help="输出文件路径")
    parser.add_argument("-f", "--format", choices=["json", "txt", "csv", "xlsx"], default="json",
                       help="输出格式 (json/txt/csv/xlsx)")
    parser.add_argument("--host", default="127.0.0.1", help="OCR服务主机地址")
    parser.add_argument("--port", type=int, default=1224, help="OCR服务端口")
    parser.add_argument("--debug", action="store_true", help="开启调试模式")

    # AI相关参数
    parser.add_argument("--no-ai", action="store_true", help="禁用AI智能解析，使用传统方法")
    parser.add_argument("--ai-model", default="glm-4.6", help="AI模型名称")
    parser.add_argument("--ai-api-key", help="智谱AI API密钥")
    parser.add_argument("--ai-base-url", help="智谱AI API基础URL")

    args = parser.parse_args()

    # 设置日志级别
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # 检查输入文件
    if not os.path.exists(args.image_path):
        print(f"错误: 图片文件不存在 - {args.image_path}", file=sys.stderr)
        sys.exit(1)

    # AI配置
    ai_config = {}
    if args.ai_api_key:
        ai_config['api_key'] = args.ai_api_key
    if args.ai_base_url:
        ai_config['base_url'] = args.ai_base_url
    if args.ai_model:
        ai_config['model'] = args.ai_model

    # 创建OCR工具实例
    use_ai = not args.no_ai
    ocr_tool = InvoiceOCRTool(args.host, args.port, use_ai=use_ai, ai_config=ai_config or None)

    # 测试OCR服务连接
    if not ocr_tool.test_ocr_connection():
        print(f"错误: 无法连接到OCR服务 {args.host}:{args.port}", file=sys.stderr)
        print("请确保umi-OCR服务已启动并运行在指定端口", file=sys.stderr)
        sys.exit(1)

    # 处理发票
    result = ocr_tool.process_invoice(args.image_path, args.format)

    if result:
        # 显示提取结果
        print("\n=== 发票识别结果 ===")
        for key, value in result.get('提取字段', {}).items():
            print(f"{key}: {value}")

        # 保存结果
        if args.output:
            ocr_tool.save_result(result, args.output, args.format)
        else:
            # 默认输出文件名
            base_name = os.path.splitext(os.path.basename(args.image_path))[0]
            default_output = f"{base_name}_result.{args.format}"
            ocr_tool.save_result(result, default_output, args.format)
            print(f"\n结果已保存到: {default_output}")
    else:
        print("发票识别失败", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()