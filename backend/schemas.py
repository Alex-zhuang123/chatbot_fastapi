from pydantic import BaseModel
from typing import List

# 输入输出模型
class AskInput(BaseModel):
    upload_files: List[str]
