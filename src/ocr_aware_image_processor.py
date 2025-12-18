#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR导向的图片处理器
专门针对OCR识别优化的图片预处理模块
"""

import logging
import os
from typing import Tuple, Optional
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np


class OCRAwareImageProcessor:
    """OCR导向的图片处理器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process_for_ocr(self, image_path: str, ocr_type: str = 'general') -> str:
        """
        为OCR处理图片

        Args:
            image_path: 原始图片路径
            ocr_type: OCR类型 ('general', 'signature', 'text')

        Returns:
            处理后图片路径
        """
        try:
            self.logger.info(f"开始OCR导向处理: {image_path}, 类型: {ocr_type}")

            with Image.open(image_path) as img:
                original_size = img.size
                original_mode = img.mode
                self.logger.info(f"原图信息: {original_size}, 模式: {original_mode}")

                # 确保为RGB模式
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # 根据OCR类型选择处理策略
                if ocr_type == 'signature':
                    processed_img = self._process_for_signature(img)
                elif ocr_type == 'text':
                    processed_img = self._process_for_text(img)
                else:
                    processed_img = self._process_for_general_ocr(img)

                # 检查处理效果
                processed_size = processed_img.size
                self.logger.info(f"处理后信息: {processed_size}")

                # 保存为高质量图片
                output_path = self._get_ocr_optimized_path(image_path, ocr_type)
                self._save_ocr_optimized(processed_img, output_path)

                self.logger.info(f"OCR导向处理完成: {output_path}")
                return output_path

        except Exception as e:
            self.logger.error(f"OCR导向处理失败: {e}")
            return image_path

    def _process_for_signature(self, image: Image.Image) -> Image.Image:
        """专门处理图签区域的图片"""
        try:
            # 针对图签优化：保持高分辨率，增强文字对比度
            processed = image.copy()

            # 智能缩放：确保文字足够清晰
            min_dpi = 300  # OCR最低DPI要求
            current_dpi = self._estimate_dpi(image)

            if current_dpi < min_dpi:
                scale_factor = min_dpi / current_dpi
                new_size = (int(image.width * scale_factor), int(image.height * scale_factor))
                processed = processed.resize(new_size, Image.Resampling.LANCZOS)
                self.logger.info(f"提升分辨率: {current_dpi:.1f} → {min_dpi} DPI")

            # 图签文字增强（更保守的处理）
            processed = self._enhance_text_clarity(processed, gentle=True)

            return processed

        except Exception as e:
            self.logger.error(f"图签处理失败: {e}")
            return image

    def _process_for_text(self, image: Image.Image) -> Image.Image:
        """专门处理文本文档的图片"""
        try:
            processed = image.copy()

            # 文档优化：保持或提升到合适的DPI
            optimal_dpi = 200  # 文档OCR最佳DPI
            current_dpi = self._estimate_dpi(image)

            if current_dpi < optimal_dpi:
                scale_factor = optimal_dpi / current_dpi
                new_size = (int(image.width * scale_factor), int(image.height * scale_factor))
                processed = processed.resize(new_size, Image.Resampling.LANCZOS)
                self.logger.info(f"文档分辨率调整: {current_dpi:.1f} → {optimal_dpi} DPI")

            # 文档文字增强
            processed = self._enhance_document_text(processed)

            return processed

        except Exception as e:
            self.logger.error(f"文档处理失败: {e}")
            return image

    def _process_for_general_ocr(self, image: Image.Image) -> Image.Image:
        """通用OCR处理"""
        try:
            processed = image.copy()

            # 通用优化：保持合适的大小和清晰度
            max_size = 4000  # 提高最大尺寸限制
            if image.width > max_size or image.height > max_size:
                ratio = min(max_size / image.width, max_size / image.height)
                new_size = (int(image.width * ratio), int(image.height * ratio))
                processed = processed.resize(new_size, Image.Resampling.LANCZOS)
                self.logger.info(f"通用尺寸调整: {image.size} → {new_size}")

            # 通用文字增强
            processed = self._enhance_general_text(processed)

            return processed

        except Exception as e:
            self.logger.error(f"通用OCR处理失败: {e}")
            return image

    def _estimate_dpi(self, image: Image.Image) -> float:
        """估算图片的DPI"""
        # 简单估算：基于图片尺寸和假设的物理尺寸
        # 这是一个粗略估算，实际应用中可能需要更复杂的逻辑

        # 假设A4纸大小的图片约为2480x3508像素对应300 DPI
        a4_width_300dpi = 2480
        a4_height_300dpi = 3508

        # 计算相对于A4纸的比例
        width_ratio = image.width / a4_width_300dpi
        height_ratio = image.height / a4_height_300dpi

        # 使用较小值来估算DPI（保守估计）
        dpi_estimate = min(width_ratio, height_ratio) * 300

        return max(dpi_estimate, 72)  # 最低72 DPI

    def _enhance_text_clarity(self, image: Image.Image, gentle: bool = True) -> Image.Image:
        """增强文字清晰度"""
        try:
            processed = image.copy()

            if gentle:
                # 温和的增强：适合图签等需要保持原始外观的场景
                enhancer = ImageEnhance.Contrast(processed)
                processed = enhancer.enhance(1.2)  # 温和的对比度增强

                enhancer = ImageEnhance.Sharpness(processed)
                processed = enhancer.enhance(1.1)  # 温和的锐化

            else:
                # 标准增强：适合一般文档
                enhancer = ImageEnhance.Contrast(processed)
                processed = enhancer.enhance(1.3)

                enhancer = ImageEnhance.Sharpness(processed)
                processed = enhancer.enhance(1.2)

            return processed

        except Exception as e:
            self.logger.error(f"文字清晰度增强失败: {e}")
            return image

    def _enhance_document_text(self, image: Image.Image) -> Image.Image:
        """增强文档文字"""
        try:
            processed = image.copy()

            # 文档专用增强
            enhancer = ImageEnhance.Contrast(processed)
            processed = enhancer.enhance(1.25)

            enhancer = ImageEnhance.Sharpness(processed)
            processed = enhancer.enhance(1.15)

            # 亮度调整：确保不会过暗或过亮
            enhancer = ImageEnhance.Brightness(processed)
            processed = enhancer.enhance(1.05)

            return processed

        except Exception as e:
            self.logger.error(f"文档文字增强失败: {e}")
            return image

    def _enhance_general_text(self, image: Image.Image) -> Image.Image:
        """通用文字增强"""
        try:
            processed = image.copy()

            # 保守的通用增强
            enhancer = ImageEnhance.Contrast(processed)
            processed = enhancer.enhance(1.15)

            return processed

        except Exception as e:
            self.logger.error(f"通用文字增强失败: {e}")
            return image

    def _save_ocr_optimized(self, image: Image.Image, output_path: str):
        """保存为OCR优化的图片"""
        try:
            # 使用无损PNG格式保存，保持最佳质量
            image.save(output_path, 'PNG', optimize=True)

            # 记录文件大小变化
            original_size = len(image.tobytes())
            file_size = os.path.getsize(output_path)
            compression_ratio = (original_size - file_size) / original_size if original_size > 0 else 0

            self.logger.info(f"图片保存完成: {output_path}, 压缩率: {compression_ratio:.1%}")

        except Exception as e:
            self.logger.error(f"图片保存失败: {e}")

    def _get_ocr_optimized_path(self, original_path: str, ocr_type: str) -> str:
        """获取OCR优化后的文件路径"""
        base_name = os.path.splitext(original_path)[0]
        return f"{base_name}_ocr_optimized_{ocr_type}.png"

    def analyze_image_quality(self, image_path: str) -> dict:
        """分析图片质量，为OCR处理提供建议"""
        try:
            with Image.open(image_path) as img:
                analysis = {
                    'file_path': image_path,
                    'size': img.size,
                    'mode': img.mode,
                    'file_size': os.path.getsize(image_path),
                    'estimated_dpi': self._estimate_dpi(img),
                    'aspect_ratio': img.width / img.height,
                    'recommended_processing': self._recommend_processing(img)
                }

                return analysis

        except Exception as e:
            self.logger.error(f"图片质量分析失败: {e}")
            return {}

    def _recommend_processing(self, image: Image.Image) -> str:
        """推荐处理方式"""
        dpi = self._estimate_dpi(image)
        megapixels = (image.width * image.height) / 1000000

        if dpi < 150:
            return "需要分辨率提升处理"
        elif megapixels > 8:
            return "需要尺寸优化处理"
        elif dpi < 200:
            return "建议文字增强处理"
        else:
            return "图片质量良好，适合OCR处理"


def main():
    """测试OCR导向图片处理器"""
    logging.basicConfig(level=logging.INFO)

    processor = OCRAwareImageProcessor()

    # 查找测试图片
    test_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                test_files.append(os.path.join(root, file))

    if not test_files:
        print("没有找到测试图片")
        return

    test_file = test_files[0]
    print(f"测试文件: {test_file}")

    # 分析原始图片质量
    analysis = processor.analyze_image_quality(test_file)
    print(f"\n图片质量分析:")
    for key, value in analysis.items():
        print(f"  {key}: {value}")

    # 测试不同处理方式
    processing_types = ['general', 'signature', 'text']

    for proc_type in processing_types:
        print(f"\n测试 {proc_type} 处理:")
        result_path = processor.process_for_ocr(test_file, proc_type)

        if result_path != test_file:
            original_size = os.path.getsize(test_file)
            processed_size = os.path.getsize(result_path)
            print(f"  处理成功: {result_path}")
            print(f"  文件大小: {original_size:,} → {processed_size:,} bytes")
            print(f"  大小变化: {((processed_size - original_size) / original_size * 100):+.1f}%")


if __name__ == "__main__":
    main()