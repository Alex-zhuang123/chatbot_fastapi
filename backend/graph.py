from typing import List
from pydantic import BaseModel,Field
from langchain_core.prompts import ChatPromptTemplate
from llm import get_llm
from config import logger
from langchain_core.output_parsers import JsonOutputParser


class KeyDevelopments(BaseModel):
    编号: str = Field(default="", )
    单号: str = Field(default="", )
    等级: str = Field(default="", )
    材料: str = Field(default="", )
    QCR: str = Field(default="", )
    尺寸: str = Field(default="", )
    易损件: str = Field(default="", )
    数量: str = Field(default="", )
    外发编号: str = Field(default="", )


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
            "1. 仅提取下面九个字段："
                "编号、单号、等级、材料、QCR、尺寸、易损件、数量、外发编号"
            "2. 每个字段独立提取，缺失字段保留空值"
            "3. 支持多条目提取:"
               "- 当检测到多个零件信息时,以JSON数组形式返回所有条目"            
        ),
        ("human", "{text}"),
    ]
)


llm = get_llm()

parser = JsonOutputParser(pydantic_object=ExtractionData)

extractor = prompt | llm | parser


def extract_key_developments(text_list:List[str]):
    """批量提取文本中的关键进展并合并结果"""
    merged = ExtractionData()
    for text in text_list:
        try:
            # 使用 invoke 替代 batch 以便逐条处理错误
            ext = extractor.invoke({"text": text})
            print(ext)
            merged.key_developments.extend(ext)
        except Exception as e:
            logger.error(f"处理失败（文本片段）: {text[:50]}... 错误: {str(e)}")
    return merged.key_developments
        
