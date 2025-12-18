#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专用图纸图签OCR识别工具 - GUI优化版本
提供用户友好的图形界面，集成AI智能识别功能
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import json
import logging
from datetime import datetime
from PIL import Image, ImageTk
import io
import base64
from invoice_ocr_tool import InvoiceOCRTool
from excel_exporter import ExcelExporter

# 导入字段配置管理器
try:
    from field_config import field_config_manager
    FIELD_CONFIG_AVAILABLE = True
except ImportError:
    FIELD_CONFIG_AVAILABLE = False


class InvoiceOCRGUI:
    """图纸图签OCR识别工具优化GUI界面"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("图纸图签OCR识别工具 - 老王特供")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)

        # 设置窗口图标和样式
        self.setup_styles()

        # 初始化OCR工具 (默认启用AI)
        try:
            self.ocr_tool = InvoiceOCRTool(use_ai=True)
            self.ai_enabled = self.ocr_tool.use_ai
        except Exception as e:
            messagebox.showerror("初始化错误", f"OCR工具初始化失败:\n{str(e)}")
            self.root.destroy()
            return

        # 初始化Excel导出器
        try:
            self.excel_exporter = ExcelExporter()
            self.excel_enabled = True
        except Exception as e:
            self.excel_enabled = False
            print(f"Excel导出器初始化失败: {e}")

        # 初始化logger
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        # 当前图片路径和数据
        self.current_image_path = None
        self.current_result = None
        self.ai_confidence = None
        self.parsing_method = None

        # 创建界面
        self.create_widgets()

        # 测试服务连接
        self.test_connections_async()

    def setup_styles(self):
        """设置界面样式"""
        try:
            style = ttk.Style()
            style.theme_use('clam')

            # 自定义颜色
            style.configure('Title.TLabel', font=('微软雅黑', 18, 'bold'), foreground='#2c3e50')
            style.configure('Header.TLabel', font=('微软雅黑', 12, 'bold'))
            style.configure('Success.TLabel', foreground='#27ae60')
            style.configure('Error.TLabel', foreground='#e74c3c')
            style.configure('Warning.TLabel', foreground='#f39c12')
            style.configure('Info.TLabel', foreground='#3498db')
            style.configure('Status.TLabel', font=('微软雅黑', 10))

            # 按钮样式
            style.configure('Primary.TButton', font=('微软雅黑', 10, 'bold'))

        except Exception:
            # 如果样式设置失败，使用默认样式
            pass

    def create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_container = ttk.Frame(self.root, padding="15")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=3)
        main_container.rowconfigure(1, weight=1)

        # 标题区域
        self.create_header(main_container)

        # 主内容区域
        content_frame = ttk.Frame(main_container)
        content_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(20, 0))
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=2)
        content_frame.rowconfigure(0, weight=1)

        # 左侧面板 - 图片选择和状态
        self.create_left_panel(content_frame)

        # 右侧面板 - 结果显示
        self.create_right_panel(content_frame)

        # 底部操作面板
        self.create_bottom_panel(main_container)

    def create_header(self, parent):
        """创建标题区域"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))

        # 主标题
        title_label = ttk.Label(header_frame, text="图纸图签OCR识别工具", style='Title.TLabel')
        title_label.grid(row=0, column=0, sticky=tk.W)

        # AI状态标识
        ai_status_text = "🤖 AI增强版" if self.ai_enabled else "📝 传统版"
        ai_status_color = "Success.TLabel" if self.ai_enabled else "Info.TLabel"
        ai_status_label = ttk.Label(header_frame, text=ai_status_text, style=ai_status_color)
        ai_status_label.grid(row=0, column=1, sticky=tk.E, padx=(20, 0))

        # 版本信息
        version_label = ttk.Label(header_frame, text="v2.0", style='Status.TLabel')
        version_label.grid(row=0, column=2, sticky=tk.E, padx=(10, 0))

    def create_left_panel(self, parent):
        """创建左侧面板"""
        left_frame = ttk.LabelFrame(parent, text="📷 图片选择", padding="15")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 15))
        left_frame.rowconfigure(2, weight=1)
        left_frame.columnconfigure(0, weight=1)

        # 文件选择区域
        file_frame = ttk.Frame(left_frame)
        file_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        file_frame.columnconfigure(0, weight=1)

        # 选择文件按钮
        select_btn = ttk.Button(file_frame, text="📂 选择图纸图片",
                               command=self.select_image, style='Primary.TButton')
        select_btn.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # 文件路径显示
        self.image_path_var = tk.StringVar(value="📄 未选择图片")
        path_frame = ttk.Frame(file_frame)
        path_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        path_frame.columnconfigure(0, weight=1)

        path_label = ttk.Label(path_frame, textvariable=self.image_path_var,
                              style='Status.TLabel', wraplength=300)
        path_label.grid(row=0, column=0, sticky=tk.W)

        # 状态信息区域
        status_frame = ttk.LabelFrame(left_frame, text="📊 服务状态", padding="10")
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(15, 0))
        status_frame.columnconfigure(0, weight=1)  # OCR状态标签占据大部分空间
        status_frame.columnconfigure(1, weight=0)  # 启动按钮固定大小

        # OCR服务状态和启动按钮在同一行
        self.ocr_status_var = tk.StringVar(value="检测中...")
        ocr_status_label = ttk.Label(status_frame, textvariable=self.ocr_status_var,
                                   style='Status.TLabel')
        ocr_status_label.grid(row=0, column=0, sticky=tk.W)

        # OCR服务启动按钮 (初始隐藏，放在状态标签右侧)
        self.start_ocr_btn = ttk.Button(status_frame, text="🚀 启动",
                                        command=self.start_ocr_service,
                                        style='Primary.TButton',
                                        width=10)  # 设置固定宽度
        # 按钮初始状态为隐藏，后续根据检测结果显示

        # AI服务状态
        if self.ai_enabled:
            self.ai_status_var = tk.StringVar(value="检测中...")
            ai_status_label = ttk.Label(status_frame, textvariable=self.ai_status_var,
                                      style='Status.TLabel')
            ai_status_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))

        # 图片预览区域
        preview_frame = ttk.LabelFrame(left_frame, text="🖼️ 图片预览", padding="10")
        preview_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(15, 0))
        preview_frame.rowconfigure(0, weight=1)
        preview_frame.columnconfigure(0, weight=1)

        self.image_preview_label = ttk.Label(preview_frame,
                                           text="暂无图片\n\n请选择图纸图片进行预览",
                                           background='#f8f9fa',
                                           relief='sunken',
                                           anchor='center')
        self.image_preview_label.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    def create_right_panel(self, parent):
        """创建右侧面板"""
        right_frame = ttk.LabelFrame(parent, text="📋 识别结果", padding="15")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)

        # 解析信息栏
        info_frame = ttk.Frame(right_frame)
        info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        info_frame.columnconfigure(2, weight=1)

        # 解析方式
        ttk.Label(info_frame, text="解析方式:", style='Status.TLabel').grid(row=0, column=0, sticky=tk.W)
        self.method_var = tk.StringVar(value="待识别")
        method_label = ttk.Label(info_frame, textvariable=self.method_var, style='Info.TLabel')
        method_label.grid(row=0, column=1, sticky=tk.W, padx=(5, 20))

        # 置信度
        self.confidence_var = tk.StringVar(value="")
        confidence_label = ttk.Label(info_frame, textvariable=self.confidence_var, style='Status.TLabel')
        confidence_label.grid(row=0, column=2, sticky=tk.W)

        # 结果显示区域
        self.create_result_display(right_frame)

    def create_result_display(self, parent):
        """创建结果显示区域"""
        # 创建Notebook用于多标签页显示
        self.result_notebook = ttk.Notebook(parent)
        self.result_notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 提取字段标签页
        self.fields_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.fields_frame, text="📊 提取字段")
        self.create_fields_display()

        # 原始OCR结果标签页
        self.raw_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.raw_frame, text="📄 原始OCR结果")
        self.create_raw_display()

        # AI分析结果标签页 (仅AI版本显示)
        if self.ai_enabled:
            self.ai_frame = ttk.Frame(self.result_notebook)
            self.result_notebook.add(self.ai_frame, text="🤖 AI分析结果")
            self.create_ai_display()

    def create_fields_display(self):
        """创建字段显示区域"""
        # 表格容器
        table_container = ttk.Frame(self.fields_frame, padding="10")
        table_container.pack(fill='both', expand=True)

        # 创建Treeview表格
        columns = ('字段名称', '提取内容', '状态')
        self.fields_tree = ttk.Treeview(table_container, columns=columns, show='headings', height=12)

        # 设置列标题和属性
        self.fields_tree.heading('字段名称', text='🏷️ 字段名称')
        self.fields_tree.heading('提取内容', text='📝 提取内容')
        self.fields_tree.heading('状态', text='✅ 状态')

        # 设置列宽
        self.fields_tree.column('字段名称', width=150, minwidth=100)
        self.fields_tree.column('提取内容', width=300, minwidth=200)
        self.fields_tree.column('状态', width=100, minwidth=80)

        # 设置样式
        self.fields_tree.tag_configure('required', background='#fff8e1')  # 必需字段浅黄色背景
        self.fields_tree.tag_configure('optional', background='#f1f8e9')   # 可选字段浅绿色背景

        # 添加滚动条
        scrollbar_v = ttk.Scrollbar(table_container, orient="vertical", command=self.fields_tree.yview)
        scrollbar_h = ttk.Scrollbar(table_container, orient="horizontal", command=self.fields_tree.xview)
        self.fields_tree.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)

        # 布局
        self.fields_tree.grid(row=0, column=0, sticky='nsew')
        scrollbar_v.grid(row=0, column=1, sticky='ns')
        scrollbar_h.grid(row=1, column=0, sticky='ew')

        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        # 初始化显示字段列表
        self.load_fields_list()

        # 配置行颜色
        self.fields_tree.tag_configure('success', background='#d4edda')
        self.fields_tree.tag_configure('warning', background='#fff3cd')
        self.fields_tree.tag_configure('error', background='#f8d7da')

    def create_raw_display(self):
        """创建原始结果显示区域"""
        raw_container = ttk.Frame(self.raw_frame, padding="10")
        raw_container.pack(fill='both', expand=True)

        # 原始结果文本框
        self.raw_text = scrolledtext.ScrolledText(raw_container,
                                                wrap=tk.WORD,
                                                font=('Consolas', 9),
                                                height=20)
        self.raw_text.pack(fill='both', expand=True)

    def create_ai_display(self):
        """创建AI分析结果显示区域"""
        ai_container = ttk.Frame(self.ai_frame, padding="10")
        ai_container.pack(fill='both', expand=True)

        # AI分析结果文本框
        self.ai_text = scrolledtext.ScrolledText(ai_container,
                                               wrap=tk.WORD,
                                               font=('微软雅黑', 9),
                                               height=20)
        self.ai_text.pack(fill='both', expand=True)

    def create_bottom_panel(self, parent):
        """创建底部操作面板"""
        bottom_frame = ttk.Frame(parent)
        bottom_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(20, 0))
        bottom_frame.columnconfigure(0, weight=1)

        # 操作按钮区域
        button_frame = ttk.Frame(bottom_frame)
        button_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        button_frame.columnconfigure(5, weight=1)

        # 识别按钮
        self.recognize_btn = ttk.Button(button_frame, text="🚀 开始识别",
                                       command=self.start_recognition,
                                       style='Primary.TButton')
        self.recognize_btn.grid(row=0, column=0, padx=(0, 10))

        # AI切换按钮 (仅AI版本显示)
        if self.ai_enabled:
            self.ai_toggle_var = tk.BooleanVar(value=True)
            ai_toggle = ttk.Checkbutton(button_frame, text="🤖 启用AI智能解析",
                                       variable=self.ai_toggle_var,
                                       command=self.toggle_ai_mode)
            ai_toggle.grid(row=0, column=1, padx=(0, 10))

        # 导出按钮
        export_btn = ttk.Button(button_frame, text="💾 导出结果",
                               command=self.export_results)
        export_btn.grid(row=0, column=2, padx=(0, 10))

        # 批量处理按钮
        batch_btn = ttk.Button(button_frame, text="📁 批量处理",
                              command=self.batch_process)
        batch_btn.grid(row=0, column=3, padx=(0, 10))

        
        # 清除按钮
        clear_btn = ttk.Button(button_frame, text="🗑️ 清除结果",
                              command=self.clear_results)
        clear_btn.grid(row=0, column=4, padx=(0, 10))

        # 进度显示
        progress_frame = ttk.Frame(bottom_frame)
        progress_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(15, 0))
        progress_frame.columnconfigure(0, weight=1)

        # 进度条
        self.progress_var = tk.StringVar(value="🔄 就绪")
        progress_label = ttk.Label(progress_frame, textvariable=self.progress_var,
                                  style='Status.TLabel')
        progress_label.grid(row=0, column=0, sticky=tk.W)

        # 进度条
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate', length=200)
        self.progress_bar.grid(row=0, column=1, sticky=tk.E, padx=(10, 0))

    def select_image(self):
        """选择图纸文件"""
        file_types = [
            ('支持的文件', '*.jpg *.jpeg *.png *.bmp *.tiff *.pdf'),
            ('PDF文件', '*.pdf'),
            ('图片文件', '*.jpg *.jpeg *.png *.bmp *.tiff'),
            ('JPEG文件', '*.jpg *.jpeg'),
            ('PNG文件', '*.png'),
            ('所有文件', '*.*')
        ]

        file_path = filedialog.askopenfilename(
            title="选择图纸文件",
            filetypes=file_types
        )

        if file_path:
            self.current_image_path = file_path
            filename = os.path.basename(file_path)
            self.image_path_var.set(f"📄 {filename}")
            self.display_image_preview(file_path)

    def display_image_preview(self, image_path):
        """显示图片或PDF预览"""
        try:
            # 检查是否为PDF文件
            if image_path.lower().endswith('.pdf'):
                self.logger.info(f"显示PDF预览: {image_path}")

                # 检查pypdfium2是否可用
                try:
                    import pypdfium2 as pdfium
                except ImportError:
                    self.image_preview_label.configure(
                        image='',
                        text="❌ PDF预览失败\npypdfium2库未安装\n请运行: pip install pypdfium2",
                        background='#ffe0e0'
                    )
                    return

                # 打开PDF文件
                pdf = None
                page = None
                bitmap = None

                try:
                    pdf = pdfium.PdfDocument(image_path)
                    self.logger.info(f"PDF预览打开成功，共 {len(pdf)} 页")

                    # 处理第一页
                    page = pdf[0]

                    # 渲染页面为图片（预览用较低分辨率）
                    bitmap = page.render(
                        scale=0.8,  # 适合预览的分辨率
                    )

                    # 将渲染的位图转换为PIL Image
                    image = bitmap.to_pil()

                except Exception as pdf_error:
                    self.image_preview_label.configure(
                        image='',
                        text=f"❌ PDF预览失败\n{str(pdf_error)}\n请检查PDF文件是否损坏",
                        background='#ffe0e0'
                    )
                    return
                finally:
                    # 清理PDF资源
                    if bitmap:
                        bitmap = None
                    if page:
                        page = None
                    if pdf:
                        pdf.close()
            else:
                # 加载图片文件
                try:
                    image = Image.open(image_path)
                except Exception as img_error:
                    self.image_preview_label.configure(
                        image='',
                        text=f"❌ 图片预览失败\n{str(img_error)}\n请检查图片文件格式",
                        background='#ffe0e0'
                    )
                    return

            # 调整图片大小以适应预览区域
            preview_width = 350
            preview_height = 450

            # 保持宽高比缩放
            image.thumbnail((preview_width, preview_height), Image.Resampling.LANCZOS)

            # 转换为PhotoImage
            photo = ImageTk.PhotoImage(image)

            # 显示图片
            self.image_preview_label.configure(image=photo, text="", background='white')
            self.image_preview_label.image = photo  # 保持引用

            # 更新状态
            file_type = "PDF" if image_path.lower().endswith('.pdf') else "图片"
            self.progress_var.set(f"📷 {file_type}已选择，点击'开始识别'进行处理")

        except Exception as e:
            self.logger.error(f"预览显示失败: {e}")
            self.image_preview_label.configure(
                image='',
                text=f"❌ 预览失败\n{str(e)}",
                background='#ffe0e0'
            )

    def test_connections_async(self):
        """异步测试服务连接"""
        def test_connections():
            try:
                # 测试OCR服务
                if self.ocr_tool.test_ocr_connection():
                    self.root.after(0, lambda: self.ocr_status_var.set("✅ OCR服务正常"))
                    self.root.after(0, lambda: self.start_ocr_btn.grid_forget())  # 隐藏启动按钮
                else:
                    self.root.after(0, lambda: self.ocr_status_var.set("❌ OCR服务未运行"))
                    self.root.after(0, lambda: self.start_ocr_btn.grid(row=0, column=1, padx=(10, 0), sticky=tk.E))  # 显示启动按钮在右侧

                # 测试AI服务 (如果启用)
                if self.ai_enabled and self.ocr_tool.ai_parser:
                    if self.ocr_tool.ai_parser.test_ai_connection():
                        self.root.after(0, lambda: self.ai_status_var.set("✅ AI服务正常"))
                    else:
                        self.root.after(0, lambda: self.ai_status_var.set("❌ AI服务失败"))

            except Exception as e:
                error_msg = f"连接测试失败: {str(e)}"
                self.root.after(0, lambda: self.progress_var.set(f"⚠️ {error_msg}"))

        # 在后台线程中测试连接
        threading.Thread(target=test_connections, daemon=True).start()

    def toggle_ai_mode(self):
        """切换AI模式"""
        self.ocr_tool.use_ai = self.ai_toggle_var.get()
        status = "启用" if self.ocr_tool.use_ai else "禁用"
        self.progress_var.set(f"🤖 AI智能解析已{status}")

    def start_recognition(self):
        """开始OCR识别"""
        if not self.current_image_path:
            messagebox.showwarning("警告", "请先选择图纸图片或PDF文件")
            return

        # 禁用识别按钮防止重复操作
        self.recognize_btn.configure(state='disabled')
        self.progress_var.set("🔄 正在识别中，请稍候...")
        self.progress_bar.start(10)
        self.root.update()

        def recognize_image():
            try:
                # 确定文件类型
                file_type = "PDF" if self.current_image_path.lower().endswith('.pdf') else "图片"

                # 执行OCR识别
                result = self.ocr_tool.process_invoice(self.current_image_path)

                if result:
                    # 在主线程中更新界面
                    self.root.after(0, self.display_results, result)
                else:
                    # OCR识别返回None，提供更具体的错误信息
                    error_msg = f"{file_type}识别失败，请检查：\n" \
                              f"1. {file_type}文件是否损坏或加密\n" \
                              f"2. umi-OCR服务是否正常运行(127.0.0.1:1224)\n" \
                              f"3. {file_type}文件质量是否清晰可读"
                    self.root.after(0, self.show_error, error_msg)

            except Exception as e:
                # 其他异常
                file_type = "PDF" if self.current_image_path.lower().endswith('.pdf') else "图片"
                error_msg = f"{file_type}识别异常: {str(e)}\n\n" \
                          f"请检查：\n" \
                          f"1. {file_type}文件格式是否正确\n" \
                          f"2. umi-OCR服务是否正常运行\n" \
                          f"3. 网络连接是否正常"
                self.root.after(0, self.show_error, error_msg)
            finally:
                # 重新启用按钮
                self.root.after(0, lambda: self.recognize_btn.configure(state='normal'))
                self.root.after(0, lambda: self.progress_bar.stop())

        # 在后台线程中执行识别
        threading.Thread(target=recognize_image, daemon=True).start()

    def display_results(self, result):
        """显示识别结果"""
        if not result:
            self.progress_var.set("❌ 识别失败")
            messagebox.showerror("错误", "图纸图签识别失败，请检查图片质量")
            return

        self.current_result = result

        # 清除现有结果
        self.clear_results()

        # 获取解析方法信息
        extracted_fields = result.get('提取字段', {})
        parsing_method = getattr(result, 'parsing_method', '未知')
        ai_confidence = getattr(result, 'ai_confidence', None)

        # 更新解析信息
        if self.ai_enabled:
            method_text = "🤖 AI智能解析" if 'AI' in parsing_method else "📝 传统正则解析"
            self.method_var.set(method_text)

            if ai_confidence is not None:
                self.confidence_var.set(f"置信度: {ai_confidence:.1%}")
            else:
                self.confidence_var.set("")
        else:
            self.method_var.set("📝 传统正则解析")
            self.confidence_var.set("")

        # 显示提取的字段
        field_status_map = {
            '项目名称': '✅',
            '设计人': '✅',
            '审核人': '✅',
            '审定人': '✅',
            '图纸编号': '✅',
            '出图日期': '✅'
        }

        for field_name, field_value in extracted_fields.items():
            if field_value:
                status = field_status_map.get(field_name, '✅')
                tag = 'success'
            else:
                status = '❌'
                tag = 'error'

            item = self.fields_tree.insert('', 'end', values=(field_name, field_value or "未识别", status))
            if tag:
                self.fields_tree.item(item, tags=(tag,))

        # 显示原始OCR结果
        if 'OCR原始结果' in result and result['OCR原始结果']:
            raw_json = json.dumps(result['OCR原始结果'], ensure_ascii=False, indent=2)
            self.raw_text.insert(tk.END, raw_json)

        # 显示AI分析结果 (仅AI版本)
        if self.ai_enabled and hasattr(result, 'ai_analysis') and result.ai_analysis:
            ai_text = result.ai_analysis
            self.ai_text.insert(tk.END, ai_text)
        elif self.ai_enabled and 'AI原始响应' in result and result['AI原始响应']:
            ai_text = result['AI原始响应']
            self.ai_text.insert(tk.END, ai_text)

        # 更新状态
        extracted_count = len([v for v in extracted_fields.values() if v])
        # 获取当前配置的字段总数
        if FIELD_CONFIG_AVAILABLE:
            total_fields = len(field_config_manager.get_field_names())
        else:
            total_fields = 6
        self.progress_var.set(f"✅ 识别完成！成功提取 {extracted_count}/{total_fields} 个字段")

        # 显示成功消息
        messagebox.showinfo("成功", f"图纸图签识别完成！\n成功提取 {extracted_count} 个字段")

    def show_error(self, error_msg):
        """显示错误信息"""
        self.progress_var.set("❌ 识别失败")
        messagebox.showerror("错误", error_msg)

    def clear_results(self):
        """清除结果"""
        # 清除字段表格
        for item in self.fields_tree.get_children():
            self.fields_tree.delete(item)

        # 清除原始结果文本
        self.raw_text.delete(1.0, tk.END)

        # 清除AI结果文本
        if hasattr(self, 'ai_text'):
            self.ai_text.delete(1.0, tk.END)

        # 重置状态
        self.progress_var.set("🔄 就绪")
        self.method_var.set("待识别")

  
    def start_ocr_service(self):
        """启动OCR服务"""
        import subprocess
        import os
        import sys

        try:
            # 导入OCR服务检测器
            try:
                from ocr_service_detector import ocr_detector

                # 首先检查OCR服务是否已经运行
                if ocr_detector.is_ocr_service_running():
                    self.logger.info("OCR服务已在运行中")
                    self.ocr_status_var.set("✅ OCR服务已连接")
                    self.start_ocr_btn.pack_forget()  # 隐藏启动按钮
                    return

                # 使用快速检测获取最佳服务
                service = ocr_detector.get_best_service_fast()

                if not service:
                    # 如果快速检测失败，使用完整检测
                    service = ocr_detector.get_best_service(quick_mode=True)

                if service:
                    ocr_service_path, service_type = service

                    # 检查进程是否已经运行
                    exe_file = os.path.join(ocr_service_path, "Umi-OCR.exe")
                    if ocr_detector.is_process_running(exe_file):
                        self.logger.info(f"OCR服务进程已在运行: {ocr_service_path}")
                        # 等待服务启动完成
                        import time
                        for i in range(10):  # 最多等待10秒
                            if ocr_detector.is_ocr_service_running():
                                self.ocr_status_var.set("✅ OCR服务已连接")
                                self.start_ocr_btn.pack_forget()
                                return
                            time.sleep(1)

                    self.logger.info(f"自动检测到OCR服务: {ocr_service_path} ({service_type})")
                else:
                    # 如果自动检测失败，尝试使用常见路径
                    common_paths = [
                        r"D:\software\个性化工具\umi-ocr\Umi-OCR_Rapid_v2.1.5",
                        r"D:\software\umi-ocr",
                        r"C:\Program Files\umi-ocr",
                        r"C:\Program Files (x86)\umi-ocr"
                    ]

                    ocr_service_path = None
                    for path in common_paths:
                        if os.path.exists(path):
                            # 检查子目录
                            for item in os.listdir(path):
                                item_path = os.path.join(path, item)
                                if os.path.isdir(item_path):
                                    exe_file = os.path.join(item_path, "Umi-OCR.exe")
                                    main_script = os.path.join(item_path, "main.py")
                                    if os.path.exists(exe_file) or os.path.exists(main_script):
                                        ocr_service_path = item_path
                                        break
                            if ocr_service_path:
                                break

                    if not ocr_service_path:
                        self._show_ocr_not_found_dialog()
                        return
            except ImportError:
                # 如果检测器模块不可用，使用默认路径
                ocr_service_path = r"D:\software\个性化工具\umi-ocr\Umi-OCR_Rapid_v2.1.5"

            # 检查OCR服务路径是否存在
            if not os.path.exists(ocr_service_path):
                self._show_ocr_not_found_dialog()
                return

            # 查找可执行文件
            main_script = os.path.join(ocr_service_path, "main.py")
            exe_file = os.path.join(ocr_service_path, "Umi-OCR.exe")

            service_command = None
            service_type = None

            if os.path.exists(exe_file):
                service_command = [exe_file]
                service_type = "可执行文件"
            elif os.path.exists(main_script):
                service_command = [sys.executable, main_script]
                service_type = "Python脚本"
            else:
                messagebox.showerror("错误", f"在OCR服务目录中未找到可执行文件:\n"
                                     f"- 尝试查找: Umi-OCR.exe\n"
                                     f"- 尝试查找: main.py\n\n"
                                     f"目录: {ocr_service_path}\n\n"
                                     f"请检查umi-OCR安装是否完整。")
                return

            self.logger.info(f"找到{service_type}: {service_command[0]}")

            # 更新状态
            self.ocr_status_var.set("🚀 正在启动OCR服务...")
            self.start_ocr_btn.config(state="disabled", text="启动中...")

            def start_service():
                try:
                    # 启动OCR服务
                    self.logger.info(f"正在启动OCR服务: {service_command[0]}")

                    # 简化启动逻辑，避免平台特定的问题
                    try:
                        if sys.platform == "win32":
                            # Windows系统：尝试在新窗口启动
                            creation_flags = subprocess.CREATE_NEW_CONSOLE
                            process = subprocess.Popen(
                                service_command,
                                cwd=ocr_service_path,
                                creationflags=creation_flags
                            )
                        else:
                            # 非Windows系统
                            process = subprocess.Popen(
                                service_command,
                                cwd=ocr_service_path
                            )

                        self.logger.info(f"OCR服务进程已启动，PID: {process.pid}")

                    except Exception as subprocess_error:
                        raise Exception(f"启动服务进程失败: {subprocess_error}")
                        import traceback
                        traceback.print_exc()

                    # 等待一会儿让服务启动
                    import time
                    time.sleep(3)

                    # 测试连接
                    if self.ocr_tool.test_ocr_connection():
                        self.root.after(0, lambda: self.ocr_status_var.set("✅ OCR服务启动成功"))
                        self.root.after(0, lambda: self.start_ocr_btn.grid_forget())
                        self.root.after(0, lambda: messagebox.showinfo("成功", "OCR服务启动成功！"))
                    else:
                        self.root.after(0, lambda: self.ocr_status_var.set("⚠️ OCR服务启动但连接失败"))
                        self.root.after(0, lambda: self.start_ocr_btn.config(state="normal", text="🚀 重新启动"))
                        self.root.after(0, lambda: messagebox.showwarning("警告", "OCR服务已启动但连接失败，请检查端口1224是否被占用。"))

                except Exception as e:
                    error_msg = f"启动OCR服务失败: {str(e)}"
                    self.root.after(0, lambda: self.ocr_status_var.set("❌ 启动失败"))
                    self.root.after(0, lambda: self.start_ocr_btn.config(state="normal", text="🚀 重试"))
                    self.root.after(0, lambda: messagebox.showerror("启动失败", error_msg))

            # 在后台线程中启动服务
            threading.Thread(target=start_service, daemon=True).start()

        except Exception as e:
            messagebox.showerror("错误", f"准备启动OCR服务时出错: {str(e)}")
            self.start_ocr_btn.config(state="normal", text="🚀 启动OCR服务")

    def _show_ocr_not_found_dialog(self):
        """显示OCR服务未找到的对话框"""
        from tkinter import messagebox, filedialog, simpledialog

        # 创建自定义对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("OCR服务未找到")
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # 标题
        title_label = ttk.Label(dialog, text="🔍 未找到OCR服务",
                               font=('Microsoft YaHei UI', 12, 'bold'))
        title_label.pack(pady=(20, 10))

        # 说明文本
        info_text = """程序在系统中未找到umi-OCR服务安装。

您可以：
1. 📁 手动指定OCR服务路径
2. 🔍 自动搜索系统中的OCR服务
3. 📥 下载并安装umi-OCR服务
4. 🚫 取消启动（手动启动OCR服务）"""

        info_label = ttk.Label(dialog, text=info_text, justify=tk.LEFT)
        info_label.pack(padx=20, pady=10)

        # 结果显示区域
        result_frame = ttk.LabelFrame(dialog, text="搜索结果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 结果文本框
        result_text = tk.Text(result_frame, height=8, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=result_text.yview)
        result_text.configure(yscrollcommand=scrollbar.set)

        result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 按钮区域
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        def auto_search():
            """自动搜索OCR服务"""
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, "🔍 正在快速搜索系统中的OCR服务...\n\n")
            dialog.update()

            try:
                from ocr_service_detector import ocr_detector

                # 首先使用快速搜索
                services = ocr_detector.find_ocr_services(quick_mode=True)

                if services:
                    result_text.insert(tk.END, f"✅ 快速搜索找到 {len(services)} 个OCR服务：\n\n")
                    for i, (path, service_type) in enumerate(services, 1):
                        result_text.insert(tk.END, f"{i}. {path}\n")
                        result_text.insert(tk.END, f"   类型: {service_type}\n\n")
                else:
                    # 如果快速搜索没找到，进行完整搜索
                    result_text.insert(tk.END, "⏳ 正在进行完整搜索（可能需要较长时间）...\n\n")
                    dialog.update()

                    services = ocr_detector.find_ocr_services(quick_mode=False)

                    if services:
                        result_text.insert(tk.END, f"✅ 完整搜索找到 {len(services)} 个OCR服务：\n\n")
                        for i, (path, service_type) in enumerate(services, 1):
                            result_text.insert(tk.END, f"{i}. {path}\n")
                            result_text.insert(tk.END, f"   类型: {service_type}\n\n")
                    else:
                        result_text.insert(tk.END, "❌ 未找到OCR服务\n\n")
                        result_text.insert(tk.END, "💡 建议：\n")
                        result_text.insert(tk.END, "1. 确认已安装umi-OCR\n")
                        result_text.insert(tk.END, "2. 尝试手动指定安装路径\n")
                        result_text.insert(tk.END, "3. 从官网下载安装：https://github.com/hiroi-sora/Umi-OCR\n")

            except Exception as e:
                result_text.insert(tk.END, f"❌ 搜索失败: {str(e)}\n")

        def manual_select():
            """手动选择OCR服务路径"""
            path = filedialog.askdirectory(
                title="请选择umi-OCR服务安装目录",
                initialdir="C:\\"
            )
            if path:
                # 检查路径是否有效
                exe_file = os.path.join(path, "Umi-OCR.exe")
                main_script = os.path.join(path, "main.py")

                if os.path.exists(exe_file) or os.path.exists(main_script):
                    result_text.delete(1.0, tk.END)
                    result_text.insert(tk.END, f"✅ 已选择OCR服务路径：\n{path}\n\n")
                    result_text.insert(tk.END, "正在启动服务...\n")

                    # 保存路径并启动服务
                    try:
                        from ocr_service_detector import ocr_detector
                        ocr_detector.save_path(path)
                        dialog.destroy()
                        # 使用选择的路径启动服务
                        self._start_ocr_service_with_path(path)
                    except Exception as e:
                        result_text.insert(tk.END, f"❌ 保存路径失败: {str(e)}\n")
                else:
                    messagebox.showerror("错误",
                        f"在选择的目录中未找到OCR服务文件：\n\n"
                        f"目录: {path}\n\n"
                        f"请确认目录包含 Umi-OCR.exe 或 main.py 文件")

        def download_ocr():
            """打开下载页面"""
            import webbrowser
            webbrowser.open("https://github.com/hiroi-sora/Umi-OCR/releases")

        # 按钮
        auto_btn = ttk.Button(button_frame, text="🔍 自动搜索", command=auto_search)
        auto_btn.pack(side=tk.LEFT, padx=(0, 10))

        manual_btn = ttk.Button(button_frame, text="📁 手动选择", command=manual_select)
        manual_btn.pack(side=tk.LEFT, padx=(0, 10))

        download_btn = ttk.Button(button_frame, text="📥 下载OCR", command=download_ocr)
        download_btn.pack(side=tk.LEFT, padx=(0, 10))

        cancel_btn = ttk.Button(button_frame, text="🚫 取消", command=dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT)

        # 默认执行自动搜索
        dialog.after(100, auto_search)

    def _start_ocr_service_with_path(self, ocr_service_path: str):
        """使用指定路径启动OCR服务"""
        import subprocess
        import os
        import sys

        try:
            # 查找可执行文件
            main_script = os.path.join(ocr_service_path, "main.py")
            exe_file = os.path.join(ocr_service_path, "Umi-OCR.exe")

            service_command = None
            service_type = None

            if os.path.exists(exe_file):
                service_command = [exe_file]
                service_type = "可执行文件"
            elif os.path.exists(main_script):
                service_command = [sys.executable, main_script]
                service_type = "Python脚本"
            else:
                messagebox.showerror("错误", f"在OCR服务目录中未找到可执行文件:\n"
                                     f"- 尝试查找: Umi-OCR.exe\n"
                                     f"- 尝试查找: main.py\n\n"
                                     f"目录: {ocr_service_path}\n\n"
                                     f"请检查umi-OCR安装是否完整。")
                return

            self.logger.info(f"找到{service_type}: {service_command[0]}")

            # 更新状态
            self.ocr_status_var.set("🚀 正在启动OCR服务...")
            self.start_ocr_btn.config(state="disabled", text="启动中...")

            def start_service():
                """在后台线程中启动服务"""
                try:
                    # 启动服务
                    if sys.platform == "win32":
                        # Windows平台
                        if hasattr(subprocess, 'CREATE_NEW_CONSOLE'):
                            creation_flags = subprocess.CREATE_NEW_CONSOLE
                        else:
                            creation_flags = 0

                        process = subprocess.Popen(
                            service_command,
                            cwd=ocr_service_path,
                            creationflags=creation_flags
                        )
                    else:
                        # 非Windows平台
                        process = subprocess.Popen(
                            service_command,
                            cwd=ocr_service_path
                        )

                    # 等待一段时间检查服务是否启动成功
                    import time
                    time.sleep(3)

                    # 在主线程中更新UI
                    self.root.after(0, lambda: self._check_ocr_service_after_start())

                except Exception as e:
                    # 在主线程中显示错误
                    self.root.after(0, lambda: self._show_ocr_start_error(str(e)))

            # 在后台线程中启动服务
            threading.Thread(target=start_service, daemon=True).start()

        except Exception as e:
            messagebox.showerror("错误", f"准备启动OCR服务时出错: {str(e)}")
            self.start_ocr_btn.config(state="normal", text="🚀 启动OCR服务")

    def load_fields_list(self):
        """加载并显示当前字段配置列表"""
        # 清空现有显示
        for item in self.fields_tree.get_children():
            self.fields_tree.delete(item)

        try:
            if FIELD_CONFIG_AVAILABLE:
                # 从字段配置管理器获取字段
                fields = field_config_manager.get_all_fields()

                if fields:
                    for field_name, field_def in fields.items():
                        status = "必需" if field_def.required else "可选"
                        tags = ('required',) if field_def.required else ('optional',)

                        self.fields_tree.insert('', 'end', values=(
                            field_name,
                            f"类型: {field_def.field_type} | {field_def.description[:50]}...",
                            status
                        ), tags=tags)
                else:
                    # 如果没有字段配置，显示默认提示
                    self.fields_tree.insert('', 'end', values=(
                        "暂无字段配置", "请使用字段配置管理器添加字段", "⚠️"
                    ), tags=('warning',))
            else:
                # 如果字段配置不可用，显示默认字段
                default_fields = [
                    "项目名称", "设计人", "审核人",
                    "审定人", "图纸编号", "出图日期"
                ]

                for field_name in default_fields:
                    self.fields_tree.insert('', 'end', values=(
                        field_name, "默认字段", "✅"
                    ), tags=('optional',))

        except Exception as e:
            self.logger.error(f"加载字段列表失败: {e}")
            self.fields_tree.insert('', 'end', values=(
                "加载失败", f"错误: {str(e)}", "❌"
            ), tags=('error',))

    def refresh_fields_display(self):
        """刷新字段显示（从字段配置管理器重新加载）"""
        self.load_fields_list()
        self.progress_var.set("✅ 字段列表已刷新")

    def export_results(self):
        """导出识别结果为Excel文件"""
        if not self.current_result:
            messagebox.showwarning("警告", "没有可导出的结果")
            return

        # 直接询问保存位置并导出为Excel
        file_path = filedialog.asksaveasfilename(
            title="保存Excel结果",
            filetypes=[
                ("Excel文件", "*.xlsx"),
                ("所有文件", "*.*")
            ],
            defaultextension=".xlsx",
            initialfile=f"图纸图签识别结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

        if not file_path:
            return

        try:
            # 准备Excel数据
            excel_data = {
                '图片路径': self.current_image_path or '',
                '处理时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '解析方式': self.method_var.get(),
                'AI置信度': self.ai_confidence,
                '提取字段': self.current_result.get('提取字段', {})
            }

            # 使用Excel导出器导出
            if not self.excel_exporter.export_single_invoice(file_path, excel_data, "horizontal"):
                raise ValueError("Excel文件导出失败")

            messagebox.showinfo("成功", f"结果已成功导出到:\n{file_path}")
            self.progress_var.set("✅ Excel导出完成")

        except Exception as e:
            messagebox.showerror("错误", f"Excel导出失败:\n{str(e)}")
            self.progress_var.set("❌ Excel导出失败")

    def save_results_to_file(self, file_path, format_type):
        """保存结果到文件"""
        if not self.current_result:
            return

        # 收集字段数据
        fields_data = self.current_result.get('提取字段', {})

        if format_type == "json":
            # 完整结果数据
            result_data = {
                '图片路径': self.current_image_path or '',
                '处理时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '解析方式': self.method_var.get(),
                'AI置信度': self.ai_confidence,
                '提取字段': fields_data,
                'OCR原始结果': self.current_result.get('OCR原始结果')
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)

        elif format_type == "txt":
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("=== 图纸图签识别结果 ===\n\n")
                f.write(f"图片路径: {self.current_image_path or 'N/A'}\n")
                f.write(f"处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"解析方式: {self.method_var.get()}\n")
                if self.ai_confidence:
                    f.write(f"AI置信度: {self.ai_confidence:.1%}\n")
                f.write(f"\n提取字段:\n")
                f.write("-" * 50 + "\n")
                for field, value in fields_data.items():
                    f.write(f"{field}: {value or '未识别'}\n")

        elif format_type == "csv":
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['字段名称', '提取内容', '识别状态'])
                for field, value in fields_data.items():
                    status = '成功' if value else '未识别'
                    writer.writerow([field, value or '', status])

        elif format_type == "xlsx":
            if not self.excel_enabled:
                raise ValueError("Excel导出功能不可用，请确保安装了openpyxl库")

            # 准备Excel数据
            excel_data = {
                '图片路径': self.current_image_path or '',
                '处理时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '解析方式': self.method_var.get(),
                'AI置信度': self.ai_confidence,
                '提取字段': fields_data
            }

            # 默认使用横向格式导出
            if not self.excel_exporter.export_single_invoice(file_path, excel_data, "horizontal"):
                raise ValueError("Excel文件导出失败")

    def batch_process(self):
        """批量处理功能"""
        # 选择批量处理的文件目录
        directory = filedialog.askdirectory(title="选择包含图纸图片和PDF的目录")

        if not directory:
            return

        # 创建批量处理窗口
        batch_window = tk.Toplevel(self.root)
        batch_window.title("批量处理 - AI增强版")
        batch_window.geometry("700x600")
        batch_window.transient(self.root)
        batch_window.grab_set()

        # 获取目录中的图片和PDF文件
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        supported_files = [
            f for f in os.listdir(directory)
            if any(f.lower().endswith(ext) for ext in image_extensions + ['.pdf'])
        ]

        if not supported_files:
            messagebox.showwarning("警告", "目录中没有找到支持的图片或PDF文件")
            batch_window.destroy()
            return

        # 创建进度显示
        ttk.Label(batch_window, text=f"找到 {len(supported_files)} 个文件",
                 font=('微软雅黑', 12, 'bold')).pack(pady=10)

        progress_var = tk.StringVar(value="准备开始批量处理...")
        ttk.Label(batch_window, textvariable=progress_var).pack(pady=5)

        progress_bar = ttk.Progressbar(batch_window, mode='determinate',
                                      maximum=len(supported_files))
        progress_bar.pack(pady=10, padx=20, fill='x')

        # 结果列表
        result_frame = ttk.Frame(batch_window)
        result_frame.pack(fill='both', expand=True, padx=10, pady=10)
        result_frame.columnconfigure(0, weight=1)

        columns = ('文件名', '类型', '状态', '解析方式', '识别字段数', '置信度')
        result_tree = ttk.Treeview(result_frame, columns=columns, show='headings', height=15)
        result_tree.heading('文件名', text='文件名')
        result_tree.heading('类型', text='类型')
        result_tree.heading('状态', text='状态')
        result_tree.heading('解析方式', text='解析方式')
        result_tree.heading('识别字段数', text='识别字段数')
        result_tree.heading('置信度', text='置信度')
        result_tree.column('文件名', width=180)
        result_tree.column('类型', width=60)
        result_tree.column('状态', width=80)
        result_tree.column('解析方式', width=100)
        result_tree.column('识别字段数', width=100)
        result_tree.column('置信度', width=80)

        result_scrollbar = ttk.Scrollbar(result_frame, orient='vertical', command=result_tree.yview)
        result_tree.configure(yscrollcommand=result_scrollbar.set)

        result_tree.pack(side='left', fill='both', expand=True)
        result_scrollbar.pack(side='right', fill='y')

        results_data = []

        def process_batch():
            for i, filename in enumerate(supported_files):
                try:
                    # 更新进度
                    file_type = "PDF" if filename.lower().endswith('.pdf') else "图片"
                    progress_var.set(f"正在处理: {filename} ({i+1}/{len(supported_files)}) - {file_type}")
                    progress_bar['value'] = i + 1
                    batch_window.update()

                    # 处理文件
                    file_path = os.path.join(directory, filename)
                    result = self.ocr_tool.process_invoice(file_path)

                    # 提取信息
                    if result and result.get('提取字段'):
                        fields = result.get('提取字段', {})
                        field_count = len([v for v in fields.values() if v])
                        status = "成功"
                        parsing_method = getattr(result, 'parsing_method', '未知')
                        confidence = getattr(result, 'ai_confidence', 0)

                        # 更新结果列表
                        batch_window.after(0, lambda f=filename, t=file_type, s=status,
                                      p=parsing_method, c=field_count, conf=confidence:
                                      result_tree.insert('', 'end',
                                      values=(f, t, s, p, f"{c}/6", f"{conf:.1%}" if conf else "")))

                        results_data.append({
                            'filename': filename,
                            'type': file_type,
                            'status': status,
                            'parsing_method': parsing_method,
                            'field_count': field_count,
                            'confidence': confidence,
                            'result': result,
                            'file_path': file_path
                        })
                    else:
                        status = "失败"
                        parsing_method = "未知"
                        batch_window.after(0, lambda f=filename, t=file_type:
                                      result_tree.insert('', 'end',
                                      values=(f, t, status, parsing_method, "0/6", "")))

                except Exception as e:
                    error_status = f"错误: {str(e)[:20]}"
                    batch_window.after(0, lambda f=filename, t=file_type if 'filename' in locals() else '未知':
                                      result_tree.insert('', 'end',
                                      values=(f, t or '未知', error_status, "未知", "0/6", "")))

            # 处理完成
            success_count = len([r for r in results_data if r['status'] == '成功'])
            ai_count = len([r for r in results_data if 'AI' in r['parsing_method']])

            batch_window.after(0, lambda: progress_var.set(
                f"✅ 批量处理完成！成功: {success_count}/{len(supported_files)} "
                f"(AI识别: {ai_count})"
            ))
            batch_window.after(0, lambda: progress_bar['value'], len(supported_files))

        def export_batch():
            if not results_data:
                messagebox.showwarning("警告", "没有可导出的结果")
                return

            file_path = filedialog.asksaveasfilename(
                title="保存批量结果",
                filetypes=[
                    ("Excel文件", "*.xlsx"),
                    ("JSON文件", "*.json"),
                    ("CSV文件", "*.csv")
                ],
                defaultextension=".xlsx"
            )

            if file_path:
                try:
                    if file_path.endswith('.xlsx') and self.excel_enabled:
                        # 使用Excel导出器导出批量结果
                        excel_data = []
                        for item in results_data:
                            if item['result']:
                                fields = item['result'].get('提取字段', {})
                                excel_data.append({
                                    '图片路径': item['file_path'],
                                    '处理时间': item['result'].get('处理时间', ''),
                                    '解析方式': item['parsing_method'],
                                    'AI置信度': item['confidence'],
                                    '提取字段': fields
                                })

                        if self.excel_exporter.export_batch_invoices(file_path, excel_data):
                            messagebox.showinfo("成功", f"批量结果已保存到: {file_path}")
                        else:
                            messagebox.showerror("错误", "Excel导出失败")
                    else:
                        # JSON或CSV格式
                        batch_result = {
                            '处理时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            '总数': len(supported_files),
                            '成功数量': success_count,
                            'AI识别数量': ai_count,
                            '结果': results_data
                        }

                        with open(file_path, 'w', encoding='utf-8') as f:
                            if file_path.endswith('.json'):
                                json.dump(batch_result, f, ensure_ascii=False, indent=2)
                            else:  # CSV
                                import csv
                                writer = csv.writer(f)
                                writer.writerow(['文件名', '类型', '状态', '解析方式', '识别字段数', '置信度'])
                                for item in results_data:
                                    writer.writerow([
                                        item['filename'], item['type'], item['status'],
                                        item['parsing_method'], f"{item['field_count']}/6",
                                        f"{item['confidence']:.1%}" if item['confidence'] else ""
                                    ])

                        messagebox.showinfo("成功", f"批量结果已保存到: {file_path}")

                except Exception as e:
                    messagebox.showerror("错误", f"保存失败: {str(e)}")

        # 添加按钮
        button_frame = ttk.Frame(batch_window)
        button_frame.pack(pady=10)

        def start_batch():
            threading.Thread(target=process_batch, daemon=True).start()

        ttk.Button(button_frame, text="开始批量处理", command=start_batch).pack(side='left', padx=5)
        ttk.Button(button_frame, text="导出结果", command=export_batch).pack(side='left', padx=5)
        ttk.Button(button_frame, text="关闭", command=batch_window.destroy).pack(side='left', padx=5)

    def _check_ocr_service_after_start(self):
        """检查OCR服务启动后的状态"""
        try:
            import requests
            response = requests.get("http://127.0.0.1:1224", timeout=5)
            if response.status_code == 200:
                self.ocr_status_var.set("✅ OCR服务已连接")
                self.start_ocr_btn.pack_forget()  # 隐藏启动按钮
                self.show_success("OCR服务启动成功！")
                self.logger.info("OCR服务启动并连接成功")
            else:
                self.ocr_status_var.set("❌ OCR服务连接失败")
                self.start_ocr_btn.config(state="normal", text="🚀 重试启动OCR服务")
                self.show_error("OCR服务启动失败，请检查服务是否正常运行")
        except Exception as e:
            self.ocr_status_var.set("❌ OCR服务连接失败")
            self.start_ocr_btn.config(state="normal", text="🚀 重试启动OCR服务")
            self.show_error(f"OCR服务启动失败: {str(e)}")

    def _show_ocr_start_error(self, error_msg):
        """显示OCR启动错误"""
        self.ocr_status_var.set("❌ OCR服务启动失败")
        self.start_ocr_btn.config(state="normal", text="🚀 重试启动OCR服务")
        self.show_error(f"启动OCR服务时出错: {error_msg}")
        self.logger.error(f"OCR服务启动失败: {error_msg}")

    def run(self):
        """运行GUI应用"""
        # 居中显示窗口
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

        # 运行主循环
        self.root.mainloop()


def main():
    """主函数"""
    try:
        # 检查PIL库是否安装
        from PIL import Image, ImageTk
    except ImportError:
        messagebox.showerror("依赖缺失", "需要安装Pillow库\n请运行: pip install Pillow")
        return

    app = InvoiceOCRGUI()
    app.run()


if __name__ == "__main__":
    main()