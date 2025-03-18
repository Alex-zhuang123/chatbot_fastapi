from typing import List
from pydantic import BaseModel,Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts.image import ImagePromptTemplate
from langchain_core.prompts import SystemMessagePromptTemplate,HumanMessagePromptTemplate,PromptTemplate
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
image_prompt_local = ImagePromptTemplate(
    prompt="{image}",  # 本地绝对路径
    image_format="path"  # 依赖模型支持
)

system_template = "你是一名模具工程师助手，负责从图片中提取关键信息，并生成符合要求的JSON格式。" \
"严格遵循以下规则：" \
"1. 仅提取下面九个字段："\
"编号、单号、等级、材料、QCR、尺寸、易损件、数量、外发编号"
"2. 每个字段独立提取，缺失字段保留空值"\
"3. 支持多条目提取:"\
"- 当检测到多个零件信息时,以JSON数组形式返回所有条目"

system_message = SystemMessagePromptTemplate.from_template(system_template)

# 定义文本模板（即使无变量，也需显式声明）
text_prompt = PromptTemplate(
    template="请分析以下图像内容：",  # 文本内容
    input_variables=[]  # 无变量时设为空列表
)

human_message = HumanMessagePromptTemplate(
    prompt=text_prompt,  # 文本部分
    additional_inputs={"image": image_prompt_local}  # 图像部分
)

chat_prompt = ChatPromptTemplate.from_messages(
    [
        system_message,
        human_message
    ]
)


llm = get_llm()

parser = JsonOutputParser(pydantic_object=ExtractionData)

extractor = chat_prompt | llm | parser


def extract_key_developments(all_images):
    """批量提取图片中的关键进展并合并结果"""
    merged = ExtractionData()
    for image in all_images:
        try:
            # 使用 invoke 替代 batch 以便逐条处理错误
            ext = extractor.invoke({
    "image": image
})
            print(ext)
            merged.key_developments.extend(ext)
        except Exception as e:
            logger.error(f"处理图片失败: {image}... 错误: {str(e)}")
    return merged.key_developments
        
