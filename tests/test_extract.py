import os
from openai import OpenAI
from pydantic import BaseModel,Field
import base64




with open("D:/estimate/files/A170147.jpeg", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode("utf-8")

client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
completion = client.chat.completions.create(
    model="qwen-vl-plus",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "提取下面九个字段：编号、单号、等级、材料、QCR、尺寸、易损件、数量、外发编号,以json格式返回。"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
        ]
    }]
)
print(completion.model_dump_json())