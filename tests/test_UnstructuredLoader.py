from langchain_unstructured import UnstructuredLoader
import os
import asyncio
from fastapi import HTTPException
from config import TEMP_DIR
from config import logger
from graph import extract_key_developments

async def process_file(filename: str):
        temp_file_path = os.path.join(TEMP_DIR, filename)
        logger.info(f"Processing file: {temp_file_path}")

        try:
            # 文件存在性检查
            if not os.path.exists(temp_file_path):
                raise HTTPException(404, f"文件 {filename} 未找到")
            
            # 异步加载文档（假设 UnstructuredLoader 支持异步）
            loader = UnstructuredLoader(
                file_path=temp_file_path,
                strategy="hi_res",
                splitPdfPage=True
            )
            docs_local = []
            async for doc in loader.alazy_load():  # 假设存在异步迭代器
                docs_local.append(doc.page_content)
            result =  extract_key_developments(docs_local)
            logger.info(f"文件 {filename} 处理成功")
            return result

        except HTTPException as e:
            logger.error(f"HTTP异常: {str(e)}")
            raise 
        except Exception as e:
            logger.error(f"处理文件 {filename} 失败: {str(e)}", exc_info=True)
            raise HTTPException(500, "内部服务器错误")

async def main():
    await process_file("6a5bfdfc-8312-43d9-b894-80a2271d904d.txt")

if __name__ == "__main__":
    asyncio.run(main())