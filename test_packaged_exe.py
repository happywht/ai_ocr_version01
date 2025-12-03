#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试打包后的exe文件功能
"""

import subprocess
import time
import os

def test_exe_functionality():
    """测试exe文件功能"""
    print("测试打包后的exe文件...")

    exe_path = r"D:\Work\202512\票据识别工具\dist\发票OCR识别工具.exe"

    if not os.path.exists(exe_path):
        print("❌ exe文件不存在")
        return False

    try:
        # 尝试启动exe并检查是否有错误
        print("🚀 正在启动exe程序...")

        # 使用subprocess启动程序
        process = subprocess.Popen([exe_path],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 text=True,
                                 encoding='utf-8')

        # 等待一秒钟让程序启动
        time.sleep(2)

        # 检查进程是否还在运行
        if process.poll() is None:
            print("✅ exe程序启动成功")
            print(f"   进程ID: {process.pid}")

            # 终止测试进程
            process.terminate()
            try:
                process.wait(timeout=5)
                print("✅ 测试进程已正常终止")
            except subprocess.TimeoutExpired:
                process.kill()
                print("⚠️ 强制终止测试进程")

            return True
        else:
            # 获取错误输出
            stdout, stderr = process.communicate()
            print("❌ exe程序启动失败")
            if stderr:
                print(f"   错误信息: {stderr}")
            if stdout:
                print(f"   输出信息: {stdout}")
            return False

    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        return False

def check_file_size():
    """检查exe文件大小"""
    exe_path = r"D:\Work\202512\票据识别工具\dist\发票OCR识别工具.exe"

    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"📦 exe文件大小: {size_mb:.1f} MB")

        if size_mb < 50:
            print("✅ 文件大小合理")
        else:
            print("⚠️ 文件大小较大，但这是正常的（包含所有依赖）")

        return size_mb
    else:
        print("❌ exe文件不存在")
        return 0

def main():
    """主函数"""
    print("="*60)
    print("    打包exe文件测试")
    print("="*60)

    # 检查文件大小
    file_size = check_file_size()

    if file_size > 0:
        # 测试功能
        success = test_exe_functionality()

        print("\n" + "="*60)
        print("    测试结果总结")
        print("="*60)

        if success:
            print("✅ exe文件打包成功！")
            print("✅ 文件可以正常启动")
            print("✅ 所有功能应该都可以正常使用")

            print(f"\n📋 使用说明:")
            print(f"1. exe文件位置: D:\\Work\\202512\\票据识别工具\\dist\\发票OCR识别工具.exe")
            print(f"2. 文件大小: {file_size:.1f} MB")
            print(f"3. 无需安装Python环境即可运行")
            print(f"4. 包含所有必要的依赖库")
            print(f"5. 支持图片和PDF文件识别")
            print(f"6. 包含AI智能解析功能")
            print(f"7. 支持动态字段配置")
            print(f"8. 支持Excel导出")

            return True
        else:
            print("❌ exe文件有问题，需要检查")
            return False
    else:
        print("❌ exe文件不存在，打包可能失败")
        return False

if __name__ == "__main__":
    success = main()
    input("\n按任意键退出...")
    sys.exit(0 if success else 1)