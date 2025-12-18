#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动修复后的OCR GUI
"""

import sys
import os
import logging

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """启动修复后的GUI"""
    print("🚀 启动修复后的OCR识别工具...")

    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('ocr_tool_fixed.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    try:
        # 导入修复后的GUI
        from ocr_gui import UniversalOCRGUI

        print("✅ GUI模块加载成功")
        print("🔧 修复内容：")
        print("   - Logger初始化问题已修复")
        print("   - PDF渲染参数错误已修复")
        print("   - None结果处理已优化")
        print("   - 缺失方法已补充")
        print("   - 文件路径验证已增强")
        print("   - 错误处理机制已完善")
        print()
        print("🎯 正在启动GUI界面...")

        # 创建并运行GUI
        app = UniversalOCRGUI()
        app.run()

    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保所有依赖模块已正确安装")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("请查看错误日志获取详细信息")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()