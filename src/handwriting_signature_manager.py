#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手写签名特征管理器
实现手写体与印刷体姓名的自动建库和匹配功能
基于Gemini对话中的技术方案实现
"""

import logging
import os
import json
import sqlite3
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from PIL import Image
import numpy as np
import cv2

try:
    import torch
    import torch.nn as nn
    import torchvision.transforms as transforms
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    transforms = None
    logging.warning("PyTorch未安装，将使用传统特征提取方法")

try:
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.decomposition import PCA
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn未安装，将使用基础相似度计算")


class SignatureFeatureExtractor:
    """签名特征提取器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 如果PyTorch可用，初始化深度学习模型
        if TORCH_AVAILABLE and transforms is not None:
            self.model = self._init_feature_model()
            # 图像预处理
            self.transform = transforms.Compose([
                transforms.Resize((128, 128)),
                transforms.Grayscale(num_output_channels=1),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.5], std=[0.5])
            ])
        else:
            self.model = None
            self.transform = None

    def _init_feature_model(self):
        """初始化特征提取模型"""
        try:
            # 简化的CNN特征提取器
            class SignatureCNN(nn.Module):
                def __init__(self):
                    super().__init__()
                    self.conv1 = nn.Conv2d(1, 32, 3, padding=1)
                    self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
                    self.conv3 = nn.Conv2d(64, 128, 3, padding=1)
                    self.pool = nn.MaxPool2d(2, 2)
                    self.fc = nn.Linear(128 * 16 * 16, 256)

                def forward(self, x):
                    x = self.pool(torch.relu(self.conv1(x)))
                    x = self.pool(torch.relu(self.conv2(x)))
                    x = self.pool(torch.relu(self.conv3(x)))
                    x = x.view(-1, 128 * 16 * 16)
                    x = self.fc(x)
                    return x

            model = SignatureCNN()
            # 这里应该加载预训练权重，暂时使用随机权重
            model.eval()
            return model

        except Exception as e:
            self.logger.error(f"初始化深度学习模型失败: {e}")
            return None

    def extract_features(self, signature_image: np.ndarray) -> Optional[np.ndarray]:
        """
        提取签名特征向量

        Args:
            signature_image: 签名图像数组

        Returns:
            特征向量
        """
        try:
            # 预处理图像
            processed_image = self._preprocess_signature(signature_image)

            if self.model and TORCH_AVAILABLE:
                # 使用深度学习模型提取特征
                return self._extract_deep_features(processed_image)
            else:
                # 使用传统方法提取特征
                return self._extract_traditional_features(processed_image)

        except Exception as e:
            self.logger.error(f"特征提取失败: {e}")
            return None

    def _preprocess_signature(self, image: np.ndarray) -> np.ndarray:
        """预处理签名图像"""
        try:
            # 确保图像是灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image.copy()

            # 二值化
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # 去除噪点
            kernel = np.ones((2, 2), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

            # 居中处理
            return self._center_signature(cleaned)

        except Exception as e:
            self.logger.error(f"图像预处理失败: {e}")
            return image

    def _center_signature(self, image: np.ndarray) -> np.ndarray:
        """将签名居中"""
        try:
            # 找到签名的边界框
            coords = np.column_stack(np.where(image > 0))
            if len(coords) == 0:
                return image

            y_min, x_min = coords.min(axis=0)
            y_max, x_max = coords.max(axis=0)

            # 裁剪签名区域
            signature = image[y_min:y_max+1, x_min:x_max+1]

            # 创建128x128的白色背景
            centered = np.ones((128, 128), dtype=np.uint8) * 255

            # 计算居中位置
            sig_h, sig_w = signature.shape
            start_y = (128 - sig_h) // 2
            start_x = (128 - sig_w) // 2

            # 将签名放置在中心
            centered[start_y:start_y+sig_h, start_x:start_x+sig_w] = signature

            return centered

        except Exception as e:
            self.logger.error(f"签名居中失败: {e}")
            return np.ones((128, 128), dtype=np.uint8) * 255

    def _extract_deep_features(self, image: np.ndarray) -> Optional[np.ndarray]:
        """使用深度学习提取特征"""
        try:
            if not self.transform:
                return None

            # 转换为PIL图像
            pil_image = Image.fromarray(image)

            # 预处理
            tensor = self.transform(pil_image).unsqueeze(0)

            # 特征提取
            with torch.no_grad():
                features = self.model(tensor)

            # 转换为numpy数组
            return features.squeeze().numpy()

        except Exception as e:
            self.logger.error(f"深度特征提取失败: {e}")
            return None

    def _extract_traditional_features(self, image: np.ndarray) -> Optional[np.ndarray]:
        """使用传统方法提取特征"""
        try:
            features = []

            # 1. HOG特征（方向梯度直方图）
            hog_features = self._compute_hog_features(image)
            features.extend(hog_features)

            # 2. LBP特征（局部二值模式）
            lbp_features = self._compute_lbp_features(image)
            features.extend(lbp_features)

            # 3. 统计特征
            stats_features = self._compute_statistical_features(image)
            features.extend(stats_features)

            return np.array(features)

        except Exception as e:
            self.logger.error(f"传统特征提取失败: {e}")
            return None

    def _compute_hog_features(self, image: np.ndarray, cell_size: int = 8) -> List[float]:
        """计算HOG特征"""
        try:
            # 简化的HOG实现
            h, w = image.shape
            features = []

            for y in range(0, h - cell_size, cell_size):
                for x in range(0, w - cell_size, cell_size):
                    cell = image[y:y+cell_size, x:x+cell_size]

                    # 计算梯度
                    grad_x = cv2.Sobel(cell, cv2.CV_64F, 1, 0, ksize=3)
                    grad_y = cv2.Sobel(cell, cv2.CV_64F, 0, 1, ksize=3)

                    # 计算梯度幅值和方向
                    magnitude = np.sqrt(grad_x**2 + grad_y**2)
                    direction = np.arctan2(grad_y, grad_x)

                    # 直方图
                    hist, _ = np.histogram(direction, bins=8, range=(-np.pi, np.pi), weights=magnitude)
                    features.extend(hist.tolist())

            return features

        except Exception as e:
            self.logger.error(f"HOG特征计算失败: {e}")
            return [0.0] * 128  # 返回零向量

    def _compute_lbp_features(self, image: np.ndarray) -> List[float]:
        """计算LBP特征"""
        try:
            # 简化的LBP实现
            h, w = image.shape
            lbp = np.zeros((h, w), dtype=np.uint8)

            for i in range(1, h-1):
                for j in range(1, w-1):
                    center = image[i, j]
                    code = 0

                    # 8邻域
                    neighbors = [
                        image[i-1, j-1], image[i-1, j], image[i-1, j+1],
                        image[i, j+1], image[i+1, j+1], image[i+1, j],
                        image[i+1, j-1], image[i, j-1]
                    ]

                    for k, neighbor in enumerate(neighbors):
                        if neighbor >= center:
                            code |= (1 << k)

                    lbp[i, j] = code

            # 计算LBP直方图
            hist, _ = np.histogram(lbp, bins=256, range=(0, 256))
            return (hist / hist.sum()).tolist()

        except Exception as e:
            self.logger.error(f"LBP特征计算失败: {e}")
            return [0.0] * 256

    def _compute_statistical_features(self, image: np.ndarray) -> List[float]:
        """计算统计特征"""
        try:
            # 基本统计量
            mean_val = np.mean(image)
            std_val = np.std(image)
            min_val = np.min(image)
            max_val = np.max(image)

            # 密度特征
            foreground_ratio = np.sum(image < 128) / image.size

            # 形状特征
            coords = np.column_stack(np.where(image < 128))
            if len(coords) > 0:
                y_min, x_min = coords.min(axis=0)
                y_max, x_max = coords.max(axis=0)
                aspect_ratio = (x_max - x_min) / (y_max - y_min + 1e-6)
            else:
                aspect_ratio = 1.0

            return [
                mean_val, std_val, min_val, max_val,
                foreground_ratio, aspect_ratio
            ]

        except Exception as e:
            self.logger.error(f"统计特征计算失败: {e}")
            return [0.0] * 6


class HandwritingSignatureManager:
    """手写签名数据库管理器"""

    def __init__(self, db_path: str = "signature_database.db"):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self.feature_extractor = SignatureFeatureExtractor()

        # 初始化数据库
        self._init_database()

    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 创建签名数据库表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS signatures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE,
                    printed_name TEXT NOT NULL,
                    signature_features BLOB,
                    signature_image_path TEXT,
                    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sample_count INTEGER DEFAULT 1
                )
            ''')

            # 创建签名样本表（存储多个样本）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS signature_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    sample_index INTEGER NOT NULL,
                    signature_features BLOB,
                    signature_image_path TEXT,
                    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES signatures (user_id)
                )
            ''')

            conn.commit()
            conn.close()

            self.logger.info("签名数据库初始化成功")

        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")

    def add_signature(self, printed_name: str, signature_image: np.ndarray,
                     user_id: Optional[str] = None) -> bool:
        """
        添加签名到数据库

        Args:
            printed_name: 印刷体姓名
            signature_image: 手写签名图像
            user_id: 用户ID（可选）

        Returns:
            是否添加成功
        """
        try:
            # 提取特征
            features = self.feature_extractor.extract_features(signature_image)
            if features is None:
                return False

            # 生成用户ID
            if not user_id:
                user_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 检查用户是否已存在
            cursor.execute("SELECT user_id, sample_count FROM signatures WHERE user_id = ? OR printed_name = ?",
                          (user_id, printed_name))
            existing = cursor.fetchone()

            if existing:
                # 用户已存在，更新样本
                existing_user_id, sample_count = existing
                user_id = existing_user_id
                new_sample_count = sample_count + 1

                # 更新主记录
                cursor.execute('''
                    UPDATE signatures
                    SET sample_count = ?, updated_time = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (new_sample_count, user_id))

                # 添加新样本
                cursor.execute('''
                    INSERT INTO signature_samples
                    (user_id, sample_index, signature_features)
                    VALUES (?, ?, ?)
                ''', (user_id, new_sample_count, features.tobytes()))

            else:
                # 新用户
                cursor.execute('''
                    INSERT INTO signatures
                    (user_id, printed_name, signature_features)
                    VALUES (?, ?, ?)
                ''', (user_id, printed_name, features.tobytes()))

                # 添加第一个样本
                cursor.execute('''
                    INSERT INTO signature_samples
                    (user_id, sample_index, signature_features)
                    VALUES (?, ?, ?)
                ''', (user_id, 1, features.tobytes()))

            conn.commit()
            conn.close()

            self.logger.info(f"签名添加成功: {printed_name} ({user_id})")
            return True

        except Exception as e:
            self.logger.error(f"添加签名失败: {e}")
            return False

    def match_signature(self, signature_image: np.ndarray, threshold: float = 0.7) -> List[Dict]:
        """
        匹配签名

        Args:
            signature_image: 待匹配的签名图像
            threshold: 相似度阈值

        Returns:
            匹配结果列表
        """
        try:
            # 提取查询签名的特征
            query_features = self.feature_extractor.extract_features(signature_image)
            if query_features is None:
                return []

            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 获取所有签名样本
            cursor.execute('''
                SELECT s.user_id, s.printed_name, s.sample_count,
                       ss.signature_features, ss.sample_index
                FROM signatures s
                JOIN signature_samples ss ON s.user_id = ss.user_id
                ORDER BY s.user_id, ss.sample_index
            ''')

            results = []
            user_matches = {}

            for row in cursor.fetchall():
                user_id, printed_name, sample_count, stored_features_blob, sample_index = row

                # 解码存储的特征
                if stored_features_blob:
                    stored_features = np.frombuffer(stored_features_blob, dtype=np.float64)

                    # 计算相似度
                    if SKLEARN_AVAILABLE:
                        similarity = cosine_similarity([query_features], [stored_features])[0][0]
                    else:
                        similarity = self._compute_cosine_similarity(query_features, stored_features)

                    # 记录匹配结果
                    if user_id not in user_matches:
                        user_matches[user_id] = {
                            'user_id': user_id,
                            'printed_name': printed_name,
                            'sample_count': sample_count,
                            'similarities': [],
                            'max_similarity': 0.0
                        }

                    user_matches[user_id]['similarities'].append({
                        'sample_index': sample_index,
                        'similarity': similarity
                    })

                    if similarity > user_matches[user_id]['max_similarity']:
                        user_matches[user_id]['max_similarity'] = similarity

            conn.close()

            # 过滤和排序结果
            for user_id, match_data in user_matches.items():
                if match_data['max_similarity'] >= threshold:
                    results.append(match_data)

            # 按相似度排序
            results.sort(key=lambda x: x['max_similarity'], reverse=True)

            return results

        except Exception as e:
            self.logger.error(f"签名匹配失败: {e}")
            return []

    def _compute_cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        try:
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return dot_product / (norm1 * norm2)

        except:
            return 0.0

    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """获取用户信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT user_id, printed_name, sample_count, created_time, updated_time
                FROM signatures
                WHERE user_id = ?
            ''', (user_id,))

            result = cursor.fetchone()
            conn.close()

            if result:
                return {
                    'user_id': result[0],
                    'printed_name': result[1],
                    'sample_count': result[2],
                    'created_time': result[3],
                    'updated_time': result[4]
                }

            return None

        except Exception as e:
            self.logger.error(f"获取用户信息失败: {e}")
            return None

    def list_all_users(self) -> List[Dict]:
        """列出所有用户"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT user_id, printed_name, sample_count, created_time, updated_time
                FROM signatures
                ORDER BY created_time DESC
            ''')

            results = []
            for row in cursor.fetchall():
                results.append({
                    'user_id': row[0],
                    'printed_name': row[1],
                    'sample_count': row[2],
                    'created_time': row[3],
                    'updated_time': row[4]
                })

            conn.close()
            return results

        except Exception as e:
            self.logger.error(f"获取用户列表失败: {e}")
            return []

    def export_database(self, export_path: str) -> bool:
        """导出数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 导出签名数据
            cursor.execute('''
                SELECT user_id, printed_name, signature_features, created_time
                FROM signatures
            ''')

            export_data = []
            for row in cursor.fetchall():
                user_id, printed_name, features_blob, created_time = row

                export_data.append({
                    'user_id': user_id,
                    'printed_name': printed_name,
                    'created_time': created_time,
                    'features_hex': features_blob.hex() if features_blob else None
                })

            conn.close()

            # 保存到文件
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"数据库导出成功: {export_path}")
            return True

        except Exception as e:
            self.logger.error(f"数据库导出失败: {e}")
            return False


def main():
    """测试手写签名管理器"""
    logging.basicConfig(level=logging.INFO)

    # 创建测试签名图像
    test_signature = np.random.randint(0, 255, (100, 200), dtype=np.uint8)

    # 初始化管理器
    manager = HandwritingSignatureManager()

    # 测试添加签名
    print("测试添加签名...")
    success = manager.add_signature("张三", test_signature, "test_user_001")
    print(f"添加结果: {success}")

    # 测试匹配
    print("\n测试签名匹配...")
    matches = manager.match_signature(test_signature, threshold=0.5)
    print(f"匹配结果: {len(matches)}个匹配")
    for match in matches:
        print(f"  {match['printed_name']}: {match['max_similarity']:.3f}")

    # 测试用户列表
    print("\n用户列表:")
    users = manager.list_all_users()
    for user in users:
        print(f"  {user['printed_name']} ({user['sample_count']}个样本)")


if __name__ == "__main__":
    main()