#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态字段配置管理器
支持自定义字段提取规则和AI提示词
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class FieldDefinition:
    """字段定义类"""
    name: str  # 字段名称
    description: str  # 字段描述
    field_type: str  # 字段类型：text, number, date, amount, custom
    patterns: List[str]  # 正则表达式模式列表
    ai_prompt: str  # AI提取提示词
    required: bool = False  # 是否必需字段
    validation_rules: Optional[Dict[str, Any]] = None  # 验证规则


class FieldConfigManager:
    """字段配置管理器"""

    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)

        # 默认配置路径
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'field_configs.json')

        self.config_path = config_path
        self.fields: Dict[str, FieldDefinition] = {}

        # 加载配置
        self.load_config()

        # 如果没有配置，使用默认配置
        if not self.fields:
            self.load_default_config()

    def load_default_config(self):
        """加载默认字段配置"""
        self.logger.info("加载默认字段配置...")

        default_fields = [
            FieldDefinition(
                name="发票号码",
                description="发票的唯一标识号码",
                field_type="text",
                patterns=[
                    r'发票号码[:：]\s*(\w+)',
                    r'No\.?\s*[:：]?\s*(\w+)',
                    r'发票代码[:：]\s*(\w+)',
                    r'票据号码[:：]\s*(\w+)'
                ],
                ai_prompt="提取发票号码或票据号码",
                required=True
            ),
            FieldDefinition(
                name="开票日期",
                description="发票开具日期",
                field_type="date",
                patterns=[
                    r'开票日期[:：]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)',
                    r'日期[:：]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)',
                    r'Date[:：]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)'
                ],
                ai_prompt="提取开票日期，格式为YYYY-MM-DD",
                required=True
            ),
            FieldDefinition(
                name="销售方名称",
                description="开票方公司名称",
                field_type="text",
                patterns=[
                    r'销售方[:：]\s*([^开票方购买方收款方付款方\s]{2,50})',
                    r'收款人[:：]\s*([^开票方购买方收款方付款方\s]{2,50})',
                    r'Seller[:：]\s*([^\n]{2,100})',
                    r'开票方[:：]\s*([^\n]{2,100})'
                ],
                ai_prompt="提取销售方或开票方的公司名称",
                required=True
            ),
            FieldDefinition(
                name="购买方名称",
                description="购买方公司名称",
                field_type="text",
                patterns=[
                    r'购买方[:：]\s*([^开票方购买方收款方付款方\s]{2,50})',
                    r'付款人[:：]\s*([^开票方购买方收款方付款方\s]{2,50})',
                    r'Buyer[:：]\s*([^\n]{2,100})',
                    r'受票方[:：]\s*([^\n]{2,100})'
                ],
                ai_prompt="提取购买方或受票方的公司名称",
                required=True
            ),
            FieldDefinition(
                name="合计金额",
                description="价税合计总金额",
                field_type="amount",
                patterns=[
                    r'价税合计[:：]\s*￥?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                    r'合计金额[:：]\s*￥?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                    r'Total[:：]\s*￥?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                    r'金额[:：]\s*￥?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'
                ],
                ai_prompt="提取价税合计或总金额，只返回数字",
                required=True
            ),
            FieldDefinition(
                name="税额",
                description="增值税税额",
                field_type="amount",
                patterns=[
                    r'税额[:：]\s*￥?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                    r'增值税[:：]\s*￥?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                    r'Tax[:：]\s*￥?\s*(\d+(?:,\d{3}*(?:\.\d{2})?)'
                ],
                ai_prompt="提取增值税税额，只返回数字",
                required=False
            )
        ]

        # 添加字段到配置
        for field in default_fields:
            self.fields[field.name] = field

        self.logger.info(f"加载了 {len(default_fields)} 个默认字段配置")

    def load_config(self):
        """从文件加载配置"""
        if not os.path.exists(self.config_path):
            self.logger.info(f"配置文件不存在: {self.config_path}")
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # 解析字段定义
            for field_name, field_data in config_data.get('fields', {}).items():
                self.fields[field_name] = FieldDefinition(**field_data)

            self.logger.info(f"从配置文件加载了 {len(self.fields)} 个字段配置")

        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")

    def save_config(self):
        """保存配置到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

            # 转换为可序列化格式
            config_data = {
                'version': '1.0',
                'created_at': datetime.now().isoformat(),
                'fields': {name: asdict(field) for name, field in self.fields.items()}
            }

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"配置已保存到: {self.config_path}")
            return True

        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
            return False

    def add_field(self, field: FieldDefinition) -> bool:
        """添加字段配置"""
        if not field.name or not field.name.strip():
            self.logger.error("字段名称不能为空")
            return False

        # 检查字段名是否已存在
        if field.name in self.fields:
            self.logger.warning(f"字段 '{field.name}' 已存在，将被覆盖")

        self.fields[field.name] = field
        self.logger.info(f"添加字段配置: {field.name}")
        return True

    def remove_field(self, field_name: str) -> bool:
        """删除字段配置"""
        if field_name not in self.fields:
            self.logger.warning(f"字段 '{field_name}' 不存在")
            return False

        del self.fields[field_name]
        self.logger.info(f"删除字段配置: {field_name}")
        return True

    def get_field_names(self) -> List[str]:
        """获取所有字段名称"""
        return list(self.fields.keys())

    def get_field(self, field_name: str) -> Optional[FieldDefinition]:
        """获取字段定义"""
        return self.fields.get(field_name)

    def get_all_fields(self) -> Dict[str, FieldDefinition]:
        """获取所有字段定义"""
        return self.fields.copy()

    def create_ai_prompt(self, fields: List[str]) -> str:
        """根据字段配置创建AI提示词"""
        if not fields:
            return ""

        prompt = """你是一个专业的文档信息识别专家，请根据提供的OCR识别文本，准确提取以下字段信息："""

        for field_name in fields:
            field = self.get_field(field_name)
            if field:
                prompt += f"\n\n{field.name}: {field.ai_prompt}"
                if field.field_type == "date":
                    prompt += "（格式：YYYY-MM-DD）"
                elif field.field_type == "amount":
                    prompt += "（只返回数字，不包含货币符号）"
                elif field.field_type == "number":
                    prompt += "（只返回数字）"

        prompt += f"""

请严格按照以下JSON格式输出每个字段的值："""

        field_list = []
        for field_name in fields:
            field_list.append(f'  "{field_name}": "识别到的{self.fields[field_name].description}或null"')

        prompt += "{\n" + ",\n".join(field_list) + "\n}"

        prompt += """

注意事项：
1. 只提取文本中明确存在的信息，不要编造内容
2. 如果某个字段无法识别，返回null
3. 数字字段只返回纯数字，不包含货币符号或文字
4. 日期字段使用YYYY-MM-DD格式
5. 仔细检查文本，确保提取准确的信息

OCR识别文本：
{ocr_text}

请仔细分析以上文本，提取出准确的字段信息，并严格按照JSON格式输出。"""

        return prompt

    def validate_field_value(self, field_name: str, value: str) -> str:
        """验证字段值"""
        if not value:
            return value

        field = self.get_field(field_name)
        if not field:
            return value

        try:
            # 根据字段类型验证
            if field.field_type == "date":
                # 日期格式验证和标准化
                import re
                date_patterns = [
                    r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})日?',
                    r'(\d{4})-(\d{1,2})-(\d{1,2})',
                    r'(\d{1,2})[/](\d{1,2})[/](\d{4})',
                ]

                for pattern in date_patterns:
                    match = re.search(pattern, value)
                    if match:
                        if pattern == date_patterns[2]:  # MM/DD/YYYY
                            return f"{match.group(3)}-{match.group(1):0>2}-{match.group(2):0>2}"
                        else:
                            return f"{match.group(1)}-{match.group(2):0>2}-{match.group(3):0>2}"

            elif field.field_type == "amount":
                # 金额格式处理
                import re
                amount_match = re.search(r'(\d+(?:,\d{3})*(?:\.\d{2})?)', value.replace(',', ''))
                if amount_match:
                    return amount_match.group(1)

            elif field.field_type == "number":
                # 数字格式处理
                import re
                number_match = re.search(r'\d+', value.replace(',', ''))
                if number_match:
                    return number_match.group()

        except Exception as e:
            self.logger.warning(f"字段 {field_name} 验证失败: {e}")

        return value

    def get_required_fields(self) -> List[str]:
        """获取必需字段列表"""
        return [name for name, field in self.fields.items() if field.required]

    def export_to_dict(self) -> Dict[str, Any]:
        """导出配置为字典格式"""
        return {
            'fields': {name: asdict(field) for name, field in self.fields.items()},
            'field_names': self.get_field_names(),
            'required_fields': self.get_required_fields(),
            'total_fields': len(self.fields)
        }

    def import_from_dict(self, config_data: Dict[str, Any]) -> bool:
        """从字典导入配置"""
        try:
            self.fields.clear()

            for field_name, field_data in config_data.get('fields', {}).items():
                self.fields[field_name] = FieldDefinition(**field_data)

            self.logger.info(f"从字典导入了 {len(self.fields)} 个字段配置")
            return True

        except Exception as e:
            self.logger.error(f"导入配置失败: {e}")
            return False


# 全局字段配置管理器实例
field_config_manager = FieldConfigManager()