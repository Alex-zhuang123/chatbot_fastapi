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


def extract_key_developments(all_images):
    """批量提取图片中的关键进展并合并结果"""
    results = ExtractionData()

    for image_path in all_images:
        try:
            with open(image_path, "rb") as f:
                image_base64 = base64.b64encode(f.read()).decode("utf-8")

            completion = client.chat.completions.create(
            model="qwen-vl-plus",
            messages=[{
                "role": "user",
                "content": [
                        {"type": "text", "text": "提取下面九个字段：编号、单号、等级、材料、QCR、尺寸、易损件、数量、外发编号,"\
                        "每个零件返回独立JSON对象，格式为：[{}, {}, ...]"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                }]
            )

             # 提取并解析JSON [[1]][[3]]
            raw_content = completion.choices[0].message.content
            json_str = raw_content.split("```json")[1].split("```")[0].strip()
            data = json.loads(json_str)

            # 遍历所有零件条目 [[1]][[8]]
            for item_dict in data:
                item = KeyDevelopments(**item_dict)
                results.key_developments.append(item)


        except FileNotFoundError:
            print(f"错误：文件 {image_path} 未找到，跳过处理")  # [[9]]
        except (IndexError, json.JSONDecodeError) as e:
            print(f"JSON解析失败：{e}，原始响应：{raw_content}")  # [[1]][[3]]
        except ValidationError as e:
            print(f"数据验证失败：{e}，解析后的数据：{item_dict}")  # [[1]]
        except Exception as e:
            print(f"处理图片 {image_path} 时发生未知错误：{str(e)}")
    
    return results

# 使用示例
if __name__ == "__main__":
    images = ["D:/estimate/files/A170147.jpeg"]
    result = extract_key_developments(images)
    print(result.model_dump_json(indent=2))


