#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业启动工具UI - 专用发票OCR识别工具
独立的现代化启动界面，不影响功能模块的独立性
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
import os
import time
import subprocess
from datetime import datetime

class LauncherGUI:
    """专业启动工具GUI界面"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("发票OCR识别工具 - 专业启动台")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        # 设置窗口属性
        self.root.resizable(True, True)

        # 初始化样式
        self.setup_styles()

        # 实例状态跟踪
        self.gui_instance = None
        self.field_config_instance = None
        self.ocr_service_running = False

        # 创建界面
        self.create_widgets()

        # 启动状态检查
        self.start_status_monitoring()

    def setup_styles(self):
        """设置界面样式"""
        try:
            style = ttk.Style()
            style.theme_use('clam')

            # 自定义颜色方案
            colors = {
                'primary': '#2c3e50',
                'secondary': '#3498db',
                'success': '#27ae60',
                'warning': '#f39c12',
                'danger': '#e74c3c',
                'light': '#ecf0f1',
                'dark': '#34495e'
            }

            # 标题样式
            style.configure('Title.TLabel',
                          font=('微软雅黑', 24, 'bold'),
                          foreground=colors['primary'])

            style.configure('Subtitle.TLabel',
                          font=('微软雅黑', 14),
                          foreground=colors['dark'])

            style.configure('Status.TLabel',
                          font=('微软雅黑', 10))

            # 按钮样式
            style.configure('Primary.TButton',
                          font=('微软雅黑', 12, 'bold'),
                          padding=(20, 10))

            style.configure('Success.TButton',
                          font=('微软雅黑', 10),
                          foreground=colors['success'])

            style.configure('Danger.TButton',
                          font=('微软雅黑', 10),
                          foreground=colors['danger'])

            # 状态标签样式
            style.configure('Running.TLabel',
                          foreground=colors['success'],
                          font=('微软雅黑', 10, 'bold'))

            style.configure('Stopped.TLabel',
                          foreground=colors['danger'],
                          font=('微软雅黑', 10, 'bold'))

        except Exception:
            # 如果样式设置失败，使用默认样式
            pass

    def create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_container = ttk.Frame(self.root, padding="30")
        main_container.pack(fill='both', expand=True)

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(2, weight=1)

        # 顶部标题区域
        self.create_header(main_container)

        # 服务状态区域
        self.create_service_status(main_container)

        # 功能模块区域
        self.create_module_controls(main_container)

        # 底部信息区域
        self.create_footer(main_container)

    def create_header(self, parent):
        """创建顶部标题区域"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 30))
        header_frame.columnconfigure(1, weight=1)

        # 主标题
        title_label = ttk.Label(header_frame, text="🚀 发票OCR识别工具", style='Title.TLabel')
        title_label.grid(row=0, column=0, sticky=tk.W)

        # 版本信息
        version_label = ttk.Label(header_frame, text="v3.0 专业版", style='Subtitle.TLabel')
        version_label.grid(row=0, column=1, sticky=tk.E)

        # 副标题
        subtitle_label = ttk.Label(header_frame,
                                 text="智能识别 · 专业配置 · 高效处理",
                                 style='Subtitle.TLabel')
        subtitle_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))

    def create_service_status(self, parent):
        """创建服务状态区域"""
        status_frame = ttk.LabelFrame(parent, text="🔧 服务状态监控", padding="20")
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 30))
        status_frame.columnconfigure(1, weight=1)

        # OCR服务状态
        ttk.Label(status_frame, text="OCR识别服务:", style='Status.TLabel').grid(
            row=0, column=0, sticky=tk.W, pady=(0, 10))
        self.ocr_status_label = ttk.Label(status_frame, text="检测中...", style='Status.TLabel')
        self.ocr_status_label.grid(row=0, column=1, sticky=tk.W, padx=(20, 0), pady=(0, 10))

        # OCR服务控制按钮
        self.ocr_service_btn = ttk.Button(status_frame, text="启动OCR服务",
                                         command=self.toggle_ocr_service)
        self.ocr_service_btn.grid(row=0, column=2, padx=(10, 0), pady=(0, 10))

        # 系统时间显示
        ttk.Label(status_frame, text="系统时间:", style='Status.TLabel').grid(
            row=1, column=0, sticky=tk.W)
        self.time_label = ttk.Label(status_frame, text="", style='Status.TLabel')
        self.time_label.grid(row=1, column=1, sticky=tk.W, padx=(20, 0))

        # 更新时间显示
        self.update_time_display()

    def create_module_controls(self, parent):
        """创建功能模块控制区域"""
        modules_frame = ttk.LabelFrame(parent, text="🎛️ 功能模块控制", padding="20")
        modules_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 30))
        modules_frame.columnconfigure(1, weight=1)
        modules_frame.rowconfigure(1, weight=1)

        # 功能1：发票OCR识别GUI
        self.create_module_card(modules_frame,
                               row=0,
                               title="📷 发票OCR识别",
                               description="智能识别发票信息，支持AI增强解析",
                               status_var="gui_instance",
                               start_cmd=self.start_gui,
                               stop_cmd=self.stop_gui)

        # 功能2：字段配置管理器
        self.create_module_card(modules_frame,
                               row=1,
                               title="⚙️ 字段配置管理器",
                               description="自定义配置识别字段，灵活适配业务需求",
                               status_var="field_config_instance",
                               start_cmd=self.start_field_config,
                               stop_cmd=self.stop_field_config)

    def create_module_card(self, parent, row, title, description, status_var, start_cmd, stop_cmd):
        """创建功能模块卡片"""
        # 模块卡片容器
        card_frame = ttk.Frame(parent)
        card_frame.grid(row=row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        card_frame.columnconfigure(1, weight=1)
        card_frame.rowconfigure(2, weight=1)

        # 模块图标和标题
        title_frame = ttk.Frame(card_frame)
        title_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        title_frame.columnconfigure(1, weight=1)

        ttk.Label(title_frame, text=title, font=('微软雅黑', 14, 'bold')).grid(
            row=0, column=0, sticky=tk.W)

        # 状态指示器
        status_label = ttk.Label(title_frame, text="● 未运行", style='Stopped.TLabel')
        status_label.grid(row=0, column=1, sticky=tk.E)

        # 模块描述
        desc_label = ttk.Label(card_frame, text=description, style='Status.TLabel')
        desc_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(0, 15))

        # 按钮区域
        button_frame = ttk.Frame(card_frame)
        button_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.S))
        button_frame.columnconfigure(2, weight=1)

        # 启动按钮
        start_btn = ttk.Button(button_frame, text="🚀 启动",
                              command=start_cmd, style='Primary.TButton')
        start_btn.grid(row=0, column=0, padx=(0, 10))

        # 停止按钮（初始禁用）
        stop_btn = ttk.Button(button_frame, text="⏹️ 停止",
                             command=stop_cmd, state='disabled')
        stop_btn.grid(row=0, column=1, padx=(0, 10))

        # 分隔线
        separator = ttk.Separator(card_frame, orient='horizontal')
        separator.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(15, 0))

        # 保存控件引用
        setattr(self, f"{status_var}_status_label", status_label)
        setattr(self, f"{status_var}_start_btn", start_btn)
        setattr(self, f"{status_var}_stop_btn", stop_btn)

    def create_footer(self, parent):
        """创建底部信息区域"""
        footer_frame = ttk.Frame(parent)
        footer_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        footer_frame.columnconfigure(1, weight=1)

        # 退出按钮
        exit_btn = ttk.Button(footer_frame, text="🚪 退出启动台",
                            command=self.exit_application,
                            style='Danger.TButton')
        exit_btn.grid(row=0, column=0, sticky=tk.W)

        # 版权信息
        copyright_label = ttk.Label(footer_frame,
                                   text="© 2024 专业发票OCR识别工具 - 技术支持版",
                                   style='Status.TLabel')
        copyright_label.grid(row=0, column=1, sticky=tk.E)

    def update_time_display(self):
        """更新时间显示"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.configure(text=current_time)
        # 每秒更新一次时间
        self.root.after(1000, self.update_time_display)

    def start_status_monitoring(self):
        """启动状态监控"""
        def check_services():
            while True:
                try:
                    # 检查OCR服务状态
                    self.check_ocr_service_status()
                    time.sleep(5)  # 每5秒检查一次
                except Exception as e:
                    print(f"状态监控异常: {e}")
                    time.sleep(10)

        # 在后台线程中启动监控
        monitor_thread = threading.Thread(target=check_services, daemon=True)
        monitor_thread.start()

    def check_ocr_service_status(self):
        """检查OCR服务状态"""
        try:
            import requests
            response = requests.get("http://127.0.0.1:1224", timeout=3)
            if response.status_code == 200:
                if not self.ocr_service_running:
                    self.root.after(0, self.update_ocr_status, True)
                    self.ocr_service_running = True
            else:
                if self.ocr_service_running:
                    self.root.after(0, self.update_ocr_status, False)
                    self.ocr_service_running = False
        except:
            if self.ocr_service_running:
                self.root.after(0, self.update_ocr_status, False)
                self.ocr_service_running = False

    def update_ocr_status(self, running):
        """更新OCR服务状态显示"""
        if running:
            self.ocr_status_label.configure(text="✅ 运行中", style='Running.TLabel')
            self.ocr_service_btn.configure(text="停止OCR服务")
        else:
            self.ocr_status_label.configure(text="❌ 未运行", style='Stopped.TLabel')
            self.ocr_service_btn.configure(text="启动OCR服务")

    def toggle_ocr_service(self):
        """切换OCR服务状态"""
        if self.ocr_service_running:
            # 停止OCR服务（这里需要根据实际情况实现）
            messagebox.showinfo("提示", "OCR服务需要手动停止\n请关闭OCR服务程序")
        else:
            # 启动OCR服务
            self.start_ocr_service()

    def start_ocr_service(self):
        """启动OCR服务"""
        try:
            # 尝试使用OCR服务检测器
            from ocr_service_detector import ocr_detector

            # 检查服务是否已在运行
            if ocr_detector.is_ocr_service_running():
                messagebox.showinfo("提示", "OCR服务已在运行中")
                return

            # 获取最佳服务
            service = ocr_detector.get_best_service_fast()
            if not service:
                service = ocr_detector.get_best_service(quick_mode=True)

            if service:
                ocr_service_path, service_type = service

                # 查找可执行文件
                main_script = os.path.join(ocr_service_path, "main.py")
                exe_file = os.path.join(ocr_service_path, "Umi-OCR.exe")

                if os.path.exists(exe_file):
                    command = [exe_file]
                elif os.path.exists(main_script):
                    command = [sys.executable, main_script]
                else:
                    messagebox.showerror("错误", f"未找到OCR服务可执行文件:\n{ocr_service_path}")
                    return

                # 启动服务
                subprocess.Popen(command, cwd=ocr_service_path)
                messagebox.showinfo("成功", "OCR服务启动中...\n请等待几秒后刷新状态")
            else:
                messagebox.showerror("错误", "未找到OCR服务安装\n请手动启动OCR服务")

        except ImportError:
            # 如果没有检测器，使用默认提示
            messagebox.showinfo("提示",
                              "请手动启动OCR服务：\n"
                              "1. 运行Umi-OCR程序\n"
                              "2. 确保服务在端口1224运行")
        except Exception as e:
            messagebox.showerror("错误", f"启动OCR服务失败: {str(e)}")

    def start_gui(self):
        """启动发票OCR识别GUI"""
        if self.gui_instance is not None:
            messagebox.showwarning("提示", "发票OCR识别界面已在运行中")
            return

        def start_gui_thread():
            try:
                # 添加src目录到路径
                current_dir = os.path.dirname(os.path.abspath(__file__))
                src_path = os.path.join(current_dir, 'src')
                if src_path not in sys.path:
                    sys.path.insert(0, src_path)

                # 导入并启动GUI
                from invoice_gui import InvoiceOCRGUI

                # 标记实例运行
                self.gui_instance = True
                self.root.after(0, self.update_module_status, 'gui', True)

                # 创建并运行GUI
                app = InvoiceOCRGUI()
                app.run()

            except Exception as e:
                messagebox.showerror("错误", f"启动发票OCR识别界面失败: {str(e)}")
            finally:
                # 重置实例状态
                self.gui_instance = None
                self.root.after(0, self.update_module_status, 'gui', False)

        # 在新线程中启动GUI
        gui_thread = threading.Thread(target=start_gui_thread, daemon=True)
        gui_thread.start()

    def stop_gui(self):
        """停止发票OCR识别GUI"""
        if self.gui_instance is None:
            return

        # 这里可以添加优雅关闭的逻辑
        # 目前只是重置状态
        self.gui_instance = None
        self.update_module_status('gui', False)

    def start_field_config(self):
        """启动字段配置管理器"""
        if self.field_config_instance is not None:
            messagebox.showwarning("提示", "字段配置管理器已在运行中")
            return

        def start_config_thread():
            try:
                # 添加src目录到路径
                current_dir = os.path.dirname(os.path.abspath(__file__))
                src_path = os.path.join(current_dir, 'src')
                if src_path not in sys.path:
                    sys.path.insert(0, src_path)

                # 导入并启动配置管理器
                from field_config_gui import FieldConfigGUI

                # 标记实例运行
                self.field_config_instance = True
                self.root.after(0, self.update_module_status, 'field_config', True)

                # 创建并运行配置管理器
                app = FieldConfigGUI()
                app.run()

            except Exception as e:
                messagebox.showerror("错误", f"启动字段配置管理器失败: {str(e)}")
            finally:
                # 重置实例状态
                self.field_config_instance = None
                self.root.after(0, self.update_module_status, 'field_config', False)

        # 在新线程中启动配置管理器
        config_thread = threading.Thread(target=start_config_thread, daemon=True)
        config_thread.start()

    def stop_field_config(self):
        """停止字段配置管理器"""
        if self.field_config_instance is None:
            return

        # 这里可以添加优雅关闭的逻辑
        self.field_config_instance = None
        self.update_module_status('field_config', False)

    def update_module_status(self, module_name, running):
        """更新模块状态显示"""
        if module_name == 'gui':
            if running:
                self.gui_instance_status_label.configure(text="● 运行中", style='Running.TLabel')
                self.gui_instance_start_btn.configure(state='disabled')
                self.gui_instance_stop_btn.configure(state='normal')
            else:
                self.gui_instance_status_label.configure(text="● 未运行", style='Stopped.TLabel')
                self.gui_instance_start_btn.configure(state='normal')
                self.gui_instance_stop_btn.configure(state='disabled')

        elif module_name == 'field_config':
            if running:
                self.field_config_instance_status_label.configure(text="● 运行中", style='Running.TLabel')
                self.field_config_instance_start_btn.configure(state='disabled')
                self.field_config_instance_stop_btn.configure(state='normal')
            else:
                self.field_config_instance_status_label.configure(text="● 未运行", style='Stopped.TLabel')
                self.field_config_instance_start_btn.configure(state='normal')
                self.field_config_instance_stop_btn.configure(state='disabled')

    def exit_application(self):
        """退出应用程序"""
        # 检查是否有运行中的模块
        running_modules = []
        if self.gui_instance is not None:
            running_modules.append("发票OCR识别界面")
        if self.field_config_instance is not None:
            running_modules.append("字段配置管理器")

        if running_modules:
            result = messagebox.askyesno(
                "确认退出",
                f"以下模块正在运行中：\n{chr(10).join(running_modules)}\n\n"
                "确定要退出启动台吗？\n"
                "（退出后各模块可继续独立运行）"
            )
            if not result:
                return

        # 关闭启动台
        self.root.destroy()

    def run(self):
        """运行启动台"""
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
        print("🚀 启动专业发票OCR识别工具启动台...")

        # 创建并运行启动台
        launcher = LauncherGUI()
        launcher.run()

    except Exception as e:
        print(f"❌ 启动台启动失败: {e}")
        messagebox.showerror("启动失败", f"启动台无法启动: {str(e)}")


if __name__ == "__main__":
    main()