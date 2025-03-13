import os
import tempfile
import asyncio
from unittest.mock import patch
from app import pdf_page_to_base64
import pymupdf as fitz
from app import  handle_file

temp_dir = r"D:\chatbot_fastapi\test_files"
save_results = [{"filename": "example4.txt",  "status": "success"},]

import asyncio
import logging

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 测试函数
async def test_pdf_page_to_base64():
    # 示例 PDF 文件路径（请替换为实际文件路径）
    pdf_path = r"C:\Users\86181\AppData\Local\Temp\tmpp3fyi69e\acfb95f2.pdf"
    page_number = 1  # 要提取的页面编号（从 1 开始）

    try:
        # 调用函数
        base64_image = await pdf_page_to_base64(pdf_path, page_number)

        if base64_image:
            logger.info("成功提取 Base64 图像，长度: %d", len(base64_image))
            # 打印前 50 个字符作为预览
            logger.info("Base64 图像预览: %s...", base64_image[:50])
        else:
            logger.error("提取 Base64 图像失败")
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")


# 测试 handle_file 函数
async def test_handle_file():
    temp_dir = "./test_files"

    test_pdf_path = os.path.join(temp_dir, "example3.pdf")

    # 模拟 save_results
    save_results = [
        {"filename": "example2.pdf", "status": "success"},
    ]

    try:
        # 调用 handle_file 函数
        result = await handle_file(temp_dir, save_results)
        print("Test Result:", result)

    finally:
        pass

# 运行测试
if __name__ == "__main__":
    asyncio.run(test_handle_file())