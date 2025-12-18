#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用OCR识别工具 - GUI增强版本（优化修复版）
支持发票识别和图纸图签提取两种模式
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

# OCR工具导入
try:
    from invoice_ocr_tool import InvoiceOCRTool
    from drawing_ocr_tool import DrawingOCRTool
    from excel_exporter import ExcelExporter
    OCR_TOOLS_AVAILABLE = True
except ImportError as e:
    OCR_TOOLS_AVAILABLE = False
    logging.warning(f"OCR工具导入失败: {e}")

# 导入字段配置管理器
try:
    from field_config import field_config_manager
    FIELD_CONFIG_AVAILABLE = True
except ImportError:
    FIELD_CONFIG_AVAILABLE = False


class UniversalOCRGUI:
    """通用OCR识别工具GUI界面 - 支持发票和图纸两种模式"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("智能OCR识别工具 - 老王特供")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)

        # 设置日志记录器
        self.logger = logging.getLogger(f"{__name__}.UniversalOCRGUI")

        # 确保logger已经配置
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        # 设置窗口图标和样式
        self.setup_styles()

        # 当前OCR模式：'invoice' 或 'drawing'
        self.ocr_mode = tk.StringVar(value='invoice')

        # 初始化OCR工具
        self.ocr_tool = None
        self.init_ocr_tool()

        # 初始化Excel导出器
        try:
            self.excel_exporter = ExcelExporter()
        except Exception as e:
            self.excel_exporter = None
            self.logger.warning(f"Excel导出功能不可用: {e}")

        # 存储识别结果
        self.current_results = []

        # 存储文件路径
        self.file_paths = []

        # 预览相关变量
        self.preview_images = {}  # 存储预览图片
        self.processing_info = {}  # 存储处理信息
        self.preview_current_file = None  # 当前预览文件
        self.preview_mode = 'normal'  # 'normal' or 'signature'

        # 图片优化器（用于图签检测）
        self.image_optimizer = None
        try:
            from image_optimizer import ImageOptimizer
            self.image_optimizer = ImageOptimizer()
        except ImportError:
            self.logger.warning("图签检测功能不可用")

        # 创建GUI组件
        self.create_widgets()

        # 绑定事件
        self.setup_events()

        self.logger.info("OCR GUI初始化完成")

    def setup_styles(self):
        """设置窗口样式和主题"""
        try:
            # 设置ttk主题
            style = ttk.Style()
            style.theme_use('clam')

            # 配置样式
            style.configure('Title.TLabel', font=('Microsoft YaHei', 12, 'bold'))
            style.configure('Header.TLabel', font=('Microsoft YaHei', 10, 'bold'))
            style.configure('Success.TLabel', foreground='green')
            style.configure('Error.TLabel', foreground='red')
            style.configure('Warning.TLabel', foreground='orange')

        except Exception as e:
            self.logger.warning(f"样式设置失败: {e}")

    def init_ocr_tool(self):
        """根据当前模式初始化OCR工具"""
        if not OCR_TOOLS_AVAILABLE:
            messagebox.showerror("初始化错误", "OCR工具模块不可用，请检查依赖")
            return

        try:
            mode = self.ocr_mode.get()
            if mode == 'drawing':
                self.ocr_tool = DrawingOCRTool()
                self.logger.info("✅ 图纸OCR工具初始化成功")
            else:  # invoice
                self.ocr_tool = InvoiceOCRTool(use_ai=True)
                self.logger.info("✅ 发票OCR工具初始化成功")
        except Exception as e:
            error_msg = f"OCR工具初始化失败:\n{str(e)}"
            messagebox.showerror("初始化错误", error_msg)
            self.logger.error(error_msg)

    def create_widgets(self):
        """创建GUI组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 顶部控制面板
        self.create_control_panel(main_frame)

        # 中间内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # 左侧文件处理区
        self.create_file_panel(content_frame)

        # 右侧结果显示区
        self.create_result_panel(content_frame)

    def create_control_panel(self, parent):
        """创建顶部控制面板"""
        control_frame = ttk.LabelFrame(parent, text="控制面板", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # 第一行：模式选择和文件操作
        row1_frame = ttk.Frame(control_frame)
        row1_frame.pack(fill=tk.X, pady=(0, 10))

        # OCR模式选择
        ttk.Label(row1_frame, text="识别模式:", style='Header.TLabel').pack(side=tk.LEFT, padx=(0, 10))

        mode_frame = ttk.Frame(row1_frame)
        mode_frame.pack(side=tk.LEFT, padx=(0, 20))

        ttk.Radiobutton(mode_frame, text="🧾 发票识别", variable=self.ocr_mode,
                       value='invoice', command=self.on_mode_change).pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="📐 图纸图签", variable=self.ocr_mode,
                       value='drawing', command=self.on_mode_change).pack(side=tk.LEFT, padx=(10, 0))

        # 分隔线
        ttk.Separator(row1_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # 文件操作按钮
        ttk.Button(row1_frame, text="📁 选择文件",
                  command=self.select_files).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(row1_frame, text="📁 选择文件夹",
                  command=self.select_folder).pack(side=tk.LEFT, padx=(0, 10))

        # 处理按钮
        self.process_btn = ttk.Button(row1_frame, text="🚀 开始识别",
                                    command=self.start_processing)
        self.process_btn.pack(side=tk.LEFT, padx=(10, 0))

        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(row1_frame, variable=self.progress_var,
                                          mode='indeterminate', length=200)
        self.progress_bar.pack(side=tk.RIGHT, padx=(10, 0))

        # 状态标签
        self.status_label = ttk.Label(row1_frame, text="就绪", style='Success.TLabel')
        self.status_label.pack(side=tk.RIGHT, padx=(10, 0))

        # 第二行：导出操作
        row2_frame = ttk.Frame(control_frame)
        row2_frame.pack(fill=tk.X)

        # 导出按钮
        ttk.Button(row2_frame, text="📊 导出Excel",
                  command=self.export_results).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(row2_frame, text="🗑️ 清空结果",
                  command=self.clear_results).pack(side=tk.LEFT, padx=(0, 10))

        # 统计信息标签
        self.stats_label = ttk.Label(row2_frame, text="未处理文件")
        self.stats_label.pack(side=tk.RIGHT)

    def create_file_panel(self, parent):
        """创建左侧文件处理面板"""
        file_frame = ttk.LabelFrame(parent, text="文件列表", padding="10")
        file_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # 文件列表 - 添加OCR和AI信息列
        columns = ('文件名', '大小', '状态', 'OCR状态', 'AI置信度', '完整路径')
        self.file_tree = ttk.Treeview(file_frame, columns=columns, show='tree headings', height=15)

        # 设置列
        self.file_tree.heading('#0', text='序号')
        self.file_tree.heading('文件名', text='文件名')
        self.file_tree.heading('大小', text='大小')
        self.file_tree.heading('状态', text='状态')
        self.file_tree.heading('OCR状态', text='OCR状态')
        self.file_tree.heading('AI置信度', text='AI置信度')
        self.file_tree.heading('完整路径', text='完整路径')  # 隐藏列

        self.file_tree.column('#0', width=40)
        self.file_tree.column('文件名', width=180)
        self.file_tree.column('大小', width=70)
        self.file_tree.column('状态', width=80)
        self.file_tree.column('OCR状态', width=80)
        self.file_tree.column('AI置信度', width=80)
        self.file_tree.column('完整路径', width=0)  # 隐藏列，宽度为0

        # 隐藏最后一列（完整路径列）
        self.file_tree.column('完整路径', width=0, stretch=False)
        self.file_tree.heading('完整路径', anchor='w')

        # 滚动条
        file_scrollbar = ttk.Scrollbar(file_frame, orient='vertical', command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=file_scrollbar.set)

        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        file_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_result_panel(self, parent):
        """创建右侧结果显示面板"""
        result_frame = ttk.LabelFrame(parent, text="识别结果", padding="10")
        result_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # 创建notebook用于多页显示
        self.result_notebook = ttk.Notebook(result_frame)
        self.result_notebook.pack(fill=tk.BOTH, expand=True)

        # 摘要页
        self.create_summary_tab()

        # 详细结果页
        self.create_detail_tab()

        # 图像预览页
        self.create_preview_tab()

    def create_summary_tab(self):
        """创建摘要标签页"""
        summary_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(summary_frame, text="📋 摘要")

        # 摘要文本框
        self.summary_text = scrolledtext.ScrolledText(summary_frame, wrap=tk.WORD,
                                                     font=('Microsoft YaHei', 9))
        self.summary_text.pack(fill=tk.BOTH, expand=True)

    def create_detail_tab(self):
        """创建详细结果标签页"""
        detail_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(detail_frame, text="📝 详细")

        # 详细结果文本框
        self.detail_text = scrolledtext.ScrolledText(detail_frame, wrap=tk.WORD,
                                                   font=('Microsoft YaHei', 9))
        self.detail_text.pack(fill=tk.BOTH, expand=True)

    def create_preview_tab(self):
        """创建图像预览标签页 - 增强版"""
        preview_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(preview_frame, text="🖼️ 实时预览")

        # 创建控制区域
        control_frame = ttk.Frame(preview_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(control_frame, text="双击文件列表中的项目可在右侧显示预览",
                 font=('Microsoft YaHei', 9)).pack(side=tk.LEFT)

        # 当前选中文件显示
        self.current_preview_label = ttk.Label(control_frame, text="未选择文件",
                                             font=('Microsoft YaHei', 9, 'bold'),
                                             foreground='gray')
        self.current_preview_label.pack(side=tk.LEFT, padx=20)

        # 预览工具按钮
        if self.ocr_mode.get() == 'drawing':
            ttk.Button(control_frame, text="🎯 检测图签",
                      command=self.show_signature_detection).pack(side=tk.RIGHT, padx=5)

        ttk.Button(control_frame, text="🔄 刷新预览",
                  command=self.refresh_preview).pack(side=tk.RIGHT, padx=5)

        # 预览区域
        preview_content = ttk.Frame(preview_frame)
        preview_content.pack(fill=tk.BOTH, expand=True, padx=5)

        # 预览画布
        self.preview_canvas = tk.Canvas(preview_content, bg='white', highlightthickness=1)

        # 预览滚动条
        v_scrollbar = ttk.Scrollbar(preview_content, orient='vertical', command=self.preview_canvas.yview)
        h_scrollbar = ttk.Scrollbar(preview_content, orient='horizontal', command=self.preview_canvas.xview)

        self.preview_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # 布局
        self.preview_canvas.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')

        preview_content.grid_rowconfigure(0, weight=1)
        preview_content.grid_columnconfigure(0, weight=1)

    def setup_events(self):
        """绑定事件处理"""
        # 文件双击事件
        self.file_tree.bind('<Double-1>', self.on_file_double_click)

        # 文件选择事件 - 更新预览
        self.file_tree.bind('<<TreeviewSelect>>', self.on_file_select)

        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_mode_change(self):
        """OCR模式改变时的处理"""
        mode = self.ocr_mode.get()
        mode_text = "发票识别" if mode == 'invoice' else "图纸图签提取"

        self.logger.info(f"切换到{mode_text}模式")
        self.clear_results()

        # 重新初始化OCR工具
        self.init_ocr_tool()

        # 更新窗口标题
        self.root.title(f"智能OCR识别工具 - {mode_text} - 老王特供")

        # 更新状态
        self.status_label.config(text=f"已切换到{mode_text}模式", style='Success.TLabel')

    def select_files(self):
        """选择要处理的文件"""
        mode = self.ocr_mode.get()
        mode_text = "发票" if mode == 'invoice' else "图纸"

        file_types = [
            ("图片文件", "*.png *.jpg *.jpeg *.bmp *.tiff"),
            ("PDF文件", "*.pdf"),
            ("所有文件", "*.*")
        ]

        files = filedialog.askopenfilenames(
            title=f"选择{mode_text}文件",
            filetypes=file_types
        )

        if files:
            self.add_files_to_list(files)

    def select_folder(self):
        """选择要处理的文件夹"""
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            # 支持的文件扩展名
            extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.pdf'}

            files = []
            for root, dirs, filenames in os.walk(folder):
                for filename in filenames:
                    if any(filename.lower().endswith(ext) for ext in extensions):
                        files.append(os.path.join(root, filename))

            if files:
                self.add_files_to_list(files)
            else:
                messagebox.showwarning("提示", "选择的文件夹中没有支持的文件")

    def add_files_to_list(self, files):
        """添加文件到列表"""
        # 清空现有项目
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        # 存储完整文件路径到实例变量
        self.file_paths = files

        # 添加新文件到界面
        for i, file_path in enumerate(files, 1):
            try:
                file_size = os.path.getsize(file_path)
                size_str = self.format_file_size(file_size)

                # 存储完整路径，但只显示文件名
                self.file_tree.insert('', 'end', iid=str(i), text=str(i),
                                   values=(os.path.basename(file_path), size_str, '待处理', '-', '-',
                                          file_path))  # 隐藏最后一列存储完整路径
            except Exception as e:
                self.logger.warning(f"无法获取文件信息: {file_path}, 错误: {e}")

        # 更新统计
        self.update_stats()

    def format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    def update_stats(self):
        """更新统计信息"""
        total_items = len(self.file_tree.get_children())
        processed_items = len([item for item in self.file_tree.get_children()
                             if self.file_tree.item(item)['values'][2] in ['已完成', '失败']])

        self.stats_label.config(text=f"总计: {total_items} | 已处理: {processed_items}")

    def start_processing(self):
        """开始处理文件"""
        if not self.ocr_tool:
            messagebox.showerror("错误", "OCR工具未初始化")
            return

        files = self._get_file_paths_from_tree()

        if not files:
            messagebox.showwarning("提示", "请先选择要处理的文件")
            return

        # 禁用处理按钮
        self.process_btn.config(state='disabled')
        self.progress_bar.start(10)
        self.status_label.config(text="处理中...", style='Warning.TLabel')

        # 在新线程中处理
        thread = threading.Thread(target=self.process_files, args=(files,))
        thread.daemon = True
        thread.start()

    def _get_file_paths_from_tree(self):
        """从文件树中获取文件路径列表"""
        files = []
        for item in self.file_tree.get_children():
            values = self.file_tree.item(item)['values']
            if len(values) >= 6:
                # 从隐藏的第6列获取完整路径
                file_path = values[5]
                if file_path and file_path != '-' and os.path.exists(file_path):
                    files.append(file_path)
            else:
                # 兼容旧版本，从实例变量获取
                if hasattr(self, 'file_paths') and self.file_paths:
                    try:
                        item_index = int(item) - 1
                        if 0 <= item_index < len(self.file_paths):
                            file_path = self.file_paths[item_index]
                            if file_path and os.path.exists(file_path):
                                files.append(file_path)
                    except (ValueError, IndexError) as e:
                        self.logger.warning(f"无法解析文件索引: {item}, 错误: {e}")
        return files

    def process_files(self, files):
        """处理文件列表"""
        mode = self.ocr_mode.get()
        results = []

        try:
            for i, file_path in enumerate(files):
                try:
                    file_name = os.path.basename(file_path)

                    # 更新状态
                    self.root.after(0, lambda idx=i+1, name=file_name:
                                  self.update_file_status(idx, "处理中...", "", ""))

                    # 处理文件（使用完整路径）
                    result = self._process_single_file(file_path, mode)

                    # 确保结果不为None
                    if result is None:
                        result = {
                            '图片路径': file_path,
                            'OCR状态': '失败',
                            'AI状态': '失败',
                            'AI置信度': 0,
                            '提取字段': {},
                            '处理时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            '解析方式': '未知',
                            '错误信息': '处理返回None结果'
                        }

                    results.append(result)

                    # 提取OCR和AI信息（添加安全检查）
                    ocr_status = result.get('OCR状态', '未知') if result else '未知'
                    ai_confidence = result.get('AI置信度', 0) if result else 0
                    ai_confidence_str = f"{ai_confidence:.0%}" if ai_confidence > 0 else "-"

                    # 更新状态
                    status = "已完成" if ocr_status == '成功' else "失败"
                    self.root.after(0, lambda idx=i+1, s=status, ocr=ocr_status, ai=ai_confidence_str:
                                  self.update_file_status(idx, s, ocr, ai))

                    # 存储结果用于预览
                    self.processing_info[file_path] = result

                except Exception as e:
                    self.logger.error(f"处理文件失败: {file_path}, 错误: {e}")
                    # 创建失败结果对象
                    error_result = {
                        '图片路径': file_path,
                        'OCR状态': '失败',
                        'AI状态': '失败',
                        'AI置信度': 0,
                        '提取字段': {},
                        '处理时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        '解析方式': '未知',
                        '错误信息': str(e)
                    }
                    results.append(error_result)
                    self.processing_info[file_path] = error_result

                    self.root.after(0, lambda idx=i+1:
                                  self.update_file_status(idx, "失败"))

            # 更新结果
            self.current_results = results
            self.root.after(0, self.display_results)

        except Exception as e:
            self.logger.error(f"批量处理失败: {e}")
            self.root.after(0, lambda: messagebox.showerror("错误", f"处理失败:\n{str(e)}"))

        finally:
            # 恢复UI状态
            self.root.after(0, self.finish_processing)

    def _process_single_file(self, file_path, mode):
        """处理单个文件"""
        try:
            if mode == 'drawing':
                return self.ocr_tool.process_drawing(file_path)
            else:  # invoice
                return self.ocr_tool.process_invoice(file_path)
        except Exception as e:
            self.logger.error(f"文件处理异常: {file_path}, 错误: {e}")
            return None

    def update_file_status(self, item_id, status, ocr_status="", ai_confidence=""):
        """更新文件处理状态"""
        try:
            children = self.file_tree.get_children()
            if item_id <= len(children):
                item = children[item_id - 1]
                current_values = list(self.file_tree.item(item)['values'])

                # 确保有足够的列
                while len(current_values) < 6:
                    current_values.append('-')

                # 更新状态列
                current_values[2] = status

                # 更新OCR和AI状态（如果提供了）
                if ocr_status:
                    current_values[3] = ocr_status
                if ai_confidence:
                    current_values[4] = ai_confidence

                self.file_tree.item(item, values=current_values)
        except (IndexError, Exception) as e:
            self.logger.warning(f"更新文件状态失败: item_id={item_id}, 错误: {e}")

    def display_results(self):
        """显示处理结果"""
        if not self.current_results:
            return

        mode = self.ocr_mode.get()
        mode_text = "发票" if mode == 'invoice' else "图纸"

        # 显示摘要
        summary_text = f"🎯 {mode_text}识别结果摘要\n"
        summary_text += f"📅 处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        summary_text += f"📊 处理文件数: {len(self.current_results)}\n"
        summary_text += "=" * 50 + "\n\n"

        success_count = 0
        for i, result in enumerate(self.current_results, 1):
            if result and result.get('OCR状态') == '成功':
                success_count += 1

            file_path = result.get('图片路径', '未知') if result else '未知'
            summary_text += f"📄 文件 {i}: {os.path.basename(file_path)}\n"
            summary_text += f"   状态: {result.get('OCR状态', '未知') if result else '未知'}\n"
            summary_text += f"   AI置信度: {result.get('AI置信度', 0):.1% if result else 0:.1%}\n"
            summary_text += f"   提取字段数: {len(result.get('提取字段', {}) if result else {})}\n\n"

        summary_text += f"\n✅ 成功: {success_count} | ❌ 失败: {len(self.current_results) - success_count}"

        self.summary_text.delete('1.0', tk.END)
        self.summary_text.insert('1.0', summary_text)

        # 显示详细结果
        detail_text = ""
        for i, result in enumerate(self.current_results, 1):
            detail_text += f"{'='*60}\n"
            detail_text += f"📄 文件 {i}: {result.get('图片路径', '未知') if result else '未知'}\n"
            detail_text += f"⏰ 处理时间: {result.get('处理时间', '未知') if result else '未知'}\n"
            detail_text += f"🔍 解析方式: {result.get('解析方式', '未知') if result else '未知'}\n"
            detail_text += f"📊 OCR状态: {result.get('OCR状态', '未知') if result else '未知'}\n"
            detail_text += f"🤖 AI状态: {result.get('AI状态', '未知') if result else '未知'}\n\n"

            # 显示字段
            fields = result.get('提取字段', {}) if result else {}
            if fields:
                detail_text += "🎯 提取字段:\n"
                for field_name, field_value in fields.items():
                    status = "✅" if field_value else "❌"
                    detail_text += f"   {field_name}: {field_value or '未识别'} {status}\n"
            else:
                detail_text += "⚠️ 未提取到字段\n"

            # 显示错误信息（如果有）
            if result and result.get('错误信息'):
                detail_text += f"\n❌ 错误信息: {result['错误信息']}\n"

            detail_text += "\n"

        self.detail_text.delete('1.0', tk.END)
        self.detail_text.insert('1.0', detail_text)

        # 更新统计
        self.update_stats()

    def finish_processing(self):
        """完成处理，恢复UI状态"""
        self.process_btn.config(state='normal')
        self.progress_bar.stop()
        self.status_label.config(text="处理完成", style='Success.TLabel')

    def export_results(self):
        """导出识别结果"""
        if not self.current_results:
            messagebox.showwarning("提示", "没有可导出的结果")
            return

        if not self.excel_exporter:
            messagebox.showerror("错误", "Excel导出功能不可用")
            return

        mode = self.ocr_mode.get()
        mode_text = "发票" if mode == 'invoice' else "图纸"

        # 保存文件对话框
        file_path = filedialog.asksaveasfilename(
            title=f"保存{mode_text}识别结果",
            filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")],
            defaultextension=".xlsx",
            initialfile=f"{mode_text}识别结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

        if file_path:
            try:
                # 获取字段配置
                field_config = None
                if FIELD_CONFIG_AVAILABLE:
                    config_file = 'peizhi001.json' if mode == 'invoice' else 'tuqian001.json'
                    try:
                        field_config = field_config_manager.load_config(config_file)
                    except:
                        pass

                # 执行导出
                if mode == 'drawing' and len(self.current_results) == 1:
                    # 单个图纸导出
                    success = self.ocr_tool.export_drawing_result(self.current_results[0], file_path)
                else:
                    # 批量导出
                    success = self.excel_exporter.export_batch_invoices(
                        file_path, self.current_results, field_config
                    )

                if success:
                    messagebox.showinfo("成功", f"{mode_text}结果已导出到:\n{file_path}")
                    self.status_label.config(text="导出成功", style='Success.TLabel')
                else:
                    messagebox.showerror("错误", "导出失败")

            except Exception as e:
                messagebox.showerror("错误", f"导出失败:\n{str(e)}")

    def clear_results(self):
        """清空结果"""
        self.current_results = []
        self.file_paths = []

        # 清空文件列表
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        # 清空结果显示
        self.summary_text.delete('1.0', tk.END)
        self.detail_text.delete('1.0', tk.END)

        # 清空预览
        self.preview_canvas.delete("all")

        # 更新统计
        self.update_stats()
        self.stats_label.config(text="未处理文件")

        self.status_label.config(text="已清空", style='Success.TLabel')

    def on_file_double_click(self, event):
        """文件双击事件处理 - 显示图片预览"""
        selection = self.file_tree.selection()
        if selection:
            item = selection[0]
            values = self.file_tree.item(item)['values']
            file_name = values[0]

            # 获取完整路径
            file_path = self._get_file_path_from_item(item, values)

            if not file_path:
                messagebox.showinfo("文件信息", f"文件名: {file_name}\n路径信息不可用")
                return

            # 显示图片预览
            self.show_image_preview(file_path, file_name)

    def _get_file_path_from_item(self, item, values):
        """从文件树项目中获取文件路径"""
        # 尝试从隐藏列获取
        if len(values) >= 6:
            file_path = values[5]
            if file_path and file_path != '-' and os.path.exists(file_path):
                return file_path

        # 尝试从实例变量获取
        if hasattr(self, 'file_paths') and self.file_paths:
            try:
                item_index = int(item) - 1
                if 0 <= item_index < len(self.file_paths):
                    file_path = self.file_paths[item_index]
                    if file_path and os.path.exists(file_path):
                        return file_path
            except (ValueError, IndexError):
                pass

        return None

    def show_image_preview(self, file_path: str, file_name: str):
        """显示图片预览对话框"""
        preview_window = None
        try:
            from PIL import Image, ImageTk

            # 验证文件路径
            if not file_path or file_path == '-' or not os.path.exists(file_path):
                messagebox.showerror("错误", f"文件不存在或路径无效:\n{file_path}")
                return

            # 创建预览窗口
            preview_window = tk.Toplevel(self.root)
            preview_window.title(f"图片预览 - {file_name}")
            preview_window.geometry("900x700")
            preview_window.transient(self.root)

            # 创建标题
            title_frame = ttk.Frame(preview_window)
            title_frame.pack(fill=tk.X, padx=10, pady=5)
            ttk.Label(title_frame, text=f"📷 {file_name}",
                     font=('Microsoft YaHei', 12, 'bold')).pack(side=tk.LEFT)

            # 创建按钮框架
            button_frame = ttk.Frame(preview_window)
            button_frame.pack(fill=tk.X, padx=10, pady=5)

            # 如果是图纸模式，添加图签检测按钮
            if self.ocr_mode.get() == 'drawing':
                ttk.Button(button_frame, text="🎯 检测图签区域",
                          command=lambda: self.detect_signature_region_safe(file_path, preview_window)).pack(side=tk.LEFT, padx=5)

            # 关闭按钮
            ttk.Button(button_frame, text="关闭", command=preview_window.destroy).pack(side=tk.RIGHT, padx=5)

            # 创建信息显示区域
            info_frame = ttk.Frame(preview_window)
            info_frame.pack(fill=tk.X, padx=10, pady=5)

            info_text = tk.Text(info_frame, height=3, wrap=tk.WORD)
            info_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
            info_text.config(state=tk.DISABLED)

            # 创建滚动区域
            canvas_frame = ttk.Frame(preview_window)
            canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            canvas = tk.Canvas(canvas_frame, bg='white')
            v_scrollbar = ttk.Scrollbar(canvas_frame, orient='vertical', command=canvas.yview)
            h_scrollbar = ttk.Scrollbar(canvas_frame, orient='horizontal', command=canvas.xview)

            canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

            canvas.grid(row=0, column=0, sticky='nsew')
            v_scrollbar.grid(row=0, column=1, sticky='ns')
            h_scrollbar.grid(row=1, column=0, sticky='ew')

            canvas_frame.grid_rowconfigure(0, weight=1)
            canvas_frame.grid_columnconfigure(0, weight=1)

            # 加载并显示图片
            self._load_and_display_image(canvas, file_path, file_name, info_text, preview_window)

            # 设置窗口关闭事件
            preview_window.protocol("WM_DELETE_WINDOW", preview_window.destroy)
            preview_window.grab_set()  # 模态窗口
            preview_window.wait_window()  # 等待窗口关闭

        except Exception as e:
            self.logger.error(f"预览功能失败: {e}")
            messagebox.showerror("预览失败", f"预览功能失败:\n{str(e)}")
            if preview_window and preview_window.winfo_exists():
                try:
                    preview_window.destroy()
                except:
                    pass

    def _load_and_display_image(self, canvas, file_path, file_name, info_text, preview_window):
        """加载并显示图片到画布"""
        try:
            img = None

            # 处理PDF文件
            if file_path.lower().endswith('.pdf'):
                canvas.create_text(10, 10, anchor='nw', text="正在加载PDF文件...", fill='blue', font=('Microsoft YaHei', 14))
                preview_window.update()

                # 转换PDF的第一页为图片
                try:
                    import pypdfium2
                    pdf = pypdfium2.PdfDocument(file_path)
                    page = pdf.get_page(0)

                    # 转换为图片（高分辨率用于预览）
                    bitmap = page.render(
                        scale=3.0,  # 高分辨率
                        grayscale=False,  # 修复参数名
                        fill_annotation=True
                    )
                    img = bitmap.to_pil()
                    pdf.close()

                    # 更新信息
                    file_size = os.path.getsize(file_path) / 1024 / 1024  # MB
                    info = f"PDF文件: {file_name}\n文件大小: {file_size:.2f} MB\n图片尺寸: {img.width} × {img.height}"
                    self.update_info_text(info_text, info)

                except Exception as pdf_error:
                    self.logger.error(f"PDF转换失败: {pdf_error}")
                    canvas.create_text(10, 10, anchor='nw',
                        text=f"PDF文件预览失败\n{str(pdf_error)}\n请确保已安装pypdfium2",
                        fill='red', font=('Microsoft YaHei', 12))
                    return
            else:
                # 直接打开图片文件
                img = Image.open(file_path)

                # 更新信息
                file_size = os.path.getsize(file_path) / 1024  # KB
                info = f"图片文件: {file_name}\n文件大小: {file_size:.1f} KB\n图片尺寸: {img.width} × {img.height} | 模式: {img.mode}"
                self.update_info_text(info_text, info)

            if img is not None:
                # 限制显示尺寸
                max_width, max_height = 850, 600
                img_width, img_height = img.size

                if img_width > max_width or img_height > max_height:
                    ratio = min(max_width / img_width, max_height / img_height)
                    display_width = int(img_width * ratio)
                    display_height = int(img_height * ratio)
                    display_img = img.resize((display_width, display_height), Image.Resampling.LANCZOS)
                else:
                    display_img = img

                # 转换为Tkinter可用的格式
                photo = ImageTk.PhotoImage(display_img)

                # 清空画布并显示图片
                canvas.delete("all")
                canvas.create_image(0, 0, anchor='nw', image=photo)
                canvas.config(scrollregion=canvas.bbox('all'))

                # 保存引用防止垃圾回收
                preview_window.image_photo = photo

                # 如果有处理信息，添加到信息显示
                if file_path in self.processing_info:
                    result = self.processing_info[file_path]
                    if result:
                        current_info = info_text.get("1.0", tk.END).strip()
                        additional_info = f"\nOCR状态: {result.get('OCR状态', '未知')}"
                        additional_info += f"\nAI置信度: {result.get('AI置信度', 0):.1%}"
                        self.update_info_text(info_text, current_info + additional_info)

                # 如果是图纸模式且有图签检测信息，显示标注
                if self.ocr_mode.get() == 'drawing':
                    self.display_signature_in_canvas(canvas, img, file_path)

        except Exception as e:
            self.logger.error(f"图片加载失败: {e}")
            canvas.create_text(10, 10, anchor='nw',
                text=f"图片加载失败\n{str(e)}",
                fill='red', font=('Microsoft YaHei', 12))

    def update_info_text(self, text_widget, text_content):
        """更新信息文本"""
        try:
            text_widget.config(state=tk.NORMAL)
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", text_content)
            text_widget.config(state=tk.DISABLED)
        except Exception as e:
            self.logger.error(f"更新信息文本失败: {e}")

    def display_signature_in_canvas(self, canvas, img, file_path):
        """在Canvas中显示图签检测结果"""
        try:
            # 查找已有的图签检测结果
            if file_path in self.processing_info:
                result = self.processing_info[file_path]
                if result and '图签区域' in result:
                    signature_region = result['图签区域']
                    if signature_region:
                        # 计算显示比例
                        canvas_width = canvas.winfo_width()
                        if canvas_width > 1:
                            # 获取显示尺寸
                            bbox = canvas.bbox('all')
                            if bbox:
                                display_width = bbox[2] - bbox[0]
                                display_height = bbox[3] - bbox[1]
                                ratio = min(display_width / img.width, display_height / img.height)

                                # 缩放图签区域坐标
                                left = signature_region[0] * ratio
                                top = signature_region[1] * ratio
                                right = signature_region[2] * ratio
                                bottom = signature_region[3] * ratio

                                # 绘制红色矩形框
                                canvas.create_rectangle(left, top, right, bottom,
                                    outline='red', width=2, tags='signature')

                                # 添加标注文字
                                canvas.create_text(left, top - 10, anchor='sw',
                                    text="图签区域", fill='red', font=('Microsoft YaHei', 10, 'bold'))
        except Exception as e:
            self.logger.error(f"显示图签标注失败: {e}")

    def detect_signature_region_safe(self, file_path: str, parent_window):
        """安全的图签区域检测方法"""
        if not self.image_optimizer:
            messagebox.showerror("错误", "图签检测功能不可用，请确保已安装image_optimizer模块")
            return

        try:
            self.status_label.config(text="检测图签区域...", style='Warning.TLabel')

            # 在新线程中执行检测
            def detect_thread():
                try:
                    with Image.open(file_path) as img:
                        # 检测图签区域
                        signature_region = self.image_optimizer.detect_signature_region(img)

                        # 在主线程中更新UI
                        parent_window.after(0, lambda: self.display_signature_result(
                            img, signature_region, img.size, parent_window, file_path))

                except Exception as e:
                    error_msg = f"图签检测失败:\n{str(e)}"
                    parent_window.after(0, lambda: messagebox.showerror("检测失败", error_msg))
                finally:
                    parent_window.after(0, lambda: self.status_label.config(
                        text="图签检测完成", style='Success.TLabel'))

            # 启动检测线程
            thread = threading.Thread(target=detect_thread)
            thread.daemon = True
            thread.start()

        except Exception as e:
            self.logger.error(f"图签检测功能失败: {e}")
            messagebox.showerror("检测失败", f"图签检测功能失败:\n{str(e)}")

    def on_file_select(self, event):
        """文件选择事件处理 - 更新右侧预览"""
        try:
            selection = self.file_tree.selection()
            if selection:
                item = selection[0]
                values = self.file_tree.item(item)['values']
                file_name = values[0]

                # 获取完整路径
                file_path = self._get_file_path_from_item(item, values)

                if not file_path:
                    self.clear_preview()
                    return

                # 更新预览
                self.update_preview(file_path, file_name)
                self.preview_current_file = file_path
            else:
                # 清空预览
                self.clear_preview()

        except Exception as e:
            self.logger.error(f"文件选择处理失败: {e}")

    def update_preview(self, file_path: str, file_name: str):
        """更新右侧预览显示"""
        try:
            # 更新当前文件标签
            self.current_preview_label.config(text=f"当前: {file_name}", foreground='blue')

            # 清空预览画布
            self.preview_canvas.delete("all")

            # 验证文件路径
            if not file_path or file_path == '-' or not os.path.exists(file_path):
                self.preview_canvas.create_text(10, 10, anchor='nw', text="文件路径无效", fill='red')
                return

            # 加载并显示图片
            from PIL import Image, ImageTk

            img = None

            try:
                # 处理PDF文件
                if file_path.lower().endswith('.pdf'):
                    # 转换PDF的第一页为图片
                    try:
                        import pypdfium2
                        pdf = pypdfium2.PdfDocument(file_path)
                        page = pdf.get_page(0)

                        # 转换为图片
                        bitmap = page.render(
                            scale=2.0,  # 适中的分辨率用于预览
                            grayscale=False,  # 修复参数名
                            fill_annotation=True
                        )
                        img = bitmap.to_pil()
                        pdf.close()
                    except Exception as pdf_error:
                        self.logger.warning(f"PDF转换失败，尝试其他方法: {pdf_error}")
                        # 如果PDF转换失败，显示提示信息
                        self.preview_canvas.create_text(10, 10, anchor='nw',
                            text=f"PDF文件预览\n请双击打开详细预览\n文件: {file_name}",
                            fill='blue', font=('Microsoft YaHei', 12))
                        return
                else:
                    # 直接打开图片文件
                    img = Image.open(file_path)

                if img is None:
                    self.preview_canvas.create_text(10, 10, anchor='nw', text="无法加载图片", fill='red')
                    return

                # 获取图片尺寸
                img_width, img_height = img.size

                # 计算显示尺寸
                self.preview_canvas.update_idletasks()  # 确保canvas尺寸已更新
                canvas_width = self.preview_canvas.winfo_width()
                canvas_height = self.preview_canvas.winfo_height()

                if canvas_width > 1 and canvas_height > 1:
                    # 限制显示尺寸
                    max_width = canvas_width - 20
                    max_height = canvas_height - 20

                    if img_width > max_width or img_height > max_height:
                        ratio = min(max_width / img_width, max_height / img_height)
                        display_width = int(img_width * ratio)
                        display_height = int(img_height * ratio)
                        display_img = img.resize((display_width, display_height), Image.Resampling.LANCZOS)
                    else:
                        display_img = img

                    # 转换为Tkinter可用的格式
                    photo = ImageTk.PhotoImage(display_img)

                    # 在Canvas中显示图片
                    self.preview_canvas.create_image(10, 10, anchor='nw', image=photo)
                    self.preview_canvas.config(scrollregion=self.preview_canvas.bbox('all'))

                    # 保存引用防止垃圾回收
                    self.preview_canvas.image_photo = photo

                    # 如果是图纸模式，显示图签检测信息
                    if self.ocr_mode.get() == 'drawing' and file_path in self.processing_info:
                        self.show_preview_annotations(file_path)

                    # 显示文件信息
                    info_text = f"尺寸: {img_width}x{img_height} | 模式: {img.mode}"
                    self.preview_canvas.create_text(10, img_height + 20, anchor='nw',
                        text=info_text, fill='gray', font=('Microsoft YaHei', 9))

            except Exception as e:
                self.logger.error(f"预览图片加载失败: {e}")
                self.preview_canvas.create_text(10, 10, anchor='nw',
                    text=f"图片加载失败\n{file_name}\n错误: {str(e)}",
                    fill='red', font=('Microsoft YaHei', 10))

        except Exception as e:
            self.logger.error(f"更新预览失败: {e}")
            self.current_preview_label.config(text=f"预览加载失败: {file_name}", foreground='red')
            # 在画布上显示错误信息
            self.preview_canvas.create_text(10, 10, anchor='nw',
                text=f"预览加载失败\n{file_name}\n错误: {str(e)}",
                fill='red', font=('Microsoft YaHei', 10))

    def clear_preview(self):
        """清空预览"""
        self.preview_canvas.delete("all")
        self.current_preview_label.config(text="未选择文件", foreground='gray')
        self.preview_current_file = None

    def show_preview_annotations(self, file_path: str):
        """在预览中显示注释信息"""
        try:
            result = self.processing_info.get(file_path, {})

            if not result:
                return

            # 创建注释文本
            annotations = []

            # OCR和AI状态
            if result.get('OCR状态'):
                annotations.append(f"OCR状态: {result['OCR状态']}")
            if result.get('AI置信度', 0) > 0:
                annotations.append(f"AI置信度: {result['AI置信度']:.1%}")

            # 处理统计
            if result.get('处理统计'):
                stats = result['处理统计']
                if stats.get('图片优化'):
                    annotations.append("图片优化: 是" if stats['图片优化'] else "图片优化: 否")
                if stats.get('图签检测'):
                    annotations.append(f"图签检测: {stats['图签检测']}")

            # 显示注释
            if annotations:
                y_offset = 20
                for annotation in annotations:
                    self.preview_canvas.create_text(15, y_offset, text=annotation,
                                                   fill='blue', font=('Microsoft YaHei', 10),
                                                   anchor='w')
                    y_offset += 20

        except Exception as e:
            self.logger.error(f"显示预览注释失败: {e}")

    def refresh_preview(self):
        """刷新当前预览"""
        if self.preview_current_file:
            self.update_preview(self.preview_current_file, os.path.basename(self.preview_current_file))

    def show_signature_detection(self):
        """在预览区域显示图签检测结果"""
        try:
            selection = self.file_tree.selection()
            if not selection:
                messagebox.showinfo("提示", "请先选择一个文件")
                return

            item = selection[0]
            values = self.file_tree.item(item)['values']

            # 获取完整路径
            file_path = self._get_file_path_from_item(item, values)

            if not file_path:
                messagebox.showerror("错误", "无法获取文件路径")
                return

            # 清空预览并显示图签检测
            self.current_preview_label.config(text="检测图签区域...", foreground='orange')
            self.preview_canvas.delete("all")

            # 在新线程中执行检测
            def detect_thread():
                try:
                    if not self.image_optimizer:
                        messagebox.showerror("错误", "图签检测功能不可用")
                        return

                    with Image.open(file_path) as img:
                        # 检测图签区域
                        signature_region = self.image_optimizer.detect_signature_region(img)

                        # 在主线程中显示结果
                        self.root.after(0, lambda: self.display_signature_in_preview(
                            img, signature_region, file_path))

                except Exception as e:
                    error_msg = f"图签检测失败:\n{str(e)}"
                    self.root.after(0, lambda: messagebox.showerror("检测失败", error_msg))
                finally:
                    self.current_preview_label.config(text="图签检测完成", foreground='green')

            # 启动检测线程
            thread = threading.Thread(target=detect_thread)
            thread.daemon = True
            thread.start()

        except Exception as e:
            self.logger.error(f"显示图签检测失败: {e}")
            messagebox.showerror("检测失败", f"显示图签检测失败:\n{str(e)}")

    def display_signature_result(self, img, signature_region, original_size, signature_window, file_path):
        """显示图签检测结果"""
        try:
            # 创建结果显示框架
            result_frame = ttk.Frame(signature_window)
            result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # 显示检测结果
            if signature_region:
                info_text = f"✅ 检测到图签区域: {signature_region}"
                ttk.Label(result_frame, text=info_text,
                         font=('Microsoft YaHei', 11, 'bold')).pack(pady=5)

                # 创建图片显示区域
                canvas_frame = ttk.Frame(result_frame)
                canvas_frame.pack(fill=tk.BOTH, expand=True)

                canvas = tk.Canvas(canvas_frame, bg='white')
                canvas.pack(fill=tk.BOTH, expand=True)

                # 显示原图并标注图签区域
                display_img = img.copy()
                if max(display_img.size) > 800:
                    ratio = 800 / max(display_img.size)
                    new_size = (int(display_img.width * ratio), int(display_img.height * ratio))
                    display_img = display_img.resize(new_size, Image.Resampling.LANCZOS)

                photo = ImageTk.PhotoImage(display_img)
                canvas.create_image(0, 0, anchor='nw', image=photo)
                canvas.image_photo = photo

                # 缩放图签区域坐标
                scale_x = display_img.width / original_size[0]
                scale_y = display_img.height / original_size[1]

                left = int(signature_region[0] * scale_x)
                top = int(signature_region[1] * scale_y)
                right = int(signature_region[2] * scale_x)
                bottom = int(signature_region[3] * scale_y)

                # 绘制图签区域框
                canvas.create_rectangle(left, top, right, bottom,
                                       outline='red', width=3, dash=(5, 5))
                canvas.create_text(left, top-10, text="图签区域",
                                   fill='red', font=('Microsoft YaHei', 10, 'bold'))

                # 显示坐标信息
                coord_text = f"坐标: {signature_region}"
                ttk.Label(result_frame, text=coord_text).pack(pady=5)

                # 创建裁剪预览
                crop_frame = ttk.LabelFrame(result_frame, text="裁剪预览", padding="5")
                crop_frame.pack(fill=tk.X, pady=5)

                crop_canvas = tk.Canvas(crop_frame, bg='white', height=200)
                crop_canvas.pack(fill=tk.X)

                # 裁剪图签区域并显示
                if self.image_optimizer:
                    cropped_img = self.image_optimizer.crop_signature_region(img, signature_region)

                    if max(cropped_img.size) > 600:
                        crop_ratio = 600 / max(cropped_img.size)
                        crop_new_size = (int(cropped_img.width * crop_ratio), int(cropped_img.height * crop_ratio))
                        cropped_display = cropped_img.resize(crop_new_size, Image.Resampling.LANCZOS)
                    else:
                        cropped_display = cropped_img

                    crop_photo = ImageTk.PhotoImage(cropped_display)
                    crop_canvas.create_image(10, 10, anchor='nw', image=crop_photo)
                    crop_canvas.image_photo = crop_photo

                    # 显示裁剪后尺寸
                    size_text = f"裁剪后尺寸: {cropped_img.size[0]} × {cropped_img.size[1]}"
                    ttk.Label(crop_frame, text=size_text).pack(pady=5)

            else:
                info_text = "❌ 未检测到图签区域"
                ttk.Label(result_frame, text=info_text,
                         font=('Microsoft YaHei', 11, 'bold')).pack(pady=20)

                # 显示原图预览
                canvas_frame = ttk.Frame(result_frame)
                canvas_frame.pack(fill=tk.BOTH, expand=True)

                canvas = tk.Canvas(canvas_frame, bg='white')
                canvas.pack(fill=tk.BOTH, expand=True)

                if max(img.size) > 600:
                    ratio = 600 / max(img.size)
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    display_img = img.resize(new_size, Image.Resampling.LANCZOS)
                else:
                    display_img = img

                photo = ImageTk.PhotoImage(display_img)
                canvas.create_image(10, 10, anchor='nw', image=photo)
                canvas.image_photo = photo

                size_text = f"图片尺寸: {original_size[0]} × {original_size[1]}"
                ttk.Label(result_frame, text=size_text).pack(pady=5)

            # 添加关闭按钮
            button_frame = ttk.Frame(signature_window)
            button_frame.pack(pady=10)

            ttk.Button(button_frame, text="关闭",
                      command=signature_window.destroy).pack()

        except Exception as e:
            self.logger.error(f"显示图签结果失败: {e}")
            messagebox.showerror("显示错误", f"显示图签检测结果失败:\n{str(e)}")

    def display_signature_in_preview(self, img, signature_region, file_path):
        """在预览画布中显示图签检测结果"""
        try:
            from PIL import Image, ImageTk

            # 清空画布
            self.preview_canvas.delete("all")

            # 显示原图
            if max(img.size) > 600:
                ratio = 600 / max(img.size)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                display_img = img.resize(new_size, Image.Resampling.LANCZOS)
            else:
                display_img = img.copy()

            photo = ImageTk.PhotoImage(display_img)
            self.preview_canvas.create_image(10, 10, anchor='nw', image=photo)
            self.preview_canvas.image_photo = photo

            # 如果检测到图签区域，显示标注
            if signature_region:
                # 缩放坐标
                scale_x = display_img.width / img.size[0]
                scale_y = display_img.height / img.size[1]

                left = int(signature_region[0] * scale_x) + 10
                top = int(signature_region[1] * scale_y) + 10
                right = int(signature_region[2] * scale_x) + 10
                bottom = int(signature_region[3] * scale_y) + 10

                # 绘制图签区域框
                self.preview_canvas.create_rectangle(left, top, right, bottom,
                                               outline='red', width=3, dash=(5, 5))
                self.preview_canvas.create_text(left, top-10, text="图签区域",
                                                   fill='red', font=('Microsoft YaHei', 10, 'bold'))

                # 显示坐标信息
                coord_text = f"图签区域: {signature_region}"
                self.preview_canvas.create_text(15, bottom + 20, text=coord_text,
                                                   fill='red', font=('Microsoft YaHei', 10),
                                                   anchor='w')

                # 创建裁剪预览
                try:
                    if self.image_optimizer:
                        cropped_img = self.image_optimizer.crop_signature_region(img, signature_region)

                        # 显示裁剪后的图片
                        if max(cropped_img.size) > 400:
                            crop_ratio = 400 / max(cropped_img.size)
                            crop_new_size = (int(cropped_img.width * crop_ratio), int(cropped_img.height * crop_ratio))
                            cropped_display = cropped_img.resize(crop_new_size, Image.Resampling.LANCZOS)
                        else:
                            cropped_display = cropped_img

                        crop_photo = ImageTk.PhotoImage(cropped_display)
                        self.preview_canvas.create_image(15, bottom + 60, anchor='nw', image=crop_photo)
                        self.preview_canvas.image_crop_photo = crop_photo

                        size_text = f"裁剪后: {cropped_img.size[0]} × {cropped_img.size[1]}"
                        self.preview_canvas.create_text(15, bottom + 80 + cropped_display.height, text=size_text,
                                                           fill='green', font=('Microsoft YaHei', 9),
                                                           anchor='w')
                except Exception as e:
                    self.logger.error(f"裁剪预览显示失败: {e}")

            else:
                # 未检测到图签区域
                self.preview_canvas.create_text(15, 50, text="❌ 未检测到图签区域",
                                                   fill='gray', font=('Microsoft YaHei', 12),
                                                   anchor='w')

        except Exception as e:
            self.logger.error(f"显示图签结果失败: {e}")
            messagebox.showerror("显示错误", f"显示图签检测结果失败:\n{str(e)}")

    def on_closing(self):
        """窗口关闭事件处理"""
        if messagebox.askokcancel("退出", "确定要退出程序吗？"):
            self.logger.info("程序正常退出")
            self.root.destroy()

    def run(self):
        """运行GUI程序"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("程序被用户中断")
        except Exception as e:
            self.logger.error(f"程序运行出错: {e}")
        finally:
            self.logger.info("程序结束")


def main():
    """主函数"""
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('ocr_tool.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    try:
        # 创建并运行GUI
        app = UniversalOCRGUI()
        app.run()
    except Exception as e:
        logging.error(f"程序启动失败: {e}")
        messagebox.showerror("错误", f"程序启动失败:\n{str(e)}")


if __name__ == "__main__":
    main()