#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图纸图签OCR识别工具
专门针对工程图纸图签区域的智能OCR识别
"""

import logging
import os
from typing import Dict, Any, Optional, Tuple, List
from PIL import Image
import json
from datetime import datetime
import numpy as np
import cv2

from image_optimizer import ImageOptimizer
from invoice_ocr_tool import InvoiceOCRTool
from ai_invoice_parser import AIInvoiceParser
from field_config import field_config_manager

# 导入增强模块
from enhanced_signature_detector import EnhancedSignatureDetector
from handwriting_signature_manager import HandwritingSignatureManager


class DrawingOCRTool:
    """图纸图签OCR识别工具"""

    def __init__(self, ocr_service_url: str = "http://127.0.0.1:1224"):
        self.logger = logging.getLogger(__name__)
        self.ocr_service_url = ocr_service_url

        # 解析URL获取主机和端口
        if ocr_service_url.startswith("http://"):
            host_port = ocr_service_url[7:]  # 移除 "http://"
        elif ocr_service_url.startswith("https://"):
            host_port = ocr_service_url[8:]  # 移除 "https://"
        else:
            host_port = ocr_service_url

        if ":" in host_port:
            host, port_str = host_port.split(":", 1)
            port = int(port_str)
        else:
            host = host_port
            port = 1224  # 默认端口

        # 初始化组件
        self.image_optimizer = ImageOptimizer()
        self.ocr_tool = InvoiceOCRTool(host, port)  # 修复：正确传递主机和端口
        self.ai_parser = AIInvoiceParser()

        # 初始化增强模块
        self.signature_detector = EnhancedSignatureDetector()
        self.signature_manager = HandwritingSignatureManager()

        # 图纸识别配置
        self.drawing_config = self._load_drawing_config()

    def _load_drawing_config(self) -> dict:
        """加载图纸识别配置"""
        try:
            # 优先使用tuqian001.json配置
            config_files = ['tuqian001.json', 'docs/field_configs.json']
            for config_file in config_files:
                if os.path.exists(config_file):
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        self.logger.info(f"使用图纸配置文件: {config_file}")
                        return config

        except Exception as e:
            self.logger.error(f"加载图纸配置失败: {e}")

        # 返回默认配置
        return {
            "fields": {
                "项目名称": {
                    "name": "项目名称",
                    "description": "该图纸的图签部分显示的项目名称",
                    "field_type": "text",
                    "patterns": [],
                    "ai_prompt": "提取该图纸所显示的 项目工程名称",
                    "required": False,
                    "validation_rules": None
                },
                "审定人": {
                    "name": "审定人",
                    "description": "图纸图签部分显示的 审定人 字段后填写的 姓名",
                    "field_type": "text",
                    "patterns": [],
                    "ai_prompt": "提取图纸图签部分显示的 审定人 字段后填写的 第一个姓名，若姓名为空，该字段可以为空",
                    "required": True,
                    "validation_rules": None
                },
                "审核人": {
                    "name": "审核人",
                    "description": "图纸图签部分显示的 审核人 字段后填写的 姓名",
                    "field_type": "text",
                    "patterns": [],
                    "ai_prompt": "提取图纸图签部分显示的 审核人 字段后填写的 第一个姓名，若姓名为空，该字段可以为空",
                    "required": True,
                    "validation_rules": None
                },
                "校核人": {
                    "name": "校核人",
                    "description": "图纸图签部分显示的 校核人 字段后填写的 姓名",
                    "field_type": "text",
                    "patterns": [],
                    "ai_prompt": "提取图纸图签部分显示的 校核人 字段后填写的 第一个姓名，若姓名为空，该字段可以为空",
                    "required": True,
                    "validation_rules": None
                },
                "设计人": {
                    "name": "设计人",
                    "description": "图纸图签部分显示的 设计人 字段后填写的 姓名",
                    "field_type": "text",
                    "patterns": [],
                    "ai_prompt": "提取图纸图签部分显示的 设计人 字段后填写的 第一个姓名，若姓名为空，该字段可以为空",
                    "required": True,
                    "validation_rules": None
                },
                "绘图人": {
                    "name": "绘图人",
                    "description": "图纸图签部分显示的 绘图人 字段后填写的 姓名",
                    "field_type": "text",
                    "patterns": [],
                    "ai_prompt": "提取图纸图签部分显示的 绘图人 字段后填写的 第一个姓名，若姓名为空，该字段可以为空",
                    "required": True,
                    "validation_rules": None
                },
                "项目负责人": {
                    "name": "项目负责人",
                    "description": "图纸图签部分显示的 项目负责人 字段后填写的 姓名",
                    "field_type": "text",
                    "patterns": [],
                    "ai_prompt": "提取图纸图签部分显示的 项目负责人 字段后填写的 第一个姓名，若姓名为空，该字段可以为空",
                    "required": True,
                    "validation_rules": None
                },
                "专业负责人": {
                    "name": "专业负责人",
                    "description": "图纸图签部分显示的 专业负责人 字段后填写的 姓名",
                    "field_type": "text",
                    "patterns": [],
                    "ai_prompt": "提取图纸图签部分显示的 专业负责人 字段后填写的 第一个姓名，若姓名为空，该字段可以为空",
                    "required": True,
                    "validation_rules": None
                },
                "项目编号": {
                    "name": "项目编号",
                    "description": "图纸图签部分显示的 项目编号 字段后填写的 信息",
                    "field_type": "text",
                    "patterns": [],
                    "ai_prompt": "提取图纸图签部分显示的 项目编号 字段后填写的 信息（仅包含字母、数字和“-”），若为空，该字段可以为空",
                    "required": True,
                    "validation_rules": None
                },
                "图纸编号": {
                    "name": "图纸编号",
                    "description": "图纸图签部分显示的 图纸编号 字段后填写的 信息",
                    "field_type": "text",
                    "patterns": [],
                    "ai_prompt": "提取图纸图签部分显示的 图纸编号 字段后填写的 信息（仅包含字母、数字和“-”），若为空，该字段可以为空",
                    "required": True,
                    "validation_rules": None
                },
                "设计阶段": {
                    "name": "设计阶段",
                    "description": "图纸图签部分显示的 设计阶段 字段后填写的 信息",
                    "field_type": "text",
                    "patterns": [],
                    "ai_prompt": "提取图纸图签部分显示的 设计阶段 字段后填写的 信息，若为空，该字段可以为空",
                    "required": True,
                    "validation_rules": None
                },
                "专业": {
                    "name": "专业",
                    "description": "图纸图签部分显示的 专业 字段后填写的 信息",
                    "field_type": "text",
                    "patterns": [],
                    "ai_prompt": "提取图纸图签部分显示的 专业 字段后填写的 信息，若为空，该字段可以为空",
                    "required": True,
                    "validation_rules": None
                },
                "出图日期": {
                    "name": "出图日期",
                    "description": "图纸图签部分显示的 出图日期 字段后填写的 信息",
                    "field_type": "date",
                    "patterns": [],
                    "ai_prompt": "提取图纸图签部分显示的 出图日期 字段后填写的 日期，若为空，该字段可以为空",
                    "required": False,
                    "validation_rules": None
                },
                "图纸比例": {
                    "name": "图纸比例",
                    "description": "图纸图签部分显示的 图纸比例 字段后填写的 信息",
                    "field_type": "text",
                    "patterns": [],
                    "ai_prompt": "提取图纸图签部分显示的 图纸比例 字段后填写的 信息，若为空，该字段可以为空",
                    "required": False,
                    "validation_rules": None
                }
            }
        }

    def process_drawing(self, image_path: str) -> Dict[str, Any]:
        """
        处理图纸，进行图签区域优化和OCR识别

        Args:
            image_path: 图片或PDF文件路径

        Returns:
            识别结果字典
        """
        try:
            self.logger.info(f"开始处理图纸: {image_path}")

            # 第一步：图片优化处理
            self.logger.info("步骤1: 图片优化处理...")
            optimized_path = self.image_optimizer.optimize_image_for_drawing(image_path)

            # 第二步：OCR识别
            self.logger.info("步骤2: OCR识别...")
            ocr_result = self.ocr_tool.process_invoice(optimized_path)

            if not ocr_result:
                self.logger.warning("OCR识别失败，返回空结果")
                return {
                    '图片路径': image_path,
                    '处理时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    '解析方式': '图纸图签识别',
                    'AI置信度': 0.0,
                    '提取字段': {},
                    '优化路径': optimized_path,
                    '原始路径': image_path,
                    'OCR状态': '失败'
                }

            # 安全的OCR结果访问函数
            def safe_get_ocr_result(key, default=''):
                if hasattr(ocr_result, 'get') and callable(getattr(ocr_result, 'get')):
                    return ocr_result.get(key, default)
                elif isinstance(ocr_result, dict):
                    return ocr_result.get(key, default)
                else:
                    self.logger.warning(f"OCR结果格式异常，无法安全访问字段: {key}")
                    return default

            # 第三步：AI智能提取
            self.logger.info("步骤3: AI智能提取...")
            try:
                # 使用图纸特定的AI提示词
                ai_result = self.ai_parser.extract_fields_with_config(
                    safe_get_ocr_result('OCR原始结果', ''),
                    self.drawing_config
                )

                # 合并结果
                if ai_result and ai_result.get('提取字段'):
                    result_data = {
                        '图片路径': image_path,
                        '处理时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        '解析方式': '🤖 图纸图签AI智能解析',
                        'AI置信度': ai_result.get('ai_confidence', 0.0),
                        '提取字段': ai_result['提取字段'],
                        'OCR原始结果': safe_get_ocr_result('OCR原始结果'),
                        '优化路径': optimized_path,
                        '原始路径': image_path,
                        'OCR状态': '成功',
                        'AI状态': '成功'
                    }
                else:
                    result_data = {
                        '图片路径': image_path,
                        '处理时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        '解析方式': '图纸图签识别',
                        'AI置信度': 0.0,
                        '提取字段': safe_get_ocr_result('提取字段', {}),
                        'OCR原始结果': safe_get_ocr_result('OCR原始结果'),
                        '优化路径': optimized_path,
                        '原始路径': image_path,
                        'OCR状态': '成功',
                        'AI状态': '失败'
                    }
            except Exception as e:
                self.logger.error(f"AI提取失败: {e}")
                result_data = {
                    '图片路径': image_path,
                    '处理时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    '解析方式': '图纸图签识别',
                    'AI置信度': 0.0,
                    '提取字段': safe_get_ocr_result('提取字段', {}),
                    'OCR原始结果': safe_get_ocr_result('OCR原始结果'),
                    '优化路径': optimized_path,
                    '原始路径': image_path,
                    'OCR状态': '成功',
                    'AI状态': '异常'
                }

            # 添加处理统计
            result_data['处理统计'] = {
                '图片优化': optimized_path != image_path,
                '图签检测': '成功' if optimized_path != image_path else '跳过',
                '字段数量': len(result_data.get('提取字段', {})),
                '必填字段': len([k for k, v in self.drawing_config.get('fields', {}).items()
                                if v.get('required', False)]),
                '可选字段': len([k for k, v in self.drawing_config.get('fields', {}).items()
                                if not v.get('required', False)])
            }

            self.logger.info(f"图纸处理完成: 提取了{len(result_data.get('提取字段', {}))}个字段")
            return result_data

        except Exception as e:
            self.logger.error(f"图纸处理失败: {e}")
            return {
                '图片路径': image_path,
                '处理时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '解析方式': '图纸图签识别',
                'AI置信度': 0.0,
                '提取字段': {},
                'OCR原始结果': '',
                '优化路径': image_path,
                '原始路径': image_path,
                'OCR状态': '异常',
                '处理统计': {}
            }

    def process_drawing_enhanced(self, image_path: str, enable_signature_matching: bool = True) -> Dict[str, Any]:
        """
        增强的图纸处理方法，集成手写体识别和匹配功能

        Args:
            image_path: 图片或PDF文件路径
            enable_signature_matching: 是否启用签名匹配功能

        Returns:
            识别结果字典
        """
        try:
            self.logger.info(f"开始增强图纸处理: {image_path}")

            # 第一步：增强图签区域检测
            self.logger.info("步骤1: 增强图签区域检测...")
            signature_region = self.signature_detector.detect_signature_region_enhanced(image_path)

            if signature_region:
                self.logger.info(f"检测到图签区域: {signature_region}")

                # 保存检测结果调试图片
                self.signature_detector.save_detection_debug(image_path, signature_region)

                # 裁剪图签区域
                cropped_image = self._crop_signature_region(image_path, signature_region)
                if cropped_image:
                    optimized_path = self._save_cropped_image(image_path, cropped_image)
                    self.logger.info(f"图签区域裁剪成功: {optimized_path}")
                else:
                    self.logger.warning("图签区域裁剪失败，使用原图")
                    optimized_path = image_path
            else:
                self.logger.warning("未检测到图签区域，使用原图")
                optimized_path = image_path

            # 第二步：OCR识别和表格结构提取
            self.logger.info("步骤2: OCR识别和表格结构提取...")
            ocr_result = self.ocr_tool.process_invoice(optimized_path)

            # 安全的OCR结果访问函数 - 修复版
            def safe_get_ocr_result_enhanced(key, default=''):
                """安全的OCR结果访问函数 - 修复版"""
                if ocr_result is None:
                    self.logger.warning("OCR结果为None")
                    return default

                # 直接访问InvoiceResult对象的属性
                if hasattr(ocr_result, 'full_text'):
                    if key == 'OCR原始结果':
                        return ocr_result.full_text
                    elif hasattr(ocr_result, key):
                        return getattr(ocr_result, key, default)

                # 如果不是InvoiceResult对象，尝试字典访问
                if isinstance(ocr_result, dict) and hasattr(ocr_result, 'get'):
                    return ocr_result.get(key, default)

                self.logger.warning(f"无法访问OCR结果字段: {key}")
                return default

            table_structure = self._extract_table_structure(image_path, signature_region)

            # 第三步：手写签名识别和匹配
            signature_matches = {}
            if enable_signature_matching and signature_region:
                self.logger.info("步骤3: 手写签名识别和匹配...")
                signature_matches = self._extract_and_match_signatures(image_path, table_structure)

            # 第四步：AI智能提取
            self.logger.info("步骤4: AI智能提取...")
            final_fields = self._extract_fields_with_signatures(
                ocr_result, table_structure, signature_matches
            )

            # 构建结果
            result_data = {
                '图片路径': image_path,
                '处理时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '解析方式': '🤖 图纸图签增强AI解析',
                'AI置信度': 100.0,  # 增强模式默认高置信度
                '提取字段': final_fields,
                'OCR原始结果': safe_get_ocr_result_enhanced('OCR原始结果', ''),
                '表格结构': table_structure,
                '签名匹配': signature_matches,
                '图签区域': signature_region,
                '优化路径': optimized_path,
                '原始路径': image_path,
                'OCR状态': '成功',
                'AI状态': '成功',
                '增强功能': {
                    '图签检测': signature_region is not None,
                    '表格分析': len(table_structure) > 0,
                    '签名匹配': len(signature_matches) > 0,
                    '自动建库': any(match.get('auto_added', False) for match in signature_matches.values())
                }
            }

            # 添加处理统计
            result_data['处理统计'] = {
                '图签检测': '成功' if signature_region else '失败',
                '表格单元数': len(table_structure),
                '识别字段数': len(final_fields),
                '签名匹配数': len(signature_matches),
                '自动建库数': sum(1 for match in signature_matches.values() if match.get('auto_added', False))
            }

            self.logger.info(f"增强图纸处理完成: 识别了{len(final_fields)}个字段，匹配了{len(signature_matches)}个签名")
            return result_data

        except Exception as e:
            self.logger.error(f"增强图纸处理失败: {e}")
            return {
                '图片路径': image_path,
                '处理时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '解析方式': '图纸图签增强识别',
                'AI置信度': 0.0,
                '提取字段': {},
                'OCR原始结果': '',
                '表格结构': [],
                '签名匹配': {},
                '优化路径': image_path,
                '原始路径': image_path,
                'OCR状态': '异常',
                'AI状态': '异常'
            }

    def _crop_signature_region(self, image_path: str, signature_region: Tuple[int, int, int, int]) -> Image.Image:
        """裁剪图签区域"""
        try:
            # 检查是否为PDF文件
            if image_path.lower().endswith('.pdf'):
                self.logger.info("检测到PDF文件，使用OCR工具的PDF渲染功能")
                # 对于PDF文件，我们需要先渲染为图像，然后裁剪
                try:
                    import pypdfium2 as pdfium
                    import io

                    # 打开PDF文件
                    pdf = pdfium.PdfDocument(image_path)
                    page = pdf[0]

                    # 渲染页面为图像
                    bitmap = page.render(
                        scale=4.0,  # 高分辨率
                        crop=(0, 0, 0, 0),
                        rotation=0,
                        grayscale=False,
                    )

                    # 转换为PIL Image
                    img = bitmap.to_pil()
                    pdf.close()

                    self.logger.info(f"PDF渲染成功，图像尺寸: {img.size}")

                except Exception as pdf_error:
                    self.logger.error(f"PDF渲染失败: {pdf_error}")
                    # 如果PDF渲染失败，返回原图
                    return None
            else:
                # 对于图片文件，直接打开
                img = Image.open(image_path)

            # 进行裁剪
            left, top, right, bottom = signature_region

            # 添加边距
            margin = 10
            left = max(0, left - margin)
            top = max(0, top - margin)
            right = min(img.width, right + margin)
            bottom = min(img.height, bottom + margin)

            return img.crop((left, top, right, bottom))

        except Exception as e:
            self.logger.error(f"裁剪图签区域失败: {e}")
            return None

    def _save_cropped_image(self, image_path: str, cropped_image: Image.Image) -> str:
        """保存裁剪后的图像"""
        try:
            base_name = os.path.splitext(image_path)[0]
            cropped_path = f"{base_name}_signature_enhanced.png"
            cropped_image.save(cropped_path, 'PNG')
            return cropped_path
        except Exception as e:
            self.logger.error(f"保存裁剪图像失败: {e}")
            return image_path

    def _extract_table_structure(self, image_path: str, signature_region: Optional[Tuple[int, int, int, int]]) -> List[Dict]:
        """提取表格结构"""
        try:
            if not signature_region:
                return []

            image = cv2.imread(image_path)
            if image is None:
                return []

            return self.signature_detector.extract_table_structure(image, signature_region)

        except Exception as e:
            self.logger.error(f"表格结构提取失败: {e}")
            return []

    def _extract_and_match_signatures(self, image_path: str, table_structure: List[Dict]) -> Dict[str, Any]:
        """提取和匹配手写签名"""
        try:
            signature_matches = {}

            if not table_structure:
                return signature_matches

            # 分析表格结构，识别姓名字段和对应的签名区域
            name_signature_pairs = self._pair_names_with_signatures(table_structure)

            for printed_name, signature_region in name_signature_pairs:
                if signature_region:
                    # 提取签名图像
                    signature_image = self._extract_signature_image(image_path, signature_region)

                    if signature_image is not None:
                        # 匹配签名
                        matches = self.signature_manager.match_signature(signature_image)

                        if matches:
                            # 找到最佳匹配
                            best_match = matches[0]
                            signature_matches[printed_name] = {
                                'matched_name': best_match['printed_name'],
                                'user_id': best_match['user_id'],
                                'confidence': best_match['max_similarity'],
                                'match_type': 'existing',
                                'signature_region': signature_region
                            }
                        else:
                            # 未找到匹配，自动添加到数据库
                            user_id = f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(signature_matches)}"
                            success = self.signature_manager.add_signature(printed_name, signature_image, user_id)

                            if success:
                                signature_matches[printed_name] = {
                                    'matched_name': printed_name,
                                    'user_id': user_id,
                                    'confidence': 1.0,  # 新添加的签名默认高置信度
                                    'match_type': 'auto_added',
                                    'signature_region': signature_region,
                                    'auto_added': True
                                }
                                self.logger.info(f"自动添加新签名: {printed_name}")

            return signature_matches

        except Exception as e:
            self.logger.error(f"签名提取和匹配失败: {e}")
            return {}

    def _pair_names_with_signatures(self, table_structure: List[Dict]) -> List[Tuple[str, Tuple[int, int, int, int]]]:
        """配对姓名和签名区域"""
        try:
            name_signature_pairs = []

            # 简化实现：寻找包含"姓名"、"设计人"等关键词的文本框
            # 然后在其右侧寻找可能的签名区域

            # 提取姓名文本框
            name_boxes = []
            for cell in table_structure:
                text = cell.get('text', '').strip()
                if any(keyword in text for keyword in ['姓名', '设计人', '审核人', '审定人', '校核人', '绘图人']):
                    # 提取冒号后面的姓名
                    if ':' in text:
                        name = text.split(':')[-1].strip()
                        if name and len(name) <= 10:  # 合理的姓名长度
                            name_boxes.append((name, cell))

            # 为每个姓名框寻找签名区域（在右侧）
            for name, cell in name_boxes:
                cell_center_x = cell['center_x']
                cell_center_y = cell['center_y']

                # 寻找右侧最近的空白区域作为签名区域
                signature_candidates = []
                for other_cell in table_structure:
                    if other_cell != cell:
                        # 检查是否在右侧
                        if (other_cell['center_x'] > cell_center_x and
                            abs(other_cell['center_y'] - cell_center_y) < 50):

                            # 检查文本是否为空或很少字符（可能是手写签名区域）
                            text = other_cell.get('text', '').strip()
                            if len(text) <= 3:  # 很少文字，可能是签名区域
                                distance = other_cell['center_x'] - cell_center_x
                                signature_candidates.append((distance, other_cell))

                if signature_candidates:
                    # 选择最近的签名区域
                    signature_candidates.sort(key=lambda x: x[0])
                    signature_cell = signature_candidates[0][1]

                    # 构建签名区域坐标
                    box = signature_cell['box']
                    signature_region = (
                        int(min(point[0] for point in box)),
                        int(min(point[1] for point in box)),
                        int(max(point[0] for point in box)),
                        int(max(point[1] for point in box))
                    )

                    name_signature_pairs.append((name, signature_region))

            return name_signature_pairs

        except Exception as e:
            self.logger.error(f"姓名签名配对失败: {e}")
            return []

    def _extract_signature_image(self, image_path: str, signature_region: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        """提取签名图像"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return None

            left, top, right, bottom = signature_region

            # 裁剪签名区域
            signature_img = image[top:bottom, left:right]

            # 转换为灰度图
            if len(signature_img.shape) == 3:
                signature_gray = cv2.cvtColor(signature_img, cv2.COLOR_BGR2GRAY)
            else:
                signature_gray = signature_img

            return signature_gray

        except Exception as e:
            self.logger.error(f"提取签名图像失败: {e}")
            return None

    def _extract_fields_with_signatures(self, ocr_result: Dict, table_structure: List[Dict],
                                      signature_matches: Dict[str, Any]) -> Dict[str, str]:
        """结合签名匹配结果提取字段"""
        try:
            # 安全获取OCR提取的字段
            if hasattr(ocr_result, 'get') and callable(getattr(ocr_result, 'get')):
                ocr_fields = ocr_result.get('提取字段', {})
            elif isinstance(ocr_result, dict):
                ocr_fields = ocr_result.get('提取字段', {})
            else:
                self.logger.warning("OCR结果格式异常，使用空字段字典")
                ocr_fields = {}

            # 增强字段信息，添加签名匹配结果
            enhanced_fields = ocr_fields.copy()

            for printed_name, match_info in signature_matches.items():
                # 查找对应的字段
                matching_field = None
                for field_name in enhanced_fields:
                    if printed_name in field_name or any(keyword in field_name
                                                        for keyword in ['设计人', '审核人', '审定人', '校核人', '绘图人']):
                        matching_field = field_name
                        break

                if matching_field:
                    # 添加签名匹配信息
                    if match_info['match_type'] == 'existing':
                        enhanced_fields[f"{matching_field}_签名验证"] = f"✅ 已匹配 ({match_info['confidence']:.2f})"
                    elif match_info['match_type'] == 'auto_added':
                        enhanced_fields[f"{matching_field}_签名验证"] = f"🆕 自动建库"

            return enhanced_fields

        except Exception as e:
            self.logger.error(f"字段提取失败: {e}")
            # 安全返回字段
            if hasattr(ocr_result, 'get') and callable(getattr(ocr_result, 'get')):
                return ocr_result.get('提取字段', {})
            elif isinstance(ocr_result, dict):
                return ocr_result.get('提取字段', {})
            else:
                self.logger.warning("OCR结果格式异常，返回空字段字典")
                return {}

    def train_signature_model(self, training_data_path: str) -> bool:
        """
        训练签名识别模型（预留接口）

        Args:
            training_data_path: 训练数据路径

        Returns:
            是否训练成功
        """
        try:
            self.logger.info(f"开始训练签名模型: {training_data_path}")

            # TODO: 实现签名模型训练逻辑
            # 1. 加载训练数据
            # 2. 数据预处理
            # 3. 模型训练
            # 4. 模型评估和保存

            self.logger.info("签名模型训练功能待实现")
            return True

        except Exception as e:
            self.logger.error(f"签名模型训练失败: {e}")
            return False

    def get_signature_statistics(self) -> Dict[str, Any]:
        """获取签名数据库统计信息"""
        try:
            users = self.signature_manager.list_all_users()

            total_users = len(users)
            total_signatures = sum(user['sample_count'] for user in users)

            # 按样本数统计
            sample_distribution = {}
            for user in users:
                count = user['sample_count']
                sample_distribution[count] = sample_distribution.get(count, 0) + 1

            return {
                'total_users': total_users,
                'total_signatures': total_signatures,
                'average_samples': total_signatures / total_users if total_users > 0 else 0,
                'sample_distribution': sample_distribution,
                'recent_users': [user for user in users[:5]]  # 最近5个用户
            }

        except Exception as e:
            self.logger.error(f"获取签名统计失败: {e}")
            return {}

    def export_drawing_result(self, result: Dict[str, Any], file_path: str) -> bool:
        """
        导出图纸识别结果

        Args:
            result: 识别结果字典
            file_path: 导出文件路径

        Returns:
            导出是否成功
        """
        try:
            from .excel_exporter import ExcelExporter

            exporter = ExcelExporter()

            # 使用图纸配置进行导出
            excel_result = exporter.export_single_invoice(
                file_path, result, "horizontal", self.drawing_config
            )

            return excel_result

        except Exception as e:
            self.logger.error(f"Excel导出失败: {e}")
            return False


def main():
    """测试图纸OCR识别功能"""
    logging.basicConfig(level=logging.INFO)

    ocr_tool = DrawingOCRTool()

    # 测试图片
    test_image = "examples/test_invoice.png"  # 可以替换为实际的图纸图片

    if os.path.exists(test_image):
        print(f"测试图纸识别: {test_image}")
        result = ocr_tool.process_drawing(test_image)

        print(f"\n识别结果:")
        print(f"处理时间: {result.get('处理时间')}")
        print(f"解析方式: {result.get('解析方式')}")
        print(f"AI置信度: {result.get('AI置信度'):.1%}")
        print(f"提取字段数: {len(result.get('提取字段', {}))}")

        if result.get('提取字段'):
            print(f"\n提取的字段:")
            for field_name, field_value in result.get('提取字段').items():
                status = "✅" if field_value else "❌"
                print(f"  {field_name}: {field_value or '未识别'} {status}")

        # 测试导出
        export_path = "test_drawing_result.xlsx"
        if ocr_tool.export_drawing_result(result, export_path):
            print(f"\n✅ 结果已导出到: {export_path}")
        else:
            print(f"\n❌ 导出失败")
    else:
        print(f"测试图片不存在: {test_image}")


if __name__ == "__main__":
    main()