#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片优化处理模块
专门针对图纸图签区域的智能检测和裁剪优化
"""

import logging
import os
from typing import Tuple, Optional, List
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np


class ImageOptimizer:
    """图片优化处理器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def optimize_image_for_drawing(self, image_path: str, lossless_mode: bool = True) -> str:
        """
        为图纸识别优化图片处理

        Args:
            image_path: 原始图片路径
            lossless_mode: 是否启用完全无损模式

        Returns:
            优化后的图片路径
        """
        try:
            self.logger.info(f"开始图纸图片处理: {image_path}, 无损模式: {lossless_mode}")

            # 如果启用无损模式，使用无损处理器
            if lossless_mode:
                from lossless_image_processor import LosslessImageProcessor
                lossless_processor = LosslessImageProcessor()

                # 首先检测图签区域
                with Image.open(image_path) as img:
                    original_size = img.size
                    self.logger.info(f"原始图片尺寸: {original_size}")

                    signature_region = self.detect_signature_region(img)
                    if signature_region:
                        self.logger.info(f"检测到图签区域: {signature_region}")

                        # 无损裁剪图签区域
                        cropped_img = self.crop_signature_region(img, signature_region)

                        # 保存裁剪后的图签区域（无损）
                        cropped_path = self._get_cropped_path(image_path)
                        self._save_lossless(cropped_img, cropped_path)
                        self.logger.info(f"无损裁剪完成: {cropped_path}")

                        return cropped_path
                    else:
                        # 没有检测到图签区域，使用无损通用处理
                        self.logger.info("未检测到图签区域，使用无损通用处理")
                        return lossless_processor.process_for_lossless_ocr(image_path, 'preserve')
            else:
                # 传统优化模式（保留兼容性）
                return self._traditional_optimize(image_path)

        except Exception as e:
            self.logger.error(f"图纸图片处理失败: {e}")
            return image_path

    def _traditional_optimize(self, image_path: str) -> str:
        """传统的图片优化模式（保留兼容性）"""
        try:
            # 打开原始图片
            with Image.open(image_path) as img:
                original_size = img.size
                self.logger.info(f"原始图片尺寸: {original_size}")

                # 检测图签区域
                signature_region = self.detect_signature_region(img)
                if signature_region:
                    self.logger.info(f"检测到图签区域: {signature_region}")

                    # 裁剪图签区域
                    cropped_img = self.crop_signature_region(img, signature_region)

                    # 进一步优化裁剪后的图片
                    optimized_img = self.enhance_signature_region(cropped_img)

                    # 保存优化后的图片
                    output_path = self._get_optimized_path(image_path)
                    self._save_lossless(optimized_img, output_path)

                    self.logger.info(f"传统优化完成: {output_path}")
                    return output_path
                else:
                    # 如果没有检测到图签区域，使用通用优化
                    return self._general_optimize(image_path)

        except Exception as e:
            self.logger.error(f"传统优化失败: {e}")
            return image_path

    def _save_lossless(self, image: Image.Image, output_path: str):
        """完全无损保存"""
        try:
            # 使用最高质量设置，零压缩
            save_params = {
                'format': 'PNG',
                'optimize': False,  # 关闭优化
                'compress_level': 0,  # 无压缩
            }

            image.save(output_path, **save_params)
            file_size = os.path.getsize(output_path)
            self.logger.info(f"无损保存完成: {output_path}, 文件大小: {file_size:,} bytes")

        except Exception as e:
            self.logger.error(f"无损保存失败: {e}")

    def _get_cropped_path(self, original_path: str) -> str:
        """获取裁剪后的图片路径"""
        base_name = os.path.splitext(original_path)[0]
        return f"{base_name}_signature_crop.png"

    def detect_signature_region(self, image: Image.Image) -> Optional[Tuple[int, int, int, int]]:
        """
        检测图片中的图签区域

        Args:
            image: PIL图像对象

        Returns:
            图签区域的坐标 (left, top, right, bottom) 或 None
        """
        try:
            # 转换为OpenCV格式
            img_array = np.array(image)
            if len(img_array.shape) == 3:
                # RGB转灰度
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            height, width = gray.shape

            # 图签通常在图片的底部右侧区域
            # 首先尝试检测底部区域
            bottom_region_height = int(height * 0.3)  # 底部30%
            right_region_width = int(width * 0.4)    # 右侧40%

            bottom_region = gray[height - bottom_region_height:height, :]

            # 边缘检测
            edges = cv2.Canny(bottom_region, 50, 150, apertureSize=3)

            # 查找轮廓
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # 筛选可能的图签区域
            signature_candidates = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)

                # 转换为全图坐标
                global_x = x
                global_y = y + (height - bottom_region_height)
                global_w = w
                global_h = h

                # 图签特征检查
                if self._is_signature_candidate(global_x, global_y, global_w, global_h, width, height):
                    confidence = self._calculate_signature_confidence(
                        global_x, global_y, global_w, global_h, width, height, edges
                    )
                    signature_candidates.append((global_x, global_y, global_w, global_h, confidence))

            if signature_candidates:
                # 选择置信度最高的候选区域
                best_candidate = max(signature_candidates, key=lambda x: x[4])
                return (best_candidate[0], best_candidate[1],
                       best_candidate[0] + best_candidate[2],
                       best_candidate[1] + best_candidate[3])

            # 如果没有检测到，尝试模板匹配方法
            return self._template_based_detection(gray, width, height)

        except Exception as e:
            self.logger.error(f"图签区域检测失败: {e}")
            return None

    def _is_signature_candidate(self, x: int, y: int, w: int, h: int,
                                image_width: int, image_height: int) -> bool:
        """判断是否为图签候选区域"""
        # 图签通常在底部右侧
        is_bottom_region = y > image_height * 0.7  # 底部30%区域
        is_right_region = x > image_width * 0.6    # 右侧40%区域

        # 合理的尺寸范围
        min_width, max_width = 100, 800
        min_height, max_height = 50, 300
        size_ok = min_width <= w <= max_width and min_height <= h <= max_height

        # 宽高比检查（图签通常是横向的）
        aspect_ratio_ok = 1.5 <= (w/h) <= 5

        return is_bottom_region and is_right_region and size_ok and aspect_ratio_ok

    def _calculate_signature_confidence(self, x: int, y: int, w: int, h: int,
                                       image_width: int, image_height: int,
                                       edges: np.ndarray) -> float:
        """计算图签候选区域的置信度"""
        try:
            # 区域内的边缘密度
            region_edges = edges[y:(y+h), x:(x+w)]
            edge_density = np.sum(region_edges > 0) / (w * h)

            # 位置权重（底部右侧得分更高）
            position_weight = 0.0
            if y > image_height * 0.8:
                position_weight += 0.3  # 底部20%
            if y > image_height * 0.9:
                position_weight += 0.2  # 底部10%

            if x > image_width * 0.7:
                position_weight += 0.3  # 右侧30%
            if x > image_width * 0.8:
                position_weight += 0.2  # 右侧20%

            # 尺寸权重（适中尺寸得分更高）
            size_weight = 0.0
            ideal_width = image_width * 0.3
            ideal_height = image_height * 0.15

            width_diff = abs(w - ideal_width) / ideal_width
            height_diff = abs(h - ideal_height) / ideal_height

            if width_diff < 0.5:
                size_weight += 0.2
            if height_diff < 0.5:
                size_weight += 0.2

            return edge_density * 0.5 + position_weight * 0.3 + size_weight * 0.2

        except:
            return 0.0

    def _template_based_detection(self, gray_image: np.ndarray, width: int, height: int) -> Optional[Tuple[int, int, int, int]]:
        """基于模板的图签检测方法"""
        try:
            # 定义典型的图签区域（基于经验）
            # 图签通常在图片底部右侧，大约占图片的25-35%

            # 策选几个可能的图签区域
            candidates = [
                (int(width * 0.65), int(height * 0.75), int(width * 0.9), int(height * 0.95)),  # 右下区域
                (int(width * 0.7), int(height * 0.8), int(width * 0.95), int(height * 0.98)),   # 更右下
                (int(width * 0.6), int(height * 0.7), int(width * 0.85), int(height * 0.9)),     # 中右下区域
            ]

            best_candidate = None
            best_confidence = 0.0

            for x, y, x2, y2 in candidates:
                w, h = x2 - x, y2 - y

                # 检查该区域的文本密度
                region = gray_image[y:y2, x:x2]
                if region.size > 0:
                    # 使用拉普拉斯算子检测文本特征
                    laplacian_var = cv2.Laplacian(region, cv2.CV_64F).var()

                    # 文本区域的拉普拉斯方差通常较高
                    if laplacian_var > 100:  # 阈值可调整
                        confidence = min(laplacian_var / 1000, 1.0)

                        # 位置权重
                        if x > width * 0.7:
                            confidence += 0.2
                        if y > height * 0.8:
                            confidence += 0.2

                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_candidate = (x, y, x2, y2)

            return best_candidate

        except Exception as e:
            self.logger.error(f"模板检测失败: {e}")
            return None

    def crop_signature_region(self, image: Image.Image, region: Tuple[int, int, int, int]) -> Image.Image:
        """裁剪图签区域"""
        left, top, right, bottom = region

        # 添加边距，确保不会切掉重要信息
        margin = 10
        left = max(0, left - margin)
        top = max(0, top - margin)
        right = min(image.width, right + margin)
        bottom = min(image.height, bottom + margin)

        return image.crop((left, top, right, bottom))

    def enhance_signature_region(self, image: Image.Image) -> Image.Image:
        """增强图签区域的可识别性"""
        try:
            # 增强对比度
            enhancer = ImageEnhance.Contrast(image)
            enhanced = enhancer.enhance(1.5)

            # 锐化处理
            sharpened = enhanced.filter(ImageFilter.SHARPEN)

            # 增加亮度（如果图片较暗）
            brightness = ImageEnhance.Brightness(sharpened)
            bright_enhanced = brightness.enhance(1.1)

            return bright_enhanced

        except Exception as e:
            self.logger.error(f"图签区域增强失败: {e}")
            return image

    def _general_optimize(self, image_path: str) -> str:
        """OCR导向的通用图片优化"""
        try:
            with Image.open(image_path) as img:
                original_size = img.size
                self.logger.info(f"原始图片尺寸: {original_size}")

                # OCR导向处理：保持高DPI和文字清晰度
                processed_img = self._ocr_optimize_general(img)

                # 保存为高质量格式
                output_path = self._get_optimized_path(image_path)
                self._save_ocr_optimized(processed_img, output_path)

                self.logger.info(f"OCR导向优化完成: {output_path}")
                return output_path

        except Exception as e:
            self.logger.error(f"OCR导向优化失败: {e}")
            return image_path

    def _ocr_optimize_general(self, image: Image.Image) -> Image.Image:
        """OCR导向的通用优化"""
        try:
            processed = image.copy()

            # 确保为RGB模式
            if processed.mode != 'RGB':
                processed = processed.convert('RGB')

            # OCR优化：提升到合适的DPI
            current_dpi = self._estimate_dpi(processed)
            optimal_dpi = 200  # OCR推荐DPI

            if current_dpi < optimal_dpi:
                scale_factor = optimal_dpi / current_dpi
                new_size = (int(processed.width * scale_factor), int(processed.height * scale_factor))
                processed = processed.resize(new_size, Image.Resampling.LANCZOS)
                self.logger.info(f"DPI提升: {current_dpi:.1f} → {optimal_dpi} DPI")

            # 尺寸优化：更大的最大尺寸限制
            max_size = 4000
            if processed.width > max_size or processed.height > max_size:
                ratio = min(max_size / processed.width, max_size / processed.height)
                new_size = (int(processed.width * ratio), int(processed.height * ratio))
                processed = processed.resize(new_size, Image.Resampling.LANCZOS)
                self.logger.info(f"尺寸调整: {image.size} → {new_size}")

            # OCR专用文字增强（温和处理）
            processed = self._enhance_for_ocr(processed)

            return processed

        except Exception as e:
            self.logger.error(f"OCR优化失败: {e}")
            return image

    def _estimate_dpi(self, image: Image.Image) -> float:
        """估算图片DPI"""
        # 基于A4纸标准进行估算
        a4_width_300dpi = 2480  # A4纸在300 DPI下的宽度
        width_ratio = image.width / a4_width_300dpi
        dpi_estimate = width_ratio * 300
        return max(dpi_estimate, 72)  # 最低72 DPI

    def _enhance_for_ocr(self, image: Image.Image) -> Image.Image:
        """OCR专用文字增强"""
        try:
            # 温和的对比度增强，避免过度处理
            enhancer = ImageEnhance.Contrast(image)
            enhanced = enhancer.enhance(1.2)

            # 温和的锐化
            enhancer = ImageEnhance.Sharpness(enhanced)
            enhanced = enhancer.enhance(1.1)

            return enhanced

        except Exception as e:
            self.logger.error(f"OCR文字增强失败: {e}")
            return image

    def _save_ocr_optimized(self, image: Image.Image, output_path: str):
        """保存OCR优化后的图片"""
        try:
            # 使用无损PNG格式
            image.save(output_path, 'PNG', optimize=True)
            self.logger.info(f"OCR优化图片已保存: {output_path}")
        except Exception as e:
            self.logger.error(f"OCR优化图片保存失败: {e}")

    def _get_optimized_path(self, original_path: str) -> str:
        """获取优化后图片的保存路径"""
        base_name = os.path.splitext(original_path)[0]
        return f"{base_name}_optimized.png"

    def get_image_info(self, image_path: str) -> dict:
        """获取图片信息"""
        try:
            with Image.open(image_path) as img:
                return {
                    'path': image_path,
                    'size': img.size,
                    'mode': img.mode,
                    'format': img.format,
                    'file_size': os.path.getsize(image_path)
                }
        except Exception as e:
            self.logger.error(f"获取图片信息失败: {e}")
            return {}


def main():
    """测试图片优化功能"""
    logging.basicConfig(level=logging.INFO)

    optimizer = ImageOptimizer()

    # 测试图片处理
    test_images = [
        "examples/test_invoice.png",
        # 可以添加更多测试图片
    ]

    for image_path in test_images:
        if os.path.exists(image_path):
            print(f"\n处理图片: {image_path}")
            optimized_path = optimizer.optimize_image_for_drawing(image_path)

            if optimized_path != image_path:
                # 获取并显示优化前后的信息
                original_info = optimizer.get_image_info(image_path)
                optimized_info = optimizer.get_image_info(optimized_path)

                print(f"原始图片: {original_info['size']}")
                print(f"优化图片: {optimized_info['size']}")
                print(f"文件大小减少: {original_info['file_size'] - optimized_info['file_size']} bytes")


if __name__ == "__main__":
    main()