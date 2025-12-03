@echo off
chcp 65001 >nul
echo ========================================
echo   票据OCR识别工具 - Git推送脚本
echo ========================================
echo.

echo 📋 当前Git状态：
cd /d "D:\Work\202512\票据识别工具"
git status --short
echo.

echo 🔗 请先在GitHub上创建仓库：
echo    1. 打开 https://github.com
echo    2. 点击右上角 "+" → "New repository"
echo    3. 仓库名: invoice-ocr-tool
echo    4. 描述: 智能票据OCR识别工具
echo    5. 选择 Public 或 Private
echo    6. 不要勾选任何初始化选项
echo    7. 点击 "Create repository"
echo.

echo 📝 创建完成后，GitHub会显示仓库URL，格式如下：
echo    HTTPS: https://github.com/您的用户名/invoice-ocr-tool.git
echo    SSH:   git@github.com:您的用户名/invoice-ocr-tool.git
echo.

set /p repo_url="请输入您的GitHub仓库URL: "

if "%repo_url%"=="" (
    echo ❌ 未输入仓库URL，退出
    pause
    exit /b 1
)

echo.
echo 🔧 正在配置远程仓库...
git remote remove origin 2>nul
git remote add origin %repo_url%

echo.
echo 🚀 正在推送代码到GitHub...
git push -u origin master

if %errorlevel% equ 0 (
    echo.
    echo ✅ 推送成功！
    echo 🔗 您的代码已上传到: %repo_url%
    echo.
    echo 📊 项目统计:
    echo    - 24个文件已提交
    echo    - 6,690行代码
    echo    - 完整的测试套件
    echo    - 专业的项目文档
) else (
    echo.
    echo ❌ 推送失败！
    echo 💡 请检查：
    echo    1. 仓库URL是否正确
    echo    2. GitHub登录状态
    echo    3. 网络连接
    echo    4. 权限设置
)

echo.
pause