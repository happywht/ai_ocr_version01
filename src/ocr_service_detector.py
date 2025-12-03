#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR服务路径智能检测器
自动检测系统中的umi-OCR服务路径
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Optional, Tuple

class OCRServiceDetector:
    """OCR服务路径检测器"""

    def __init__(self):
        self.common_paths = [
            # Windows常见路径
            r"C:\Program Files\umi-ocr",
            r"C:\Program Files (x86)\umi-ocr",
            r"D:\software\umi-ocr",
            r"D:\software\个性化工具\umi-ocr",
            r"D:\tools\umi-ocr",
            r"E:\software\umi-ocr",
            r"F:\software\umi-ocr",

            # 用户目录
            os.path.expanduser("~/umi-ocr"),
            os.path.expanduser("~/Desktop/umi-ocr"),
            os.path.expanduser("~/Downloads/umi-ocr"),
            os.path.expanduser("~/AppData/Local/umi-ocr"),

            # 当前项目目录
            os.path.join(os.getcwd(), "umi-ocr"),
            os.path.join(os.getcwd(), "..", "umi-ocr"),
            os.path.join(os.path.dirname(__file__), "..", "umi-ocr"),
        ]

        # 配置文件路径
        self.config_file = os.path.join(os.path.dirname(__file__), "..", "config", "ocr_paths.json")
        self.saved_paths = self.load_saved_paths()

        # 缓存检测结果，避免重复搜索
        self._cached_services = None
        self._cache_timestamp = 0
        self._cache_ttl = 30  # 缓存30秒

    def load_saved_paths(self) -> List[str]:
        """加载保存的路径"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('ocr_paths', [])
        except Exception:
            pass
        return []

    def save_path(self, path: str):
        """保存有效的OCR路径"""
        if path not in self.saved_paths:
            self.saved_paths.insert(0, path)  # 插入到最前面
            # 只保留最近10个路径
            self.saved_paths = self.saved_paths[:10]

            try:
                os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump({'ocr_paths': self.saved_paths}, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

    def find_ocr_services(self, quick_mode: bool = True) -> List[Tuple[str, str]]:
        """查找所有可用的OCR服务

        Args:
            quick_mode: 快速模式，只检查保存的路径和常见路径，不进行系统搜索

        Returns:
            List[Tuple[str, str]]: (路径, 类型) 的列表，类型为 "可执行文件" 或 "Python脚本"
        """
        import time

        # 检查缓存
        current_time = time.time()
        if (self._cached_services is not None and
            current_time - self._cache_timestamp < self._cache_ttl):
            return self._cached_services

        found_services = []

        # 合并搜索路径：保存的路径 + 常见路径
        all_paths = self.saved_paths + self.common_paths

        # 首先检查保存的路径
        for path in self.saved_paths:
            service_info = self._check_path(path)
            if service_info:
                found_services.append(service_info)

        # 然后检查常见路径
        for path in self.common_paths:
            # 避免重复
            if any(service[0] == path for service in found_services):
                continue

            service_info = self._check_path(path)
            if service_info:
                found_services.append(service_info)

        # 只在非快速模式下进行系统搜索
        if not quick_mode:
            system_found = self._search_system()
            for path, service_type in system_found:
                # 避免重复
                if any(service[0] == path for service in found_services):
                    continue
                found_services.append((path, service_type))

        # 更新缓存
        self._cached_services = found_services
        self._cache_timestamp = current_time

        return found_services

    def _check_path(self, path: str) -> Optional[Tuple[str, str]]:
        """检查指定路径是否包含OCR服务"""
        if not os.path.exists(path):
            return None

        # 查找可执行文件
        exe_file = os.path.join(path, "Umi-OCR.exe")
        main_script = os.path.join(path, "main.py")

        if os.path.exists(exe_file):
            return (path, "可执行文件")
        elif os.path.exists(main_script):
            return (path, "Python脚本")

        # 检查是否有umi-ocr相关的子目录
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    # 检查子目录中是否有可执行文件
                    sub_exe = os.path.join(item_path, "Umi-OCR.exe")
                    sub_main = os.path.join(item_path, "main.py")

                    if os.path.exists(sub_exe) or os.path.exists(sub_main):
                        return (item_path, "可执行文件" if os.path.exists(sub_exe) else "Python脚本")
        except Exception:
            pass

        return None

    def _search_system(self) -> List[Tuple[str, str]]:
        """在系统中搜索umi-ocr相关目录"""
        found_services = []

        try:
            # 搜索C盘根目录
            for drive in ['C:', 'D:', 'E:', 'F:']:
                if os.path.exists(drive):
                    try:
                        for root, dirs, files in os.walk(drive + '\\'):
                            # 限制搜索深度，避免搜索太深
                            if root.count('\\') > 5:
                                continue

                            # 检查目录名是否包含umi-ocr
                            for dirname in dirs:
                                if 'umi-ocr' in dirname.lower():
                                    dir_path = os.path.join(root, dirname)
                                    service_info = self._check_path(dir_path)
                                    if service_info:
                                        found_services.append(service_info)
                                        # 如果找到服务，停止搜索这个目录的子目录
                                        dirs.remove(dirname)
                                        break

                            # 检查是否有Umi-OCR.exe文件
                            for filename in files:
                                if filename.lower() == 'umi-ocr.exe':
                                    found_services.append((root, "可执行文件"))
                                    break

                            # 限制搜索结果数量
                            if len(found_services) >= 5:
                                break
                    except Exception:
                        continue

                    if len(found_services) >= 5:
                        break
        except Exception:
            pass

        return found_services

    def get_best_service(self, quick_mode: bool = True) -> Optional[Tuple[str, str]]:
        """获取最佳OCR服务（优先返回保存的路径）"""
        services = self.find_ocr_services(quick_mode=quick_mode)
        return services[0] if services else None

    def get_best_service_fast(self) -> Optional[Tuple[str, str]]:
        """快速获取最佳OCR服务，只检查保存的路径"""
        # 首先检查缓存
        import time
        current_time = time.time()
        if (self._cached_services is not None and
            current_time - self._cache_timestamp < self._cache_ttl):
            return self._cached_services[0] if self._cached_services else None

        # 只检查保存的路径
        for path in self.saved_paths:
            service_info = self._check_path(path)
            if service_info:
                # 更新缓存
                self._cached_services = [service_info]
                self._cache_timestamp = current_time
                return service_info

        # 如果保存的路径都无效，清除缓存并返回None
        self._cached_services = None
        return None

    def invalidate_cache(self):
        """清除缓存，强制重新搜索"""
        self._cached_services = None
        self._cache_timestamp = 0

    def manual_add_path(self, path: str) -> bool:
        """手动添加路径"""
        if os.path.exists(path):
            service_info = self._check_path(path)
            if service_info:
                self.save_path(path)
                return True
        return False

    def is_ocr_service_running(self, port: int = 1224) -> bool:
        """检查OCR服务是否正在运行"""
        try:
            import requests
            response = requests.get(f"http://127.0.0.1:{port}", timeout=3)
            return response.status_code == 200
        except Exception:
            return False

    def is_process_running(self, exe_path: str) -> bool:
        """检查指定路径的OCR服务进程是否正在运行"""
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    if proc.info['exe'] and proc.info['exe'].lower() == exe_path.lower():
                        return True
                    if proc.info['name'] and 'umi-ocr' in proc.info['name'].lower():
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except ImportError:
            # 如果没有psutil，使用简单检查
            return self.is_ocr_service_running()
        except Exception:
            return False

# 全局检测器实例
ocr_detector = OCRServiceDetector()

def detect_ocr_service() -> Optional[str]:
    """便捷函数：检测并返回最佳OCR服务路径"""
    service = ocr_detector.get_best_service()
    return service[0] if service else None

if __name__ == "__main__":
    """测试OCR服务检测功能"""
    print("🔍 OCR服务路径检测测试")
    print("=" * 50)

    detector = OCRServiceDetector()

    # 查找所有服务
    services = detector.find_ocr_services()

    if services:
        print(f"✅ 找到 {len(services)} 个OCR服务:")
        for i, (path, service_type) in enumerate(services, 1):
            print(f"  {i}. {path} ({service_type})")

        # 获取最佳服务
        best = detector.get_best_service()
        if best:
            print(f"\n🎯 推荐使用: {best[0]} ({best[1]})")
    else:
        print("❌ 未找到OCR服务")
        print("\n💡 建议:")
        print("1. 确认已安装umi-OCR")
        print("2. 尝试手动指定路径")
        print("3. 将umi-OCR安装到常见目录")