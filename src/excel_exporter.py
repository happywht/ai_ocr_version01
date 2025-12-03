#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel导出工具
提供专业的Excel文件导出功能，支持多种格式和样式
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.utils import get_column_letter
from datetime import datetime
import os
from typing import List, Dict, Any, Optional


class ExcelExporter:
    """Excel导出工具类"""

    def __init__(self):
        """初始化Excel导出工具"""
        # 定义样式
        self.setup_styles()

    def setup_styles(self):
        """设置Excel样式"""
        # 字体样式
        self.title_font = Font(name='微软雅黑', size=14, bold=True, color='FFFFFF')
        self.header_font = Font(name='微软雅黑', size=12, bold=True, color='FFFFFF')
        self.content_font = Font(name='微软雅黑', size=11)
        self.number_font = Font(name='Arial', size=11)

        # 填充样式
        self.title_fill = PatternFill(start_color='2E86AB', end_color='2E86AB', fill_type='solid')
        self.header_fill = PatternFill(start_color='4A90E2', end_color='4A90E2', fill_type='solid')
        self.success_fill = PatternFill(start_color='D4EDDA', end_color='D4EDDA', fill_type='solid')
        self.warning_fill = PatternFill(start_color='FFF3CD', end_color='FFF3CD', fill_type='solid')
        self.error_fill = PatternFill(start_color='F8D7DA', end_color='F8D7DA', fill_type='solid')

        # 边框样式
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        self.thick_border = Border(
            left=Side(style='thick'),
            right=Side(style='thick'),
            top=Side(style='thick'),
            bottom=Side(style='thick')
        )
        self.default_border = thin_border

        # 对齐样式
        self.center_alignment = Alignment(horizontal='center', vertical='center')
        self.left_alignment = Alignment(horizontal='left', vertical='center')
        self.right_alignment = Alignment(horizontal='right', vertical='center')

    def export_single_invoice(self, file_path: str, invoice_data: Dict[str, Any],
                           format_type: str = "horizontal") -> bool:
        """
        导出单张发票数据

        Args:
            file_path: 导出文件路径
            invoice_data: 发票数据
            format_type: 导出格式 ("horizontal" 横向, "vertical" 纵向)

        Returns:
            导出是否成功
        """
        try:
            # 创建工作簿
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "发票识别结果"

            if format_type == "horizontal":
                self._create_horizontal_format(ws, invoice_data)
            else:
                self._create_vertical_format(ws, invoice_data)

            # 设置列宽
            self._auto_adjust_columns(ws)

            # 保存文件
            wb.save(file_path)
            return True

        except Exception as e:
            print(f"Excel导出失败: {str(e)}")
            return False

    def export_batch_invoices(self, file_path: str, invoices_data: List[Dict[str, Any]]) -> bool:
        """
        批量导出发票数据

        Args:
            file_path: 导出文件路径
            invoices_data: 发票数据列表

        Returns:
            导出是否成功
        """
        try:
            # 创建工作簿
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "批量识别结果"

            # 创建表头
            headers = [
                "序号", "图片路径", "处理时间", "解析方式", "AI置信度",
                "发票号码", "开票日期", "销售方名称", "购买方名称",
                "合计金额", "税额", "识别状态"
            ]

            # 设置表头
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = self.header_font
                cell.fill = self.header_fill
                cell.border = self.default_border
                cell.alignment = self.center_alignment

            # 填充数据
            for row, invoice in enumerate(invoices_data, 2):
                # 基础信息
                ws.cell(row=row, column=1, value=row-1)  # 序号
                ws.cell(row=row, column=2, value=invoice.get('图片路径', ''))
                ws.cell(row=row, column=3, value=invoice.get('处理时间', ''))
                ws.cell(row=row, column=4, value=invoice.get('解析方式', ''))
                ws.cell(row=row, column=5, value=invoice.get('AI置信度', ''))

                # 提取字段
                fields = invoice.get('提取字段', {})
                ws.cell(row=row, column=6, value=fields.get('发票号码', ''))
                ws.cell(row=row, column=7, value=fields.get('开票日期', ''))
                ws.cell(row=row, column=8, value=fields.get('销售方名称', ''))
                ws.cell(row=row, column=9, value=fields.get('购买方名称', ''))
                ws.cell(row=row, column=10, value=fields.get('合计金额', ''))
                ws.cell(row=row, column=11, value=fields.get('税额', ''))

                # 识别状态
                extracted_count = len([v for v in fields.values() if v])
                total_fields = len(fields)
                status = f"{extracted_count}/{total_fields}"
                ws.cell(row=row, column=12, value=status)

                # 设置行样式
                for col in range(1, 13):
                    cell = ws.cell(row=row, column=col)
                    cell.font = self.content_font
                    cell.border = self.default_border
                    cell.alignment = self.left_alignment

                    # 根据识别状态设置背景色
                    if col == 12:  # 状态列
                        if extracted_count == total_fields:
                            cell.fill = self.success_fill
                        elif extracted_count >= total_fields * 0.7:
                            cell.fill = self.warning_fill
                        else:
                            cell.fill = self.error_fill
                    elif col in [6, 10, 11]:  # 重要字段列
                        cell.font = self.number_font
                        cell.alignment = self.right_alignment

            # 设置列宽
            column_widths = [8, 25, 20, 15, 12, 15, 15, 25, 25, 15, 15, 12]
            for i, width in enumerate(column_widths, 1):
                ws.column_dimensions[get_column_letter(i)].width = width

            # 保存文件
            wb.save(file_path)
            return True

        except Exception as e:
            print(f"批量Excel导出失败: {str(e)}")
            return False

    def _create_horizontal_format(self, ws, invoice_data: Dict[str, Any]):
        """创建横向格式 (序号/{字段_List})"""
        # 标题
        title_cell = ws.cell(row=1, column=1, value="发票识别结果")
        title_cell.font = self.title_font
        title_cell.fill = self.title_fill
        title_cell.border = self.thick_border
        title_cell.alignment = self.center_alignment
        ws.merge_cells('A1:L1')

        # 基本信息
        basic_info = [
            ("图片路径", invoice_data.get('图片路径', '')),
            ("处理时间", invoice_data.get('处理时间', '')),
            ("解析方式", invoice_data.get('解析方式', '')),
            ("AI置信度", invoice_data.get('AI置信度', ''))
        ]

        for i, (label, value) in enumerate(basic_info, 3):
            ws.cell(row=i, column=1, value=label).font = self.header_font
            ws.cell(row=i, column=1).fill = self.header_fill
            ws.cell(row=i, column=1).border = self.default_border
            ws.cell(row=i, column=1).alignment = self.center_alignment

            ws.cell(row=i, column=2, value=value).font = self.content_font
            ws.cell(row=i, column=2).border = self.default_border
            ws.cell(row=i, column=2).alignment = self.left_alignment

        # 字段列表标题
        field_title_row = len(basic_info) + 4
        ws.cell(row=field_title_row, column=1, value="字段提取结果").font = self.title_font
        ws.cell(row=field_title_row, column=1).fill = self.title_fill
        ws.cell(row=field_title_row, column=1).border = self.thick_border
        ws.cell(row=field_title_row, column=1).alignment = self.center_alignment
        ws.merge_cells(f'A{field_title_row}:L{field_title_row}')

        # 字段列表表头
        headers = ["序号", "字段名称", "提取内容", "状态"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=field_title_row + 1, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.default_border
            cell.alignment = self.center_alignment

        # 字段数据
        fields = invoice_data.get('提取字段', {})
        field_definitions = [
            ("发票号码", "发票的唯一标识号码"),
            ("开票日期", "发票开具的日期"),
            ("销售方名称", "开票方的公司名称"),
            ("购买方名称", "收票方的公司名称"),
            ("合计金额", "价税合计金额"),
            ("税额", "增值税税额")
        ]

        for i, (field_name, description) in enumerate(field_definitions, field_title_row + 2):
            field_value = fields.get(field_name, '')
            status = "✅ 成功" if field_value else "❌ 未识别"

            # 序号
            ws.cell(row=i, column=1, value=i - field_title_row - 1).border = self.default_border
            ws.cell(row=i, column=1).alignment = self.center_alignment

            # 字段名称
            ws.cell(row=i, column=2, value=f"{field_name}\n({description})").border = self.default_border
            ws.cell(row=i, column=2).alignment = self.center_alignment

            # 提取内容
            content_cell = ws.cell(row=i, column=3, value=field_value)
            content_cell.border = self.default_border
            content_cell.alignment = self.left_alignment

            # 状态
            status_cell = ws.cell(row=i, column=4, value=status)
            status_cell.border = self.default_border
            status_cell.alignment = self.center_alignment

            # 根据状态设置颜色
            if field_value:
                status_cell.fill = self.success_fill
                content_cell.fill = self.success_fill
            else:
                status_cell.fill = self.error_fill
                content_cell.fill = self.error_fill

    def _create_vertical_format(self, ws, invoice_data: Dict[str, Any]):
        """创建纵向格式"""
        # 标题
        title_cell = ws.cell(row=1, column=1, value="发票识别结果")
        title_cell.font = self.title_font
        title_cell.fill = self.title_fill
        title_cell.border = self.thick_border
        title_cell.alignment = self.center_alignment
        ws.merge_cells('A1:C1')

        # 基本信息
        row = 3
        basic_info = [
            ("图片路径", invoice_data.get('图片路径', '')),
            ("处理时间", invoice_data.get('处理时间', '')),
            ("解析方式", invoice_data.get('解析方式', '')),
            ("AI置信度", invoice_data.get('AI置信度', ''))
        ]

        for label, value in basic_info:
            ws.cell(row=row, column=1, value=label).font = self.header_font
            ws.cell(row=row, column=1).fill = self.header_fill
            ws.cell(row=row, column=1).border = self.default_border
            ws.cell(row=row, column=1).alignment = self.center_alignment

            ws.cell(row=row, column=2, value=value).font = self.content_font
            ws.cell(row=row, column=2).border = self.default_border
            ws.cell(row=row, column=2).alignment = self.left_alignment
            ws.merge_cells(f'B{row}:C{row}')
            row += 1

        # 字段详细信息
        row += 2
        ws.cell(row=row, column=1, value="字段详细信息").font = self.title_font
        ws.cell(row=row, column=1).fill = self.title_fill
        ws.cell(row=row, column=1).border = self.thick_border
        ws.cell(row=row, column=1).alignment = self.center_alignment
        ws.merge_cells(f'A{row}:C{row}')
        row += 1

        fields = invoice_data.get('提取字段', {})
        for field_name, field_value in fields.items():
            # 字段名称
            ws.cell(row=row, column=1, value=field_name).font = self.header_font
            ws.cell(row=row, column=1).fill = self.header_fill
            ws.cell(row=row, column=1).border = self.default_border
            ws.cell(row=row, column=1).alignment = self.center_alignment

            # 字段值
            value_cell = ws.cell(row=row, column=2, value=field_value or "未识别")
            value_cell.font = self.content_font
            value_cell.border = self.default_border
            value_cell.alignment = self.left_alignment
            ws.merge_cells(f'B{row}:C{row}')

            # 根据是否有值设置颜色
            if field_value:
                value_cell.fill = self.success_fill
            else:
                value_cell.fill = self.error_fill

            row += 1

    def _auto_adjust_columns(self, ws):
        """自动调整列宽"""
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)

            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass

            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width

    def create_summary_sheet(self, wb, invoices_data: List[Dict[str, Any]]):
        """创建汇总表"""
        if not invoices_data:
            return

        ws = wb.create_sheet("数据汇总")

        # 统计信息
        total_invoices = len(invoices_data)
        successful_invoices = len([inv for inv in invoices_data
                                if len([v for v in inv.get('提取字段', {}).values() if v]) >= 4])

        # 创建汇总内容
        summary_data = [
            ("统计项目", "数值", "说明"),
            ("总发票数", total_invoices, "处理的发票总数"),
            ("成功识别", successful_invoices, "成功识别≥4个字段的发票"),
            ("识别成功率", f"{successful_invoices/total_invoices:.1%}" if total_invoices > 0 else "0%", "识别成功的比例"),
            ("导出时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "文件导出时间")
        ]

        for row, (item, value, desc) in enumerate(summary_data, 1):
            ws.cell(row=row, column=1, value=item).font = self.header_font
            ws.cell(row=row, column=1).fill = self.header_fill
            ws.cell(row=row, column=1).border = self.default_border

            ws.cell(row=row, column=2, value=value).font = self.content_font
            ws.cell(row=row, column=2).border = self.default_border

            ws.cell(row=row, column=3, value=desc).font = self.content_font
            ws.cell(row=row, column=3).border = self.default_border

        # 设置列宽
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 30


def main():
    """测试Excel导出功能"""
    # 测试数据
    test_invoice = {
        '图片路径': 'test_invoice.jpg',
        '处理时间': '2024-12-02 22:50:00',
        '解析方式': '🤖 AI智能解析',
        'AI置信度': 0.95,
        '提取字段': {
            '发票号码': '12345678',
            '开票日期': '2024-01-01',
            '销售方名称': '某某科技有限公司',
            '购买方名称': '某某贸易有限公司',
            '合计金额': '10600.00',
            '税额': '600.00'
        }
    }

    exporter = ExcelExporter()

    # 测试单张发票导出
    print("测试单张发票Excel导出...")
    if exporter.export_single_invoice("test_single_invoice.xlsx", test_invoice):
        print("✅ 单张发票导出成功")
    else:
        print("❌ 单张发票导出失败")

    # 测试批量导出
    print("\n测试批量发票Excel导出...")
    test_invoices = [test_invoice] * 3
    if exporter.export_batch_invoices("test_batch_invoices.xlsx", test_invoices):
        print("✅ 批量发票导出成功")
    else:
        print("❌ 批量发票导出失败")

    print("\nExcel导出功能测试完成！")


if __name__ == "__main__":
    main()