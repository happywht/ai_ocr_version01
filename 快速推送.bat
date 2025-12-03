@echo off
chcp 65001 >nul
echo ========================================
echo   票据OCR识别工具 - 快速推送脚本
echo ========================================
echo.

echo 📋 当前Git状态：
cd /d "D:\Work\202512\票据识别工具"
git status --short
echo.

echo 📝 请先在GitHub上创建仓库：
echo.
echo 🔗 步骤：
echo    1. 打开 https://github.com
echo    2. 登录您的账号（776815438@qq.com）
echo    3. 点击右上角 "+" → "New repository"
echo    4. 仓库名: invoice-ocr-tool
echo    5. 描述: 智能票据OCR识别工具
echo    6. 选择 Public（推荐）
echo    7. 不要勾选任何初始化选项
echo    8. 点击 "Create repository"
echo.

echo ⚠️  重要提示：
echo    GitHub可能要求您使用Personal Access Token代替密码
echo    如果需要，请访问：https://github.com/settings/tokens
echo.

echo 🚀 创建完成后，双击此脚本继续...

pause