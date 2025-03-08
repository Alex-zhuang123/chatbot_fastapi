import os
import logging
from fastapi import HTTPException, UploadFile
from langchain_unstructured import UnstructuredLoader
from config import TEMP_DIR, logger

# 文件上传处理
async def handle_file_upload(file: UploadFile):
    os.makedirs(TEMP_DIR, exist_ok=True)
    temp_file_path = os.path.join(TEMP_DIR, file.filename)

    try:
        # 保存文件
        with open(temp_file_path, "wb") as f:
            f.write(await file.read())

        # 加载文档内容
        loader = UnstructuredLoader(file_path=temp_file_path, strategy="hi_res")
        docs = "\n".join(doc.page_content for doc in loader.lazy_load() if doc.page_content.strip())
        return {"filename": file.filename, "content_length": len(docs)}
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail="Failed to process the uploaded file")
    finally:
        # 确保文件句柄关闭
        await file.close()

# 删除临时文件
def cleanup_temp_file(filename: str):
    temp_file_path = os.path.join(TEMP_DIR, filename)
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)