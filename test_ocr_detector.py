#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试OCR服务智能检测功能
"""

import sys
import os

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

def test_ocr_detector():
    """测试OCR服务检测器"""
    print("="*60)
    print("    OCR服务智能检测功能测试")
    print("="*60)

    try:
        from ocr_service_detector import OCRServiceDetector, ocr_detector

        print("✅ OCR检测器导入成功")

        # 测试检测器类
        detector = OCRServiceDetector()
        print(f"✅ 检测器实例创建成功")
        print(f"   常见路径数量: {len(detector.common_paths)}")
        print(f"   保存路径数量: {len(detector.saved_paths)}")

        # 测试搜索功能
        print(f"\n🔍 开始搜索OCR服务...")
        services = detector.find_ocr_services()

        if services:
            print(f"✅ 找到 {len(services)} 个OCR服务:")
            for i, (path, service_type) in enumerate(services, 1):
                print(f"   {i}. {path}")
                print(f"      类型: {service_type}")
                print(f"      存在: {os.path.exists(path)}")

                # 检查具体文件
                exe_file = os.path.join(path, "Umi-OCR.exe")
                main_script = os.path.join(path, "main.py")
                print(f"      exe文件: {os.path.exists(exe_file)}")
                print(f"      main脚本: {os.path.exists(main_script)}")

            # 测试最佳服务
            best_service = detector.get_best_service()
            if best_service:
                print(f"\n🎯 最佳OCR服务:")
                print(f"   路径: {best_service[0]}")
                print(f"   类型: {best_service[1]}")

                # 测试保存功能
                detector.save_path(best_service[0])
                print(f"   ✅ 路径已保存到配置文件")
        else:
            print(f"❌ 未找到OCR服务")
            print(f"\n💡 可能的原因:")
            print(f"   1. umi-OCR未安装")
            print(f"   2. 安装路径不在常见位置")
            print(f"   3. 服务文件损坏")

        # 测试便捷函数
        print(f"\n🔧 测试便捷函数:")
        best_path = ocr_detector.get_best_service()
        if best_path:
            print(f"   ✅ 便捷函数检测成功: {best_path[0]}")
        else:
            print(f"   ❌ 便捷函数检测失败")

        return len(services) > 0

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_manual_add():
    """测试手动添加路径"""
    print("\n" + "="*60)
    print("    手动添加路径测试")
    print("="*60)

    try:
        from ocr_service_detector import ocr_detector

        # 测试添加无效路径
        invalid_path = "C:\\不存在的路径"
        result = ocr_detector.manual_add_path(invalid_path)
        print(f"添加无效路径 '{invalid_path}': {result} (应该是False)")

        # 如果有找到的服务，测试重复添加
        existing_service = ocr_detector.get_best_service()
        if existing_service:
            valid_path = existing_service[0]
            result = ocr_detector.manual_add_path(valid_path)
            print(f"添加有效路径 '{valid_path}': {result} (应该是True)")

        return True

    except Exception as e:
        print(f"❌ 手动添加测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始OCR服务智能检测功能测试...\n")

    # 测试检测功能
    test1_result = test_ocr_detector()

    # 测试手动添加
    test2_result = test_manual_add()

    print("\n" + "="*60)
    print("    测试结果总结")
    print("="*60)

    if test1_result and test2_result:
        print("✅ OCR服务智能检测功能测试通过！")
        print("\n🎯 功能特点:")
        print("1. 🔍 智能搜索：自动检测系统中的umi-OCR服务")
        print("2. 📁 路径管理：保存和记忆常用的OCR服务路径")
        print("3. 🎛️ 手动配置：支持手动指定OCR服务路径")
        print("4. 🔄 自动回退：多层检测机制确保找到服务")
        print("5. 📱 GUI集成：友好的用户界面支持")

        print("\n💡 使用建议:")
        print("- 如果自动检测失败，可以手动指定路径")
        print("- 支持的文件：Umi-OCR.exe, main.py")
        print("- 配置文件保存在: config/ocr_paths.json")
        print("- 最多保存10个历史路径")

        return True
    else:
        print("❌ 部分检测功能存在问题")
        return False

if __name__ == "__main__":
    success = main()
    input("\n按任意键退出...")
    sys.exit(0 if success else 1)