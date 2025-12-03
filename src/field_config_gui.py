#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字段配置管理GUI界面
提供用户友好的字段配置管理功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from field_config import field_config_manager, FieldDefinition


class FieldConfigGUI:
    """字段配置管理GUI类"""

    def __init__(self, parent_window=None):
        self.logger = logging.getLogger(__name__)
        self.parent_window = parent_window  # 父窗口引用

        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("字段配置管理器")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')

        # 设置样式
        self.setup_styles()

        # 创建界面
        self.create_widgets()

        # 加载现有配置
        self.load_field_configs()

        # 当前选中的字段
        self.current_field_name = None

    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        style.theme_use('clam')

        # 配置样式
        style.configure('Title.TLabel', font=('Microsoft YaHei', 12, 'bold'))
        style.configure('Heading.TLabel', font=('Microsoft YaHei', 10, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')

    def create_widgets(self):
        """创建界面组件"""
        # 主标题
        title_label = ttk.Label(self.root, text="🔧 动态字段配置管理器", style='Title.TLabel')
        title_label.pack(pady=10)

        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 左侧：字段列表
        left_frame = ttk.LabelFrame(main_frame, text="字段列表", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))

        # 字段列表
        self.field_listbox = tk.Listbox(left_frame, width=25, height=25)
        self.field_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.field_listbox.bind('<<ListboxSelect>>', self.on_field_select)

        # 滚动条
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.field_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.field_listbox.config(yscrollcommand=scrollbar.set)

        # 字段列表按钮
        list_button_frame = ttk.Frame(left_frame)
        list_button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        ttk.Button(list_button_frame, text="新增字段", command=self.add_field).pack(fill=tk.X, pady=2)
        ttk.Button(list_button_frame, text="删除字段", command=self.delete_field).pack(fill=tk.X, pady=2)

        # 右侧：字段详情
        right_frame = ttk.LabelFrame(main_frame, text="字段详情", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 字段详情表单
        self.create_field_form(right_frame)

        # 底部：操作按钮
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=20, pady=10)

        # 左侧按钮
        left_buttons = ttk.Frame(bottom_frame)
        left_buttons.pack(side=tk.LEFT)

        if self.parent_window:
            ttk.Button(left_buttons, text="🔙 返回主界面", command=self.return_to_main).pack(side=tk.LEFT, padx=(0, 10))

        # 右侧按钮
        right_buttons = ttk.Frame(bottom_frame)
        right_buttons.pack(side=tk.RIGHT)

        ttk.Button(right_buttons, text="保存配置", command=self.save_config).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(right_buttons, text="重置配置", command=self.reset_config).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(right_buttons, text="导入配置", command=self.import_config).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(right_buttons, text="导出配置", command=self.export_config).pack(side=tk.RIGHT, padx=(10, 0))

        # 状态栏
        self.status_label = ttk.Label(self.root, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=(0, 10))

    def create_field_form(self, parent):
        """创建字段详情表单"""
        # 字段名称
        ttk.Label(parent, text="字段名称:", style='Heading.TLabel').grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.name_var, width=30).grid(row=0, column=1, sticky=tk.EW, pady=5)

        # 字段描述
        ttk.Label(parent, text="字段描述:", style='Heading.TLabel').grid(row=1, column=0, sticky=tk.W, pady=5)
        self.description_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.description_var, width=30).grid(row=1, column=1, sticky=tk.EW, pady=5)

        # 字段类型
        ttk.Label(parent, text="字段类型:", style='Heading.TLabel').grid(row=2, column=0, sticky=tk.W, pady=5)
        self.type_var = tk.StringVar()
        type_combo = ttk.Combobox(parent, textvariable=self.type_var,
                                 values=["text", "number", "date", "amount", "custom"],
                                 state="readonly", width=28)
        type_combo.grid(row=2, column=1, sticky=tk.EW, pady=5)
        type_combo.bind("<<ComboboxSelected>>", self.on_type_change)

        # 是否必需
        self.required_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="必需字段", variable=self.required_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)

        # AI提示词
        ttk.Label(parent, text="AI提取提示词:", style='Heading.TLabel').grid(row=4, column=0, sticky=tk.NW, pady=5)
        self.ai_prompt_var = tk.StringVar()
        ai_prompt_text = tk.Text(parent, height=3, width=40)
        ai_prompt_text.grid(row=4, column=1, sticky=tk.EW, pady=5)
        self.ai_prompt_text = ai_prompt_text

        # 正则表达式模式
        ttk.Label(parent, text="正则表达式模式:", style='Heading.TLabel').grid(row=5, column=0, sticky=tk.NW, pady=5)

        # 模式列表框架
        pattern_frame = ttk.Frame(parent)
        pattern_frame.grid(row=5, column=1, sticky=tk.EW, pady=5)

        # 模式列表
        pattern_list_frame = ttk.Frame(pattern_frame)
        pattern_list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.pattern_listbox = tk.Listbox(pattern_list_frame, height=6)
        self.pattern_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        pattern_scrollbar = ttk.Scrollbar(pattern_list_frame, orient="vertical", command=self.pattern_listbox.yview)
        pattern_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.pattern_listbox.config(yscrollcommand=pattern_scrollbar.set)

        # 模式操作按钮
        pattern_button_frame = ttk.Frame(pattern_frame)
        pattern_button_frame.pack(side=tk.RIGHT, padx=(10, 0))

        ttk.Button(pattern_button_frame, text="添加", command=self.add_pattern, width=8).pack(pady=2)
        ttk.Button(pattern_button_frame, text="删除", command=self.delete_pattern, width=8).pack(pady=2)
        ttk.Button(pattern_button_frame, text="编辑", command=self.edit_pattern, width=8).pack(pady=2)

        # 模式输入对话框
        self.pattern_entry_var = tk.StringVar()

        # 配置列权重
        parent.columnconfigure(1, weight=1)

    def load_field_configs(self):
        """加载字段配置到列表"""
        self.field_listbox.delete(0, tk.END)

        fields = field_config_manager.get_all_fields()
        for field_name in fields.keys():
            self.field_listbox.insert(tk.END, field_name)

        self.status_label.config(text=f"已加载 {len(fields)} 个字段配置")

    def on_field_select(self, event):
        """字段选择事件处理"""
        selection = self.field_listbox.curselection()
        if not selection:
            return

        field_name = self.field_listbox.get(selection[0])
        self.current_field_name = field_name

        # 加载字段详情
        field = field_config_manager.get_field(field_name)
        if field:
            self.load_field_to_form(field)

        self.status_label.config(text=f"已选择字段: {field_name}")

    def load_field_to_form(self, field: FieldDefinition):
        """加载字段数据到表单"""
        self.name_var.set(field.name)
        self.description_var.set(field.description)
        self.type_var.set(field.field_type)
        self.required_var.set(field.required)

        # 加载AI提示词
        self.ai_prompt_text.delete(1.0, tk.END)
        self.ai_prompt_text.insert(1.0, field.ai_prompt)

        # 加载正则表达式模式
        self.pattern_listbox.delete(0, tk.END)
        for pattern in field.patterns:
            self.pattern_listbox.insert(tk.END, pattern)

    def add_field(self):
        """添加新字段"""
        # 清空表单
        self.name_var.set("")
        self.description_var.set("")
        self.type_var.set("text")
        self.required_var.set(False)
        self.ai_prompt_text.delete(1.0, tk.END)
        self.pattern_listbox.delete(0, tk.END)

        self.current_field_name = None
        self.status_label.config(text="请填写字段详情并保存")

    def delete_field(self):
        """删除字段"""
        selection = self.field_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要删除的字段")
            return

        field_name = self.field_listbox.get(selection[0])

        if messagebox.askyesno("确认删除", f"确定要删除字段 '{field_name}' 吗？"):
            if field_config_manager.remove_field(field_name):
                self.field_listbox.delete(selection[0])
                self.status_label.config(text=f"已删除字段: {field_name}", style='Success.TLabel')
                self.add_field()  # 清空表单
            else:
                messagebox.showerror("错误", "删除字段失败")

    def add_pattern(self):
        """添加正则表达式模式"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加正则表达式模式")
        dialog.geometry("500x150")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="正则表达式模式:").pack(pady=10)

        pattern_var = tk.StringVar()
        pattern_entry = ttk.Entry(dialog, textvariable=pattern_var, width=60)
        pattern_entry.pack(pady=5, padx=20)
        pattern_entry.focus()

        def save_pattern():
            pattern = pattern_var.get().strip()
            if pattern:
                self.pattern_listbox.insert(tk.END, pattern)
                dialog.destroy()
            else:
                messagebox.showwarning("提示", "请输入有效的正则表达式模式")

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="确定", command=save_pattern).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def delete_pattern(self):
        """删除选中的正则表达式模式"""
        selection = self.pattern_listbox.curselection()
        if selection:
            self.pattern_listbox.delete(selection[0])

    def edit_pattern(self):
        """编辑选中的正则表达式模式"""
        selection = self.pattern_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要编辑的模式")
            return

        current_pattern = self.pattern_listbox.get(selection[0])

        dialog = tk.Toplevel(self.root)
        dialog.title("编辑正则表达式模式")
        dialog.geometry("500x150")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="正则表达式模式:").pack(pady=10)

        pattern_var = tk.StringVar(value=current_pattern)
        pattern_entry = ttk.Entry(dialog, textvariable=pattern_var, width=60)
        pattern_entry.pack(pady=5, padx=20)
        pattern_entry.focus()
        pattern_entry.select_range(0, tk.END)

        def save_pattern():
            pattern = pattern_var.get().strip()
            if pattern:
                self.pattern_listbox.delete(selection[0])
                self.pattern_listbox.insert(selection[0], pattern)
                dialog.destroy()
            else:
                messagebox.showwarning("提示", "请输入有效的正则表达式模式")

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="确定", command=save_pattern).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def on_type_change(self, event):
        """字段类型改变事件处理"""
        field_type = self.type_var.get()

        # 根据字段类型设置默认的AI提示词
        default_prompts = {
            "text": "提取文本信息",
            "number": "提取数字信息",
            "date": "提取日期信息",
            "amount": "提取金额信息",
            "custom": "提取自定义信息"
        }

        if not self.ai_prompt_text.get(1.0, tk.END).strip():
            self.ai_prompt_text.delete(1.0, tk.END)
            self.ai_prompt_text.insert(1.0, default_prompts.get(field_type, ""))

    def save_config(self):
        """保存字段配置"""
        # 获取表单数据
        field_name = self.name_var.get().strip()
        if not field_name:
            messagebox.showwarning("提示", "请输入字段名称")
            return

        description = self.description_var.get().strip()
        if not description:
            messagebox.showwarning("提示", "请输入字段描述")
            return

        field_type = self.type_var.get()
        required = self.required_var.get()
        ai_prompt = self.ai_prompt_text.get(1.0, tk.END).strip()

        # 获取正则表达式模式
        patterns = []
        for i in range(self.pattern_listbox.size()):
            patterns.append(self.pattern_listbox.get(i))

        # 创建字段定义
        field = FieldDefinition(
            name=field_name,
            description=description,
            field_type=field_type,
            patterns=patterns,
            ai_prompt=ai_prompt,
            required=required
        )

        # 保存字段配置
        if field_config_manager.add_field(field):
            # 如果是新增字段，添加到列表
            if self.current_field_name != field_name:
                self.field_listbox.insert(tk.END, field_name)

            # 保存到文件
            if field_config_manager.save_config():
                self.status_label.config(text=f"已保存字段配置: {field_name}", style='Success.TLabel')
                self.current_field_name = field_name
            else:
                messagebox.showerror("错误", "保存配置文件失败")
        else:
            messagebox.showerror("错误", "保存字段配置失败")

    def reset_config(self):
        """重置配置为默认值"""
        if messagebox.askyesno("确认重置", "确定要重置所有字段配置为默认值吗？此操作不可撤销。"):
            field_config_manager.load_default_config()
            self.load_field_configs()
            self.add_field()  # 清空表单
            self.status_label.config(text="已重置为默认配置", style='Success.TLabel')

    def import_config(self):
        """导入配置文件"""
        file_path = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                if field_config_manager.import_from_dict(config_data):
                    self.load_field_configs()
                    self.status_label.config(text="配置导入成功", style='Success.TLabel')
                else:
                    messagebox.showerror("错误", "配置导入失败")

            except Exception as e:
                messagebox.showerror("错误", f"配置文件格式错误: {str(e)}")

    def export_config(self):
        """导出配置文件"""
        file_path = filedialog.asksaveasfilename(
            title="保存配置文件",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )

        if file_path:
            try:
                config_data = field_config_manager.export_to_dict()

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=2)

                self.status_label.config(text=f"配置已导出到: {file_path}", style='Success.TLabel')

            except Exception as e:
                messagebox.showerror("错误", f"配置导出失败: {str(e)}")

    def return_to_main(self):
        """返回主界面"""
        if self.parent_window:
            # 销毁当前窗口
            self.root.destroy()
            # 显示父窗口
            self.parent_window.deiconify()
        else:
            # 如果没有父窗口，直接销毁
            self.root.destroy()

    def run(self):
        """运行GUI"""
        self.root.mainloop()


def main():
    """主函数"""
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # 创建并运行GUI
    app = FieldConfigGUI()
    app.run()


if __name__ == "__main__":
    main()