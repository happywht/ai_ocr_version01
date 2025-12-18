#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强图签检测器
结合传统计算机视觉和深度学习的精准图签区域检测
基于Gemini对话中的技术方案实现
"""

import logging
import os
from typing import Tuple, Optional, List, Dict
import cv2
import numpy as np
from PIL import Image
import json

# 复用原有OCR功能，不使用PaddleOCR
PADDLEOCR_AVAILABLE = False


class EnhancedSignatureDetector:
    """增强图签检测器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 复用原有OCR服务
        self.ocr_service_url = "http://127.0.0.1:1224"

        # 图签检测参数
        self.detection_params = {
            'bottom_ratio': 0.4,      # 底部区域比例
            'right_ratio': 0.5,       # 右侧区域比例
            'min_table_width': 200,   # 最小表格宽度
            'min_table_height': 100,  # 最小表格高度
            'hough_threshold': 50,    # 霍夫变换阈值
            'min_line_length': 100,   # 最小线段长度
            'max_line_gap': 10        # 最大线段间隙
        }

    def detect_signature_region_enhanced(self, image_path: str) -> Optional[Tuple[int, int, int, int]]:
        """
        增强的图签区域检测

        Args:
            image_path: 图像路径

        Returns:
            图签区域坐标 (left, top, right, bottom) 或 None
        """
        try:
            self.logger.info(f"开始增强图签检测: {image_path}")

            # 读取图像
            image = cv2.imread(image_path)
            if image is None:
                self.logger.error(f"无法读取图像: {image_path}")
                return None

            height, width = image.shape[:2]

            # 方法1：传统CV检测
            cv_result = self._detect_by_traditional_cv(image, width, height)
            if cv_result:
                self.logger.info("传统CV方法检测成功")
                return cv_result

            # 方法2：传统OCR检测（复用原有OCR服务）
            ocr_result = self._detect_by_original_ocr(image, width, height)
            if ocr_result:
                self.logger.info("原有OCR方法检测成功")
                return ocr_result

            # 方法3：比例定位（兜底方案）
            proportion_result = self._detect_by_proportion(width, height)
            if proportion_result:
                self.logger.info("比例定位方法检测成功")
                return proportion_result

            self.logger.warning("所有检测方法均失败")
            return None

        except Exception as e:
            self.logger.error(f"增强图签检测失败: {e}")
            return None

    def _detect_by_traditional_cv(self, image: np.ndarray, width: int, height: int) -> Optional[Tuple[int, int, int, int]]:
        """基于传统计算机视觉的检测方法"""
        try:
            # 灰度化
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # 定义右下角感兴趣区域
            roi_x = int(width * (1 - self.detection_params['right_ratio']))
            roi_y = int(height * (1 - self.detection_params['bottom_ratio']))
            roi_w = width - roi_x
            roi_h = height - roi_y

            roi = gray[roi_y:height, roi_x:width]

            # 霍夫直线检测
            lines = self._detect_table_lines(roi)

            if len(lines) > 4:  # 表格应该有多条线
                # 基于直线构建矩形
                table_rect = self._build_table_from_lines(lines, roi_x, roi_y)
                if table_rect:
                    return table_rect

            # 如果霍夫变换失败，尝试边缘检测 + 轮廓检测
            return self._detect_by_contours(roi, roi_x, roi_y, width, height)

        except Exception as e:
            self.logger.error(f"传统CV检测失败: {e}")
            return None

    def _detect_table_lines(self, roi: np.ndarray) -> List:
        """检测表格中的直线"""
        try:
            # Canny边缘检测
            edges = cv2.Canny(roi, 50, 150, apertureSize=3)

            # 霍夫直线检测
            lines = cv2.HoughLinesP(
                edges,
                rho=1,
                theta=np.pi/180,
                threshold=self.detection_params['hough_threshold'],
                minLineLength=self.detection_params['min_line_length'],
                maxLineGap=self.detection_params['max_line_gap']
            )

            if lines is None:
                return []

            return [line[0] for line in lines]

        except Exception as e:
            self.logger.error(f"表格直线检测失败: {e}")
            return []

    def _build_table_from_lines(self, lines: List, roi_x: int, roi_y: int) -> Optional[Tuple[int, int, int, int]]:
        """基于检测到的直线构建表格矩形"""
        try:
            if len(lines) < 4:
                return None

            # 分类横线和竖线
            horizontal_lines = []
            vertical_lines = []

            for x1, y1, x2, y2 in lines:
                if abs(x2 - x1) > abs(y2 - y1):  # 横线
                    horizontal_lines.append((x1 + roi_x, y1 + roi_y, x2 + roi_x, y2 + roi_y))
                else:  # 竖线
                    vertical_lines.append((x1 + roi_x, y1 + roi_y, x2 + roi_x, y2 + roi_y))

            if len(horizontal_lines) >= 2 and len(vertical_lines) >= 2:
                # 找到最外围的线条
                h_lines = sorted(horizontal_lines, key=lambda line: min(line[1], line[3]))
                v_lines = sorted(vertical_lines, key=lambda line: min(line[0], line[2]))

                # 构建矩形
                top = min(h_lines[0][1], h_lines[0][3])
                bottom = max(h_lines[-1][1], h_lines[-1][3])
                left = min(v_lines[0][0], v_lines[0][2])
                right = max(v_lines[-1][0], v_lines[-1][2])

                return (left, top, right, bottom)

            return None

        except Exception as e:
            self.logger.error(f"从直线构建表格失败: {e}")
            return None

    def _detect_by_contours(self, roi: np.ndarray, roi_x: int, roi_y: int,
                           width: int, height: int) -> Optional[Tuple[int, int, int, int]]:
        """基于轮廓的检测方法"""
        try:
            # 二值化
            _, binary = cv2.threshold(roi, 127, 255, cv2.THRESH_BINARY_INV)

            # 形态学操作
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

            # 查找轮廓
            contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # 筛选表格候选区域
            table_candidates = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)

                # 转换为全局坐标
                global_x = x + roi_x
                global_y = y + roi_y

                # 表格特征验证
                if self._is_table_candidate(global_x, global_y, w, h, width, height):
                    confidence = self._calculate_table_confidence(
                        global_x, global_y, w, h, width, height
                    )
                    table_candidates.append((global_x, global_y, w, h, confidence))

            if table_candidates:
                # 选择置信度最高的候选区域
                best = max(table_candidates, key=lambda x: x[4])
                return (best[0], best[1], best[0] + best[2], best[1] + best[3])

            return None

        except Exception as e:
            self.logger.error(f"轮廓检测失败: {e}")
            return None

    def _is_table_candidate(self, x: int, y: int, w: int, h: int,
                           image_width: int, image_height: int) -> bool:
        """判断是否为表格候选区域"""
        # 位置检查：应该在右下角
        is_bottom = y > image_height * 0.7
        is_right = x > image_width * 0.6

        # 尺寸检查
        min_w = self.detection_params['min_table_width']
        min_h = self.detection_params['min_table_height']
        size_ok = w >= min_w and h >= min_h

        # 宽高比检查
        aspect_ratio = w / h if h > 0 else 0
        aspect_ok = 1.5 <= aspect_ratio <= 5

        return is_bottom and is_right and size_ok and aspect_ok

    def _calculate_table_confidence(self, x: int, y: int, w: int, h: int,
                                   image_width: int, image_height: int) -> float:
        """计算表格候选区域的置信度"""
        try:
            confidence = 0.0

            # 位置权重
            if x > image_width * 0.8:
                confidence += 0.3
            elif x > image_width * 0.7:
                confidence += 0.2

            if y > image_height * 0.9:
                confidence += 0.3
            elif y > image_height * 0.8:
                confidence += 0.2

            # 尺寸权重
            ideal_w = image_width * 0.3
            ideal_h = image_height * 0.2

            w_ratio = min(w / ideal_w, ideal_w / w)
            h_ratio = min(h / ideal_h, ideal_h / h)

            confidence += (w_ratio + h_ratio) * 0.1

            return min(confidence, 1.0)

        except:
            return 0.0

    def _detect_by_original_ocr(self, image: np.ndarray, width: int, height: int) -> Optional[Tuple[int, int, int, int]]:
        """基于原有OCR服务的检测方法"""
        try:
            # 导入原有OCR工具
            from invoice_ocr_tool import InvoiceOCRTool

            # 只检测右下角区域
            roi_x = int(width * (1 - self.detection_params['right_ratio']))
            roi_y = int(height * (1 - self.detection_params['bottom_ratio']))
            roi = image[roi_y:height, roi_x:width]

            # 保存ROI为临时文件
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                from PIL import Image
                roi_pil = Image.fromarray(roi)
                roi_pil.save(tmp.name)
                tmp_path = tmp.name

            try:
                # 使用原有OCR服务
                ocr_tool = InvoiceOCRTool(self.ocr_service_url)
                result = ocr_tool.process_invoice(tmp_path)

                if result and result.get('OCR原始结果'):
                    # 基于OCR结果估算文本区域
                    ocr_text = result['OCR原始结果']

                    # 简单启发式：如果OCR识别到足够多的文本，认为这是一个有效区域
                    if len(ocr_text.strip()) > 10:  # 至少10个字符
                        # 返回ROI的全局坐标
                        return (roi_x, roi_y, width, height)

                return None

            finally:
                # 清理临时文件
                try:
                    os.unlink(tmp_path)
                except:
                    pass

        except Exception as e:
            self.logger.error(f"原有OCR检测失败: {e}")
            return None

    def _detect_by_proportion(self, width: int, height: int) -> Optional[Tuple[int, int, int, int]]:
        """基于比例的检测方法（兜底方案）"""
        try:
            # 基于Gemini建议的比例：右侧25%和下方20%
            right_ratio = 0.25
            bottom_ratio = 0.2

            left = int(width * (1 - right_ratio))
            top = int(height * (1 - bottom_ratio))
            right = width
            bottom = height

            return (left, top, right, bottom)

        except Exception as e:
            self.logger.error(f"比例检测失败: {e}")
            return None

    def extract_table_structure(self, image: np.ndarray, table_region: Tuple[int, int, int, int]) -> List[Dict]:
        """
        提取表格结构信息

        Args:
            image: 原始图像
            table_region: 表格区域坐标

        Returns:
            表格单元格列表
        """
        try:
            left, top, right, bottom = table_region
            table_img = image[top:bottom, left:right]

            # 使用原有OCR服务提取表格结构
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                from PIL import Image
                table_pil = Image.fromarray(table_img)
                table_pil.save(tmp.name)
                tmp_path = tmp.name

            try:
                # 使用原有OCR服务
                from invoice_ocr_tool import InvoiceOCRTool
                ocr_tool = InvoiceOCRTool(self.ocr_service_url)
                result = ocr_tool.process_invoice(tmp_path)

                cells = []
                if result and result.get('OCR原始结果'):
                    ocr_text = result['OCR原始结果']

                    # 简化处理：将OCR文本按行分割，模拟表格单元格
                    lines = ocr_text.split('\n')
                    for line_idx, line in enumerate(lines):
                        line = line.strip()
                        if line:
                            # 估算单元格位置（简化处理）
                            cell_height = (bottom - top) // max(len(lines), 1)
                            cell_y = top + line_idx * cell_height

                            # 创建模拟的单元格信息
                            cells.append({
                                'line_index': line_idx,
                                'box': [(left, cell_y), (right, cell_y), (right, cell_y + cell_height), (left, cell_y + cell_height)],
                                'text': line,
                                'confidence': 0.8,  # 默认置信度
                                'center_x': (left + right) / 2,
                                'center_y': cell_y + cell_height / 2
                            })

                return cells

            finally:
                # 清理临时文件
                try:
                    os.unlink(tmp_path)
                except:
                    pass

        except Exception as e:
            self.logger.error(f"表格结构提取失败: {e}")
            return []

    def save_detection_debug(self, image_path: str, detection_result: Tuple[int, int, int, int]):
        """保存检测结果调试图片"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return

            left, top, right, bottom = detection_result

            # 绘制检测框
            cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0), 3)

            # 添加标签
            cv2.putText(image, 'Signature Region', (left, top-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # 保存调试图片
            debug_path = image_path.replace('.', '_signature_detection.')
            cv2.imwrite(debug_path, image)
            self.logger.info(f"检测结果已保存: {debug_path}")

        except Exception as e:
            self.logger.error(f"保存调试图片失败: {e}")


def main():
    """测试增强图签检测器"""
    logging.basicConfig(level=logging.INFO)

    detector = EnhancedSignatureDetector()

    # 测试图片
    test_images = [
        "examples/test_invoice.png",
        # 可以添加更多测试图片
    ]

    for image_path in test_images:
        if os.path.exists(image_path):
            print(f"\n检测图签区域: {image_path}")
            result = detector.detect_signature_region_enhanced(image_path)

            if result:
                left, top, right, bottom = result
                width = right - left
                height = bottom - top
                print(f"检测结果: ({left}, {top}, {right}, {bottom})")
                print(f"区域尺寸: {width} x {height}")

                # 保存调试图片
                detector.save_detection_debug(image_path, result)
            else:
                print("未检测到图签区域")


if __name__ == "__main__":
    main()