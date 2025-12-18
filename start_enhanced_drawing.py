#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强图签识别工具启动脚本
专门用于测试和演示新实现的图签识别功能
"""

import sys
import os


def print_banner():
    """打印程序标题"""
    print("=" * 60)
    print("      增强图签识别工具 - 基于Gemini对话技术方案")
    print("=" * 60)
    print("🎯 功能特性:")
    print("   • 精准右下角图签区域检测")
    print("   • 霍夫直线检测 + 传统OCR服务")
    print("   • 手写签名特征提取和匹配")
    print("   • 自动建库和相似度计算")
    print("   • 表格结构智能分析")
    print("   • 复用现有OCR服务，无需额外依赖")
    print("=" * 60)


def check_dependencies():
    """检查新增功能的依赖"""
    print("🔍 检查依赖库...")

    # 基础依赖检查         'pillow': '图像处理库',
    basic_deps = {
        'requests': 'HTTP请求库',
        'pypdfium2': 'PDF处理库',
        'anthropic': '智谱AI库',
        'openpyxl': 'Excel导出库'
    }

    # 新增功能依赖检查
    enhanced_deps = {
        'cv2': 'OpenCV计算机视觉库',
        'numpy': 'NumPy数值计算库',
    }

    # 可选深度学习依赖
    optional_deps = {
        'torch': 'PyTorch深度学习框架',
        'sklearn': 'scikit-learn机器学习库'
    }

    missing_basic = []
    missing_enhanced = []
    missing_optional = []

    # 检查基础依赖
    for dep, desc in basic_deps.items():
        try:
            __import__(dep)
            print(f"   ✅ {desc} ({dep})")
        except ImportError:
            missing_basic.append(dep)
            print(f"   ❌ {desc} ({dep}) - 缺失")

    # 检查增强功能依赖
    for dep, desc in enhanced_deps.items():
        try:
            __import__(dep)
            print(f"   ✅ {desc} ({dep})")
        except ImportError:
            missing_enhanced.append(dep)
            print(f"   ❌ {desc} ({dep}) - 缺失")

    # 检查可选依赖
    for dep, desc in optional_deps.items():
        try:
            __import__(dep)
            print(f"   ✅ {desc} ({dep}) - 可选")
        except ImportError:
            missing_optional.append(dep)
            print(f"   ⚠️  {desc} ({dep}) - 可选，建议安装")

    if missing_basic:
        print(f"\n❌ 缺少必需依赖: {', '.join(missing_basic)}")
        print("请运行: pip install -r docs/requirements.txt")
        return False

    if missing_enhanced:
        print(f"\n❌ 缺少增强功能依赖: {', '.join(missing_enhanced)}")
        print("请运行: pip install opencv-python numpy")
        return False

    if missing_optional:
        print(f"\n⚠️  建议安装可选依赖以获得最佳体验:")
        print("   pip install torch torchvision scikit-learn")

    print("\n✅ 依赖检查完成！")
    return True


def show_menu():
    """显示功能菜单"""
    print("\n🎮 请选择功能:")
    print("1. 测试增强图签检测")
    print("2. 演示手写签名数据库")
    print("3. 运行完整增强识别流程")
    print("4. 启动原有GUI界面")
    print("5. 查看技术实现报告")
    print("6. 安装可选依赖")
    print("7. 退出")
    print("-" * 40)


def test_enhanced_signature_detection():
    """测试增强图签检测"""
    print("\n🔍 测试增强图签检测...")
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        from enhanced_signature_detector import EnhancedSignatureDetector

        detector = EnhancedSignatureDetector()

        # 查找测试图片
        test_images = []
        for pattern in ["examples/test_invoice*.png", "examples/test_invoice*.jpg"]:
            import glob
            test_images.extend(glob.glob(pattern))

        if test_images:
            for image_path in test_images[:2]:  # 最多测试2张图片
                print(f"\n📷 处理图片: {image_path}")
                result = detector.detect_signature_region_enhanced(image_path)

                if result:
                    left, top, right, bottom = result
                    width = right - left
                    height = bottom - top
                    print(f"   ✅ 检测成功: 坐标({left},{top},{right},{bottom}) 尺寸({width}x{height})")
                    detector.save_detection_debug(image_path, result)
                    print(f"   📸 调试图片已保存")
                else:
                    print("   ❌ 未检测到图签区域")
        else:
            print("⚠️  未找到测试图片，请将测试图片放在 examples/ 目录下")

    except Exception as e:
        print(f"❌ 测试失败: {e}")


def demo_signature_database():
    """演示签名数据库"""
    print("\n🗄️ 演示手写签名数据库...")
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        from handwriting_signature_manager import HandwritingSignatureManager
        import numpy as np

        manager = HandwritingSignatureManager("demo_signatures.db")

        # 创建测试签名
        test_signatures = {
            "张三": np.random.randint(0, 255, (100, 200), dtype=np.uint8),
            "李四": np.random.randint(0, 255, (80, 150), dtype=np.uint8),
        }

        print("\n📝 添加测试签名...")
        for name, signature in test_signatures.items():
            success = manager.add_signature(name, signature)
            print(f"   {'✅' if success else '❌'} {name}")

        print("\n🔍 测试签名匹配...")
        for name, signature in test_signatures.items():
            matches = manager.match_signature(signature, threshold=0.5)
            print(f"\n   查询: {name}")
            if matches:
                for match in matches[:2]:
                    print(f"   ✅ 匹配: {match['printed_name']} (相似度: {match['max_similarity']:.3f})")
            else:
                print("   ❌ 无匹配")

        # 显示统计
        users = manager.list_all_users()
        print(f"\n📊 数据库统计: {len(users)}个用户")

    except Exception as e:
        print(f"❌ 演示失败: {e}")


def run_full_enhanced_ocr():
    """运行完整增强识别流程"""
    print("\n🚀 运行完整增强识别流程...")
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        from drawing_ocr_tool import DrawingOCRTool

        # 查找测试图片
        test_image = None
        for pattern in ["examples/test_invoice*.png", "examples/test_invoice*.jpg"]:
            import glob
            images = glob.glob(pattern)
            if images:
                test_image = images[0]
                break

        if test_image:
            print(f"📷 处理图片: {test_image}")

            ocr_tool = DrawingOCRTool()
            result = ocr_tool.process_drawing_enhanced(test_image, enable_signature_matching=True)

            if result:
                print("\n✅ 增强识别完成!")
                print(f"   处理时间: {result.get('处理时间')}")
                print(f"   解析方式: {result.get('解析方式')}")
                print(f"   AI置信度: {result.get('AI置信度'):.1f}%")

                # 显示增强功能状态
                enhanced_features = result.get('增强功能', {})
                print(f"\n🔧 增强功能:")
                for feature, status in enhanced_features.items():
                    icon = "✅" if status else "❌"
                    print(f"   {icon} {feature}: {'启用' if status else '未启用'}")

                # 显示处理统计
                stats = result.get('处理统计', {})
                if stats:
                    print(f"\n📊 处理统计:")
                    for key, value in stats.items():
                        print(f"   {key}: {value}")

                # 显示提取的字段
                fields = result.get('提取字段', {})
                if fields:
                    print(f"\n📋 提取字段 ({len(fields)}个):")
                    for field_name, field_value in list(fields.items())[:5]:  # 显示前5个
                        status = "✅" if field_value else "❌"
                        print(f"   {status} {field_name}: {field_value or '未识别'}")
                    if len(fields) > 5:
                        print(f"   ... 还有{len(fields)-5}个字段")

            else:
                print("❌ 增强识别失败")
        else:
            print("⚠️  未找到测试图片，请将测试图片放在 examples/ 目录下")

    except Exception as e:
        print(f"❌ 运行失败: {e}")
        import traceback
        traceback.print_exc()


def start_original_gui():
    """启动原有GUI界面"""
    print("\n🖥️ 启动原有GUI界面...")
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        from invoice_gui import InvoiceOCRGUI
        app = InvoiceOCRGUI()
        app.run()
    except Exception as e:
        print(f"❌ GUI启动失败: {e}")


def show_technical_report():
    """显示技术实现报告"""
    print("\n📄 技术实现报告")
    print("=" * 40)

    # 查找最新的测试报告
    import glob
    report_files = glob.glob("enhanced_drawing_ocr_test_report_*.json")

    if report_files:
        latest_report = max(report_files)
        print(f"📋 最新测试报告: {latest_report}")

        try:
            import json
            with open(latest_report, 'r', encoding='utf-8') as f:
                report = json.load(f)

            print(f"\n📅 测试时间: {report.get('test_time')}")

            implemented_features = report.get('implemented_features', {})
            print(f"\n✅ 已实现功能 ({len(implemented_features)}个):")
            for feature, status in implemented_features.items():
                print(f"   {status} {feature}")

            gemini_integration = report.get('gemini_technology_integration', {})
            print(f"\n🤖 Gemini技术融合 ({len(gemini_integration)}个):")
            for tech, status in gemini_integration.items():
                print(f"   {status} {tech}")

        except Exception as e:
            print(f"❌ 读取报告失败: {e}")
    else:
        print("⚠️  未找到测试报告")

    print(f"\n📁 相关文件:")
    print(f"   • src/enhanced_signature_detector.py - 增强图签检测器")
    print(f"   • src/handwriting_signature_manager.py - 手写签名管理器")
    print(f"   • src/drawing_ocr_tool.py - 增强图纸OCR工具")
    print(f"   • test_enhanced_drawing_ocr.py - 测试脚本")
    print(f"   • signature_database.db - 签名数据库")


def install_optional_dependencies():
    """安装可选依赖"""
    print("\n📦 安装可选依赖...")
    optional_deps = [
        "torch>=2.0.0",
        "torchvision>=0.15.0",
        "scikit-learn>=1.3.0"
    ]

    import subprocess

    for dep in optional_deps:
        print(f"\n正在安装 {dep}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✅ {dep} 安装成功")
        except subprocess.CalledProcessError:
            print(f"❌ {dep} 安装失败")

    print(f"\n可选依赖安装完成！重启程序以生效。")


def main():
    """主函数"""
    print_banner()

    # 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败，程序无法运行")
        input("按任意键退出...")
        return

    # 主循环
    while True:
        show_menu()

        try:
            choice = input("\n请输入选择 (1-7): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 再见！")
            break

        if choice == "1":
            test_enhanced_signature_detection()
        elif choice == "2":
            demo_signature_database()
        elif choice == "3":
            run_full_enhanced_ocr()
        elif choice == "4":
            start_original_gui()
        elif choice == "5":
            show_technical_report()
        elif choice == "6":
            install_optional_dependencies()
        elif choice == "7":
            print("\n👋 再见！")
            break
        else:
            print("\n❌ 无效选择，请输入 1-7")

        if choice != "7":
            input("\n按回车键继续...")


if __name__ == "__main__":
    main()