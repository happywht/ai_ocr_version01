#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能发票解析器
使用智谱AI进行发票字段的智能识别和提取
"""

import anthropic
import json
import re
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
from field_config import field_config_manager


class AIInvoiceParser:
    """AI智能发票解析器"""

    def __init__(self, api_key: str = None, base_url: str = None, model: str = "glm-4.6"):
        """
        初始化AI解析器

        Args:
            api_key: 智谱API密钥
            base_url: 智谱API基础URL
            model: 使用的模型名称
        """
        # 使用提供的配置或默认配置
        self.api_key = api_key or "ccd69d4c776d4e2696a6ef026159fb9c.YUPVkBmrRXu1xoZG"
        self.base_url = base_url or "https://open.bigmodel.cn/api/anthropic"
        self.model = model

        # 初始化Anthropic客户端
        self.client = anthropic.Anthropic(
            api_key=self.api_key,
            base_url=self.base_url
        )

        # 设置日志
        self.logger = logging.getLogger(__name__)

        # 字段定义和验证规则
        self.field_definitions = {
            "发票号码": {
                "description": "发票的唯一标识号码，通常是8-12位数字或字母数字组合",
                "pattern": r"[A-Za-z0-9]{8,20}",
                "required": True
            },
            "开票日期": {
                "description": "发票开具的日期，格式为YYYY-MM-DD",
                "pattern": r"\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?",
                "required": True,
                "format": "date"
            },
            "销售方名称": {
                "description": "开票方（销售方）的公司全称",
                "pattern": r"[^发票号码开票日期销售方购买方合计金额税额\s]{2,50}",
                "required": True
            },
            "购买方名称": {
                "description": "收票方（购买方）的公司全称",
                "pattern": r"[^发票号码开票日期销售方购买方合计金额税额\s]{2,50}",
                "required": True
            },
            "合计金额": {
                "description": "价税合计金额，不含税符号的纯数字",
                "pattern": r"\d+(?:,\d{3})*(?:\.\d{1,2})?",
                "required": True,
                "format": "number"
            },
            "税额": {
                "description": "增值税税额，不含税符号的纯数字",
                "pattern": r"\d+(?:,\d{3})*(?:\.\d{1,2})?",
                "required": True,
                "format": "number"
            }
        }

    def create_extraction_prompt(self, ocr_text: str, field_names: List[str] = None) -> str:
        """
        创建专业的字段提取提示词

        Args:
            ocr_text: OCR识别的原始文本
            field_names: 需要提取的字段名称列表，如果为None则使用所有配置的字段

        Returns:
            完整的AI提示词
        """
        # 如果没有指定字段，使用所有配置的字段
        if field_names is None:
            field_names = field_config_manager.get_field_names()

        # 生成字段描述
        field_descriptions = []
        for field_name in field_names:
            field = field_config_manager.get_field(field_name)
            if field:
                format_note = ""
                if field.field_type == "date":
                    format_note = "（格式：YYYY-MM-DD）"
                elif field.field_type == "amount":
                    format_note = "（只返回数字，不包含货币符号）"
                elif field.field_type == "number":
                    format_note = "（只返回数字）"

                field_descriptions.append(f"- {field_name}：{field.description}{format_note}")

        prompt = f"""你是一个专业的文档信息识别专家，擅长从OCR识别的文本中准确提取关键字段信息。

# 任务说明
请从以下OCR识别的文本中提取指定的字段信息。文本可能包含识别错误、格式混乱或噪声，请运用你的专业知识进行准确识别和修正。

# 需要提取的字段
{chr(10).join(field_descriptions)}

# 提取要求
1. **准确性优先**：如果信息不完整或模糊，请基于上下文进行合理推断
2. **格式标准化**：
   - 日期格式统一为：YYYY-MM-DD
   - 金额和数字格式统一为：纯数字（不含逗号和货币符号），金额保留两位小数
   - 文本字段保持原始格式，去除多余空格
3. **数据验证**：提取的数据应该符合基本的业务逻辑（如日期合理、金额为正数等）
4. **缺失处理**：如果某个字段确实无法识别，设为null

# 输出格式要求
请严格按照以下JSON格式输出，不要添加任何其他文字：

```json
{{"""

        # 为每个字段生成JSON格式
        json_fields = []
        for field_name in field_names:
            field = field_config_manager.get_field(field_name)
            if field:
                json_fields.append(f'  "{field_name}": "识别到的{field.description}或null"')

        prompt += ",\n".join(json_fields)
        prompt += """
}
```

# OCR识别文本
```
"""
        prompt += ocr_text
        prompt += """
```

请仔细分析以上文本，提取出准确的字段信息，并严格按照JSON格式输出。"""

        return prompt

    def extract_fields_with_ai(self, ocr_text: str, field_names: List[str] = None) -> Optional[Dict[str, Any]]:
        """
        使用AI提取发票字段

        Args:
            ocr_text: OCR识别的原始文本
            field_names: 需要提取的字段名称列表，如果为None则使用所有配置的字段

        Returns:
            提取的字段字典，包含置信度和原始响应
        """
        try:
            # 如果没有指定字段，使用所有配置的字段
            if field_names is None:
                field_names = field_config_manager.get_field_names()

            # 创建提示词
            prompt = self.create_extraction_prompt(ocr_text, field_names)

            self.logger.info(f"开始AI智能字段提取，目标字段：{field_names}")

            # 调用AI API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1  # 低温度确保结果稳定
            )

            # 获取AI响应
            ai_response = response.content[0].text.strip()
            self.logger.debug(f"AI原始响应: {ai_response}")

            # 解析JSON响应
            extracted_fields = self.parse_ai_response(ai_response)

            # 使用字段配置管理器验证和清理字段
            validated_fields = {}
            for field_name, field_value in extracted_fields.items():
                validated_fields[field_name] = field_config_manager.validate_field_value(field_name, field_value)

            # 计算置信度（基于字段配置）
            confidence = self.calculate_dynamic_confidence(extracted_fields, validated_fields, field_names)

            # 构建完整结果
            result = {
                "extracted_fields": validated_fields,
                "ai_confidence": confidence,
                "raw_ai_response": ai_response,
                "processing_time": response.usage.output_tokens if hasattr(response, 'usage') else None,
                "model_used": self.model,
                "field_names": field_names  # 记录提取的字段列表
            }

            self.logger.info(f"AI字段提取完成，成功提取 {len([v for v in validated_fields.values() if v])} 个字段")

            return result

        except Exception as e:
            self.logger.error(f"AI字段提取失败: {str(e)}")
            return None

    def parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """
        解析AI的JSON响应

        Args:
            ai_response: AI返回的文本响应

        Returns:
            解析后的字段字典
        """
        try:
            # 提取JSON部分
            json_match = re.search(r'```json\s*(.*?)\s*```', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 如果没有代码块标记，尝试直接解析
                json_str = ai_response.strip()

            # 解析JSON
            extracted_fields = json.loads(json_str)

            return extracted_fields

        except json.JSONDecodeError as e:
            self.logger.error(f"AI响应JSON解析失败: {e}")
            self.logger.debug(f"尝试解析的JSON字符串: {ai_response}")

            # 尝试简单的文本解析作为备选方案
            return self.extract_fields_fallback(ai_response)

        except Exception as e:
            self.logger.error(f"AI响应解析失败: {e}")
            return {}

    def extract_fields_fallback(self, text: str) -> Dict[str, Any]:
        """
        备用字段提取方法（简单正则表达式）

        Args:
            text: AI响应文本

        Returns:
            提取的字段字典
        """
        fields = {}

        # 简单的字段提取正则
        patterns = {
            "发票号码": r'发票号码["\s:：]+([^",\n]+)',
            "开票日期": r'开票日期["\s:：]+([^",\n]+)',
            "销售方名称": r'销售方名称["\s:：]+([^",\n]+)',
            "购买方名称": r'购买方名称["\s:：]+([^",\n]+)',
            "合计金额": r'合计金额["\s:：]+([^",\n]+)',
            "税额": r'税额["\s:：]+([^",\n]+)'
        }

        for field, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                value = match.group(1).strip()
                # 清理值
                if value and value not in ['null', 'None', '']:
                    fields[field] = value
                else:
                    fields[field] = None
            else:
                fields[field] = None

        return fields

    def validate_and_clean_fields(self, fields: Dict[str, Any]) -> Dict[str, str]:
        """
        验证和清理提取的字段

        Args:
            fields: AI提取的原始字段

        Returns:
            验证后的字段字典
        """
        cleaned_fields = {}

        for field_name, field_value in fields.items():
            if field_name not in self.field_definitions:
                continue

            field_info = self.field_definitions[field_name]

            # 处理null值
            if field_value is None or field_value in ['null', 'None', '']:
                cleaned_fields[field_name] = None
                continue

            # 字符串处理
            field_str = str(field_value).strip()

            # 格式标准化
            if field_info.get("format") == "date":
                # 日期格式标准化
                date_match = re.search(r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})日?', field_str)
                if date_match:
                    year, month, day = date_match.groups()
                    cleaned_fields[field_name] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                else:
                    cleaned_fields[field_name] = field_str
            elif field_info.get("format") == "number":
                # 数字格式标准化（移除逗号和货币符号）
                number_match = re.search(r'[\d,]+\.?\d*', field_str.replace('￥', '').replace(',', ''))
                if number_match:
                    number_str = number_match.group()
                    try:
                        # 转换为浮点数再格式化，确保两位小数
                        number = float(number_str)
                        cleaned_fields[field_name] = f"{number:.2f}"
                    except ValueError:
                        cleaned_fields[field_name] = field_str
                else:
                    cleaned_fields[field_name] = field_str
            else:
                # 普通字段清理
                cleaned_fields[field_name] = field_str

            # 验证字段格式
            if cleaned_fields[field_name] is not None:
                pattern = field_info.get("pattern")
                if pattern and not re.match(pattern, cleaned_fields[field_name]):
                    self.logger.warning(f"字段 {field_name} 格式验证失败: {cleaned_fields[field_name]}")

        return cleaned_fields

    def calculate_dynamic_confidence(self, raw_fields: Dict[str, Any], validated_fields: Dict[str, str], field_names: List[str]) -> float:
        """
        计算提取结果的置信度（基于动态字段配置）

        Args:
            raw_fields: AI提取的原始字段
            validated_fields: 验证后的字段
            field_names: 提取的字段名称列表

        Returns:
            置信度分数 (0.0-1.0)
        """
        if not field_names:
            return 0.0

        total_fields = len(field_names)
        extracted_count = 0
        validated_count = 0
        required_satisfied = 0
        total_required = 0

        for field_name in field_names:
            field = field_config_manager.get_field(field_name)
            if not field:
                continue

            # 统计必需字段
            if field.required:
                total_required += 1

            field_value = validated_fields.get(field_name)
            if field_value and field_value not in ['null', 'None', '']:
                extracted_count += 1

                # 进行字段类型验证
                try:
                    if field.field_type == "date":
                        import re
                        date_pattern = r'\d{4}-\d{2}-\d{2}'
                        if re.match(date_pattern, field_value):
                            validated_count += 1
                    elif field.field_type in ["amount", "number"]:
                        import re
                        number_pattern = r'\d+(?:\.\d+)?'
                        if re.match(number_pattern, field_value.replace(',', '')):
                            validated_count += 1
                    elif field.field_type == "text":
                        if len(field_value.strip()) >= 2:
                            validated_count += 1
                    else:
                        # 自定义字段类型，基本长度检查
                        if len(field_value.strip()) >= 1:
                            validated_count += 1
                except Exception:
                    pass

                # 检查必需字段是否满足
                if field.required and field_value not in ['null', 'None', '']:
                    required_satisfied += 1

        # 基于多个因子计算置信度
        extraction_rate = extracted_count / total_fields  # 提取率
        validation_rate = validated_count / max(extracted_count, 1)  # 验证通过率
        required_rate = required_satisfied / max(total_required, 1)  # 必需字段满足率

        # 加权计算置信度
        confidence = (extraction_rate * 0.4 + validation_rate * 0.4 + required_rate * 0.2)
        return round(confidence, 3)

    def test_ai_connection(self) -> bool:
        """
        测试AI服务连接

        Returns:
            连接是否成功
        """
        try:
            # 发送简单的测试请求
            response = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[
                    {
                        "role": "user",
                        "content": "Hello, please respond with 'OK'"
                    }
                ]
            )

            return response.content[0].text.strip().lower() in ['ok', 'hello']

        except Exception as e:
            self.logger.error(f"AI服务连接测试失败: {str(e)}")
            return False


# def main():
#     """测试AI解析器"""
#     parser = AIInvoiceParser()

#     # 测试AI连接
#     print("测试AI服务连接...")
#     if parser.test_ai_connection():
#         print("✅ AI服务连接正常")
#     else:
#         print("❌ AI服务连接失败")
#         return

#     # 测试字段提取
#     test_ocr_text = """
#     专用发票
#     发票号码：12345678
#     开票日期：2024年01月01日

#     销售方：某某科技有限公司
#     纳税人识别号：91110000000000001X

#     购买方：某某贸易有限公司
#     纳税人识别号：91110000000000002Y

#     价税合计：￥10,600.00
#     税额：600.00
#     """

#     print("\n测试AI字段提取...")
#     result = parser.extract_fields_with_ai(test_ocr_text)

#     if result:
#         print("✅ AI字段提取成功")
#         print("\n提取结果:")
#         for field, value in result["extracted_fields"].items():
#             print(f"  {field}: {value}")

#         print(f"\n置信度: {result['ai_confidence']}")
#         print(f"使用模型: {result['model_used']}")
#     else:
#         print("❌ AI字段提取失败")


# if __name__ == "__main__":
#     main()