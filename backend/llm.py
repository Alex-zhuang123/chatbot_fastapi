from langchain_community.llms import Tongyi
from config import DASHSCOPE_API_KEY, MODEL_NAME, TEMPERATURE, logger

# 初始化大模型
def get_llm():
    try:
        return Tongyi(
            dashscope_api_key=DASHSCOPE_API_KEY,
            model_name=MODEL_NAME,
            temperature=TEMPERATURE
        )
    except Exception as e:
        logger.error(f"Error initializing LLM: {e}")
        raise RuntimeError("Failed to initialize the language model")
    