import os
from openai import OpenAI
from pydantic import BaseModel,Field,ValidationError
import base64
from typing import List
import json

client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

class KeyDevelopments(BaseModel):
    编号: str = Field(default="", )
    单号: str = Field(default="", )
    等级: str = Field(default="", )
    材料: str = Field(default="", )
    QCR: str = Field(default="", )
    尺寸: str = Field(default="", )
    易损件: str = Field(default="", )
    数量: int = Field(default="")
    外发编号: str = Field(default="", )


class ExtractionData(BaseModel):
    """提取图纸中的关键信息，支持多条目结构化输出"""
    key_developments: List[KeyDevelopments] = Field(
        default_factory=list,
        description="多个零件信息的列表"
    )



async def extract_key_developments(all_images_base64):
    """批量提取图片中的关键进展并合并结果"""
    results = ExtractionData()
    for image_base64 in all_images_base64:
        try:
            completion = await client.chat.completions.create(
                model="qwen-vl-plus",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "提取下面九个字段:编号、单号、等级、材料、QCR、尺寸、易损件、数量、外发编号," \
                         "返回JSON对象,格式示例为:[{}]" \
                         "如果存在空值,则返回空字符串,不要自己虚构"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                }]
            )
            # 提取并解析JSON
            raw_content = completion.choices[0].message.content
            json_str = raw_content.split("```json")[1].split("```")[0].strip()
            data = json.loads(json_str)
            # 遍历所有零件条目
            for item_dict in data:
                item = KeyDevelopments(**item_dict)
                results.key_developments.append(item)
        except FileNotFoundError:
            print(f"错误:文件 {image_base64} 未找到，跳过处理")
        except (IndexError, json.JSONDecodeError) as e:
            print(f"JSON解析失败:{e}，原始响应：{raw_content}")
        except ValidationError as e:
            print(f"数据验证失败:{e}，解析后的数据：{item_dict}")
        except Exception as e:
            print(f"处理图片 {image_base64} 时发生未知错误：{str(e)}")
    return results

# 使用示例
if __name__ == "__main__":
    image_path = "D:/estimate/files/F2404521.png"
    
    # 检查文件是否存在
    try:
        with open(image_path, "rb") as f:
            # 读取图像并转换为 Base64 编码
            image_base64 = base64.b64encode(f.read()).decode("utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"Image file not found at path: {image_path}")
    
    # 将 Base64 编码存储在列表中
    image_base64_list = [image_base64]
    result = extract_key_developments(image_base64_list)
    print(result.model_dump_json(indent=2))


