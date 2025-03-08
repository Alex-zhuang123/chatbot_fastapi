from pydantic import BaseModel
from langserve import CustomUserType

# 用户问题模型
class UserQuestion(BaseModel):
    question: str

# 输入输出模型
class AskInput(CustomUserType):
    question: str
    upload_file: str

class AskOutput(CustomUserType):
    answer: str