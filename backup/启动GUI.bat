@echo off
cd /d "%~dp0"
title 发票OCR识别工具
echo 正在启动专用发票OCR识别工具...
python start_gui.py
if errorlevel 1 (
    echo.
    echo 启动失败，请检查Python环境和依赖库
    pause
)