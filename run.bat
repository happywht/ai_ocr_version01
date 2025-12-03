@echo off
chcp 65001 >nul
title 专用发票OCR识别工具

echo ==========================================
echo        专用发票OCR识别工具 - AI增强版
echo ==========================================
echo.

python start.py

if errorlevel 1 (
    echo.
    echo 程序执行出错，请检查Python环境和依赖库
    pause
)