import os
import logging
from typing import List
from fastapi import HTTPException, UploadFile
from config import TEMP_DIR, logger, MAX_FILE_SIZE, ALLOWED_FILE_TYPES

logger = logging.getLogger(__name__)

# 文件上传处理
async def handle_file_uploads(files: List[UploadFile]):
    if len(files) > 100:
        raise HTTPException(status_code=400, detail="You can upload up to 100 files at once.")

    os.makedirs(TEMP_DIR, exist_ok=True)

    results = []
    for file in files:
        await check_file_size(file)
        await check_file_type(file)

        temp_file_path = os.path.join(TEMP_DIR, os.path.basename(file.filename))

        try:
            await save_file(file, temp_file_path)
            results.append({"filename": file.filename, "content_length": file.size})
        except Exception as e:
            logger.error(f"Error uploading file {file.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to process the uploaded file {file.filename}")
        finally:
            # 确保文件句柄关闭
            await file.close()

    return results


# 检查文件大小
async def check_file_size(file: UploadFile):
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File {file.filename} exceeds the size limit of {MAX_FILE_SIZE} bytes.")

# 检查文件类型
async def check_file_type(file: UploadFile):
    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(status_code=400, detail=f"File {file.filename} is not in the correct format.")


# 保存文件
async def save_file(file: UploadFile, destination: str):
    with open(destination, "wb") as f:
        while content := await file.read(1024):
            f.write(content)

# 删除临时文件
def cleanup_temp_files(filenames: List[str]):
    # 确保临时目录存在
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    for filename in filenames:
        # 提取纯文件名，防止路径逃逸
        safe_filename = os.path.basename(filename)
        temp_file_path = os.path.join(TEMP_DIR, safe_filename)
        
        try:
            # 仅删除普通文件（排除目录、符号链接等）
            if os.path.isfile(temp_file_path):
                os.remove(temp_file_path)
                logger.info(f"Deleted temp file: {temp_file_path}")
            else:
                logger.warning(f"File not found or not a regular file: {temp_file_path}")
        
        except OSError as e:
            logger.error(f"Error removing temp file {temp_file_path}: {e}")