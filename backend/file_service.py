import os
import logging
from uuid import uuid4
from typing import List
from fastapi import HTTPException, UploadFile
from aiofiles import os as async_os
from aiofiles import open as aio_open
import asyncio

logger = logging.getLogger(__name__)

class FileService:
    def __init__(self, max_size: int, allowed_types: list):
        self.max_size = max_size
        self.allowed_types = allowed_types
        

    async def save_files(self, files: List[UploadFile], temp_dir: str) -> List[dict]:
        """
        并发保存多个文件
        """

        os.makedirs(temp_dir, exist_ok=True)
        logger.info(f"Created temporary directory: {temp_dir}")

        if len(files) > 100:
            raise HTTPException(400, "最多上传100个文件")
        
        # 创建并发任务
        tasks = [self._save_single_file(file, temp_dir) for file in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for file, res in zip(files, results):
            if isinstance(res, Exception):
                processed_results.append({"filename": file.filename, "status": "failed", "reason": str(res)})
                logger.error(f"Failed to process file {file.filename}: {str(res)}")
            else:
                processed_results.append(res)

        return processed_results
    
    async def _save_single_file(self, file: UploadFile, temp_dir: str) -> dict:
        """
        保存单个文件，包括大小检查、类型检查和文件写入。
        """
        try:
            # 检查文件大小
            await self._check_file_size(file)

            # 检查文件类型
            await self._check_file_type(file)

            # 生成安全文件名
            safe_name = f"{uuid4().hex[:8]}.{file.filename.split('.')[-1].lower()}"
            file_path = os.path.join(temp_dir, safe_name)

            # 写入文件内容
            async with aio_open(file_path, "wb") as f:
                while content := await file.read(10240):  # 每次读取 10KB
                    await f.write(content)

            return {"filename": safe_name, "size": file.size, "status": "success"}

        except Exception as e:
            logger.error(f"文件 {file.filename} 处理失败: {str(e)}")
            raise e  # 抛出异常，由调用方处理
    async def _check_file_size(self, file: UploadFile):
        """
        检查文件大小是否超过限制。
        """
        if file.size > self.max_size:
            raise HTTPException(400, f"文件 {file.filename} 超过大小限制") #

    async def _check_file_type(self, file: UploadFile):
        """
        检查文件类型是否允许。
        """
        if file.content_type not in self.allowed_types:
            raise HTTPException(400, f"文件 {file.filename} 类型不支持")