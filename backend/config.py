import os

# 配置日志
import logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

TEMP_DIR = os.getenv("TEMP_DIR", "temp")


# 大模型配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
if not DASHSCOPE_API_KEY:
    raise ValueError("DASHSCOPE_API_KEY environment variable is not set")

MODEL_NAME = "qwen2.5-vl-72b-instruct"
TEMPERATURE = 0.7

# 文件上传配置
MAX_FILE_SIZE =  1024 * 1024 * 10  # 10MB
ALLOWED_FILE_TYPES = ["application/pdf", "image/png", "image/jpeg","text/plain"]