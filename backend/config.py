import os

# 配置日志
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 临时目录路径
TEMP_DIR = './temp'

# 大模型配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
MODEL_NAME = "qwen2.5-vl-72b-instruct"
TEMPERATURE = 2