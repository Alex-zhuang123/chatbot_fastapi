from typing import List
from pydantic import BaseModel,Field
from langchain_core.prompts import ChatPromptTemplate
from llm import get_llm
from config import logger
from langchain_core.output_parsers import JsonOutputParser


class KeyDevelopments(BaseModel):
    材料: str = Field(default="", description="材料信息(材质/材料规格)")
    零件名称: str = Field(default="", description="零件名称信息(部件名称/零件号)")
    图号: str = Field(default="", description="图号信息(图纸编号/代号)")


class ExtractionData(BaseModel):
    """提取图纸中的关键信息，支持多条目结构化输出"""
    key_developments: List[KeyDevelopments] = Field(
        default_factory=list,
        description="多个零件信息的列表"
    )


# 定义提示词,提供说明与额外的上下文。
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是一名专业工程师，负责从机械图纸文本中提取结构化信息。"
            "严格遵循以下规则："
            "1. 仅提取三个字段："
               "材料(同义词：材质/材料规格/Material)"
               "零件名称(同义词：部件名称/零件号/Part No.)"
               "图号(同义词：图纸编号/代号/Drawing No.)"
            "2. 字段可能使用中文同义词或不同分隔符(如：材质=铝合金;部件名:螺栓;图号A1234)"
            "3. 每个字段独立提取，缺失字段保留空值"
            "4. 支持多条目提取:"
               "- 当检测到多个零件信息时,以JSON数组形式返回所有条目"
               "- 自动识别条目分隔符:分号(;)/换行符(\\n)/分隔线(---/***等)"
            "5. 忽略其他信息（尺寸/数量/技术参数等）"
            
            "---- 示例开始 ----"
            """示例1（多分隔符混合）：
                输入：材质_不锈钢#图纸编号_X9Y9Z;材料：碳钢,零件名称:法兰盘,图号:B-5678
                输出：
                [{{\"材料\": \"不锈钢\", \"零件名称\": \"\", \"图号\": \"X9Y9Z\"}},
                {{\"材料\": \"碳钢\", \"零件名称\": \"法兰盘\", \"图号\": \"B-5678\"}}]"""
            "---- 示例结束 ----"

            "---- 示例开始 ----"
            """示例2（分隔线+不完整字段）：
                输入："
                --- 零件组1 ---\n
                材料规格: 青铜; 零件号: 垫片-001\n
                *** 零件组2 ***\n
                部件名称：齿轮组
                输出：
                [{{\"材料\": \"青铜\", \"零件名称\": \"垫片-001\", \"图号\": \"\"}},
                {{\"材料\": \"\", \"零件名称\": \"齿轮组\", \"图号\": \"\"}}]"""
            "---- 示例结束 ----"

            "---- 示例开始 ----"
            """示例3（异常处理）：
                输入：材料：铝合金，零件名称：螺丝，尺寸：M8
                输出：
                [{{\"材料\": \"铝合金\", \"零件名称\": \"螺丝\", \"图号\": \"\"}}]"""
            "---- 示例结束 ----"

        ),
        ("user", [
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/jpeg;base64,{image_data}"},
                },
            ]),
    ]
)


llm = get_llm()

parser = JsonOutputParser(pydantic_object=ExtractionData)

extractor = prompt | llm | parser


def extract_key_developments(images_list):
    """批量提取图片中的关键进展并合并结果"""
    merged = ExtractionData()
    for image_data in images_list:
        try:
            # 使用 invoke 替代 batch 以便逐条处理错误
            ext = extractor.invoke({"image_data": image_data})
            print(ext)
            merged.key_developments.extend(ext)
        except Exception as e:
            logger.error(f"处理失败（文本片段）: {image_data[:50]}... 错误: {str(e)}")
    return merged.key_developments
        
