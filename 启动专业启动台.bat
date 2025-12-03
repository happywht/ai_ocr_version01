@echo off
chcp 65001 >nul
title 发票OCR识别工具 - 专业启动台

echo.
echo ========================================
echo    发票OCR识别工具 - 专业启动台
echo ========================================
echo.

echo 🚀 正在启动专业启动台...
echo.

REM 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或未添加到PATH环境变量
    echo.
    echo 请确保:
    echo 1. 已安装Python 3.7+
    echo 2. Python已添加到系统PATH环境变量
    echo.
    pause
    exit /b 1
)

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 启动快速启动脚本
python 快速启动.py

REM 检查退出代码
if errorlevel 1 (
    echo.
    echo ❌ 启动失败，请检查错误信息
    pause
) else (
    echo.
    echo ✅ 程序已正常退出
)

pause