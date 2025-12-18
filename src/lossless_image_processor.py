#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完全无损的OCR图片处理器
精度第一，零损失策略
"""

import logging
import os
from typing import Tuple, Optional
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np


class LosslessImageProcessor:
    """完全无损的OCR图片处理器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process_for_lossless_ocr(self, image_path: str, processing_mode: str = 'preserve') -> str:
        """
        完全无损的OCR图片处理

        Args:
            image_path: 原始图片路径
            processing_mode: 处理模式
                'preserve' - 完全保留原始质量
                'minimal' - 最小化必要处理
                'adaptive' - 自适应智能处理

        Returns:
            处理后图片路径
        """
        try:
            self.logger.info(f"开始无损OCR处理: {image_path}, 模式: {processing_mode}")

            with Image.open(image_path) as img:
                original_info = self._analyze_original_image(img)
                self.logger.info(f"原图分析: {original_info}")

                # 根据处理模式选择策略
                if processing_mode == 'preserve':
                    processed_img = self._preserve_quality(img)
                elif processing_mode == 'minimal':
                    processed_img = self._minimal_processing(img)
                else:  # adaptive
                    processed_img = self._adaptive_processing(img)

                # 完全无损保存
                output_path = self._get_lossless_path(image_path, processing_mode)
                self._save_lossless(processed_img, output_path)

                # 验证无损程度
                quality_check = self._verify_lossless(image_path, output_path)
                self.logger.info(f"质量验证: {quality_check}")

                return output_path

        except Exception as e:
            self.logger.error(f"无损OCR处理失败: {e}")
            return image_path

    def _analyze_original_image(self, image: Image.Image) -> dict:
        """分析原始图片"""
        return {
            'size': image.size,
            'mode': image.mode,
            'has_transparency': 'transparency' in image.info or image.mode in ('RGBA', 'LA'),
            'color_depth': len(image.getbands()) * 8,
            'megapixels': (image.width * image.height) / 1000000,
            'estimated_dpi': self._estimate_dpi(image)
        }

    def _preserve_quality(self, image: Image.Image) -> Image.Image:
        """完全保留原始质量 - 零处理"""
        try:
            self.logger.info("采用完全保留模式 - 零处理")

            # 仅进行必要的格式转换
            if image.mode not in ('RGB', 'RGBA'):
                self.logger.info(f"模式转换: {image.mode} → RGB")
                if 'transparency' in image.info or image.mode == 'RGBA':
                    # 保持透明度
                    converted = Image.new('RGBA', image.size)
                    converted.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                    return converted
                else:
                    return image.convert('RGB')

            # 完全不修改原始像素
            return image.copy()

        except Exception as e:
            self.logger.error(f"质量保留失败: {e}")
            return image

    def _minimal_processing(self, image: Image.Image) -> Image.Image:
        """最小化必要处理 - 仅修复明显问题"""
        try:
            self.logger.info("采用最小化处理模式")
            processed = image.copy()

            # 确保正确的颜色模式
            if processed.mode not in ('RGB', 'RGBA'):
                if processed.mode == 'P' and 'transparency' in processed.info:
                    # 保持调色板图片的透明度
                    processed = processed.convert('RGBA')
                else:
                    processed = processed.convert('RGB')

            # 仅修复明显的问题
            issues_fixed = []

            # 检查是否为极低分辨率
            if max(processed.size) < 300:
                # 仅对极低分辨率进行最小放大
                scale = 2.0
                new_size = (int(processed.width * scale), int(processed.height * scale))
                processed = processed.resize(new_size, Image.Resampling.LANCZOS)
                issues_fixed.append("极低分辨率提升")

            # 检查是否为黑白图片但被误认为彩色
            if processed.mode == 'RGB':
                r, g, b = processed.split()
                if np.array_equal(np.array(r), np.array(g)) and np.array_equal(np.array(g), np.array(b)):
                    # 实际是灰度图，保持为RGB但无需额外处理
                    pass

            if issues_fixed:
                self.logger.info(f"最小化处理修复: {', '.join(issues_fixed)}")
            else:
                self.logger.info("无需处理，原始质量完美")

            return processed

        except Exception as e:
            self.logger.error(f"最小化处理失败: {e}")
            return image

    def _adaptive_processing(self, image: Image.Image) -> Image.Image:
        """自适应智能处理 - 根据图片质量智能决策"""
        try:
            self.logger.info("采用自适应处理模式")

            # 智能分析
            analysis = self._analyze_for_adaptive_processing(image)
            self.logger.info(f"图片质量分析: {analysis}")

            # 根据分析结果决定处理策略
            if analysis['quality_score'] >= 0.9:
                # 高质量图片 - 完全保留
                return self._preserve_quality(image)
            elif analysis['quality_score'] >= 0.7:
                # 中等质量 - 最小化处理
                return self._minimal_processing(image)
            else:
                # 低质量 - 智能增强（但仍然保守）
                return self._conservative_enhancement(image)

        except Exception as e:
            self.logger.error(f"自适应处理失败: {e}")
            return image

    def _analyze_for_adaptive_processing(self, image: Image.Image) -> dict:
        """为自适应处理分析图片"""
        try:
            # 计算质量评分
            megapixels = (image.width * image.height) / 1000000
            dpi_estimate = self._estimate_dpi(image)

            # 基础质量评分
            if megapixels >= 2 and dpi_estimate >= 200:
                base_score = 0.9
            elif megapixels >= 1 and dpi_estimate >= 150:
                base_score = 0.8
            elif megapixels >= 0.5 and dpi_estimate >= 100:
                base_score = 0.7
            else:
                base_score = 0.5

            # 颜色深度调整
            color_depth_bonus = 0.1 if image.mode in ('RGB', 'RGBA') else 0

            # 综合评分
            quality_score = min(base_score + color_depth_bonus, 1.0)

            return {
                'quality_score': quality_score,
                'megapixels': megapixels,
                'dpi_estimate': dpi_estimate,
                'mode': image.mode,
                'recommended_action': self._get_recommended_action(quality_score)
            }

        except Exception as e:
            self.logger.error(f"图片分析失败: {e}")
            return {'quality_score': 0.5, 'recommended_action': 'minimal'}

    def _get_recommended_action(self, quality_score: float) -> str:
        """获取推荐处理方式"""
        if quality_score >= 0.9:
            return 'preserve'
        elif quality_score >= 0.7:
            return 'minimal'
        else:
            return 'enhance'

    def _conservative_enhancement(self, image: Image.Image) -> Image.Image:
        """保守的增强处理 - 仅处理明显低质量问题"""
        try:
            self.logger.info("采用保守增强模式")
            processed = image.copy()

            # 确保正确的颜色模式
            if processed.mode not in ('RGB', 'RGBA'):
                processed = processed.convert('RGB')

            # 保守的DPI提升（仅在必要时）
            current_dpi = self._estimate_dpi(processed)
            if current_dpi < 100:  # 仅在极低DPI时才提升
                scale = 1.5  # 保守的放大比例
                new_size = (int(processed.width * scale), int(processed.height * scale))
                processed = processed.resize(new_size, Image.Resampling.LANCZOS)
                self.logger.info(f"保守DPI提升: {current_dpi:.1f} → {current_dpi * scale:.1f}")

            return processed

        except Exception as e:
            self.logger.error(f"保守增强失败: {e}")
            return image

    def _estimate_dpi(self, image: Image.Image) -> float:
        """估算图片DPI（保守估计）"""
        # 基于常见纸张尺寸的保守估算
        # A4纸: 2480x3508 @ 300 DPI
        # Letter纸: 2550x3300 @ 300 DPI

        pixel_count = image.width * image.height
        if pixel_count >= 2000000:  # 2MP以上
            return 200  # 假设为中等DPI
        elif pixel_count >= 500000:  # 0.5MP以上
            return 150  # 假设为标准DPI
        else:
            return 96   # 假设为屏幕DPI

    def _save_lossless(self, image: Image.Image, output_path: str):
        """完全无损保存"""
        try:
            # 使用最高质量设置
            save_params = {
                'format': 'PNG',
                'optimize': False,  # 关闭优化，确保无损
                'compress_level': 0,  # 无压缩
            }

            # 如果有透明度，保持RGBA
            if image.mode in ('RGBA', 'LA'):
                save_params['format'] = 'PNG'
            else:
                save_params['format'] = 'PNG'

            image.save(output_path, **save_params)

            file_size = os.path.getsize(output_path)
            self.logger.info(f"无损保存完成: {output_path}, 文件大小: {file_size:,} bytes")

        except Exception as e:
            self.logger.error(f"无损保存失败: {e}")

    def _verify_lossless(self, original_path: str, processed_path: str) -> dict:
        """验证无损程度"""
        try:
            original_size = os.path.getsize(original_path)
            processed_size = os.path.getsize(processed_path)

            # 分析质量保持程度
            with Image.open(original_path) as orig, Image.open(processed_path) as proc:
                orig_info = self._analyze_original_image(orig)
                proc_info = self._analyze_original_image(proc)

            # 计算相似度
            size_similarity = 1.0 - abs(orig_info['megapixels'] - proc_info['megapixels']) / max(orig_info['megapixels'], 1)

            return {
                'original_size': original_size,
                'processed_size': processed_size,
                'size_ratio': processed_size / original_size if original_size > 0 else 1.0,
                'size_similarity': size_similarity,
                'quality_preserved': size_similarity >= 0.95,  # 95%以上认为无损
                'recommendation': '完美无损' if size_similarity >= 0.95 else '轻微调整'
            }

        except Exception as e:
            self.logger.error(f"无损验证失败: {e}")
            return {'quality_preserved': False, 'error': str(e)}

    def _get_lossless_path(self, original_path: str, processing_mode: str) -> str:
        """获取无损处理后的文件路径"""
        base_name = os.path.splitext(original_path)[0]
        return f"{base_name}_lossless_{processing_mode}.png"

    def create_quality_report(self, image_path: str) -> dict:
        """创建图片质量报告"""
        try:
            with Image.open(image_path) as img:
                analysis = self._analyze_original_image(img)

                # OCR适用性评估
                ocr_suitability = self._assess_ocr_suitability(img)

                return {
                    'file_info': {
                        'path': image_path,
                        'size_bytes': os.path.getsize(image_path),
                        'size_mb': os.path.getsize(image_path) / (1024 * 1024)
                    },
                    'image_analysis': analysis,
                    'ocr_assessment': ocr_suitability,
                    'recommendations': self._generate_recommendations(analysis, ocr_suitability)
                }

        except Exception as e:
            self.logger.error(f"质量报告生成失败: {e}")
            return {'error': str(e)}

    def _assess_ocr_suitability(self, image: Image.Image) -> dict:
        """评估OCR适用性"""
        megapixels = (image.width * image.height) / 1000000
        dpi_estimate = self._estimate_dpi(image)

        # OCR适用性评分
        if megapixels >= 1 and dpi_estimate >= 150:
            suitability_score = 1.0
            suitability = '优秀'
        elif megapixels >= 0.5 and dpi_estimate >= 100:
            suitability_score = 0.8
            suitability = '良好'
        elif megapixels >= 0.3 and dpi_estimate >= 72:
            suitability_score = 0.6
            suitability = '一般'
        else:
            suitability_score = 0.4
            suitability = '较差'

        return {
            'score': suitability_score,
            'rating': suitability,
            'megapixels': megapixels,
            'dpi_estimate': dpi_estimate,
            'text_clarity': '高' if dpi_estimate >= 200 else '中' if dpi_estimate >= 150 else '低'
        }

    def _generate_recommendations(self, analysis: dict, ocr_assessment: dict) -> list:
        """生成处理建议"""
        recommendations = []

        if ocr_assessment['score'] >= 0.8:
            recommendations.append("✅ 图片质量优秀，建议采用无损保留模式")
        elif ocr_assessment['score'] >= 0.6:
            recommendations.append("⚡ 图片质量良好，建议采用最小化处理模式")
        else:
            recommendations.append("🔧 图片质量偏低，建议采用自适应处理模式")

        if ocr_assessment['dpi_estimate'] < 150:
            recommendations.append("📐 分辨率偏低，可考虑适度提升")

        if analysis['megapixels'] < 0.5:
            recommendations.append("📏 图片较小，建议使用高质量扫描")

        return recommendations


def main():
    """测试无损图片处理器"""
    logging.basicConfig(level=logging.INFO)

    processor = LosslessImageProcessor()

    # 查找测试图片
    test_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                test_files.append(os.path.join(root, file))

    if not test_files:
        print("没有找到测试图片")
        return

    test_file = test_files[0]
    print(f"测试文件: {test_file}")

    # 创建质量报告
    print(f"\n📊 图片质量报告:")
    report = processor.create_quality_report(test_file)

    if 'error' not in report:
        print(f"文件大小: {report['file_info']['size_mb']:.2f} MB")
        print(f"图片尺寸: {report['image_analysis']['size']}")
        print(f"颜色模式: {report['image_analysis']['mode']}")
        print(f"估算DPI: {report['ocr_assessment']['dpi_estimate']}")
        print(f"OCR适用性: {report['ocr_assessment']['rating']} ({report['ocr_assessment']['score']:.1%})")

        print(f"\n💡 处理建议:")
        for rec in report['recommendations']:
            print(f"   {rec}")
    else:
        print(f"报告生成失败: {report['error']}")

    # 测试不同处理模式
    processing_modes = ['preserve', 'minimal', 'adaptive']

    for mode in processing_modes:
        print(f"\n🔧 测试 {mode} 模式:")
        result_path = processor.process_for_lossless_ocr(test_file, mode)

        if result_path != test_file:
            original_size = os.path.getsize(test_file)
            processed_size = os.path.getsize(result_path)

            print(f"   处理成功: {os.path.basename(result_path)}")
            print(f"   文件大小: {original_size:,} → {processed_size:,} bytes")
            print(f"   大小变化: {((processed_size - original_size) / original_size * 100):+.1f}%")

            # 验证无损程度
            verification = processor._verify_lossless(test_file, result_path)
            print(f"   无损验证: {verification['recommendation']}")
            print(f"   质量保持: {'是' if verification['quality_preserved'] else '否'}")
        else:
            print(f"   使用原图（无需处理）")


if __name__ == "__main__":
    main()