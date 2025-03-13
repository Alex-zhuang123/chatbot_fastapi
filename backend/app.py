from fastapi import FastAPI, HTTPException, UploadFile, Depends, File
from tempfile import mkdtemp
from typing import List
import shutil
import logging
from file_service import FileService
from config import MAX_FILE_SIZE, ALLOWED_FILE_TYPES
import os
from graph import extract_key_developments
import base64
import io
import asyncio
import pymupdf as fitz
from PIL import Image
import zlib

app = FastAPI()

# 配置日志
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# 依赖注入
def get_file_service():
    return FileService(max_size=MAX_FILE_SIZE, allowed_types=ALLOWED_FILE_TYPES)

# 接收上传文件的接口
@app.post("/upload-files/")
async def upload_files(
    files: List[UploadFile] = File(...),
    file_service: FileService = Depends(get_file_service)
):
    temp_dir = mkdtemp()
    logger.info(f"Created temporary directory: {temp_dir}")
    try:
        # 保存上传的文件到临时目录
        save_results = await file_service.save_files(files, temp_dir)
        logger.info(f"Files saved to temporary directory: {save_results}")
        
        # 返回保存结果和临时目录路径
        return {
            "save_results": save_results,
            "temp_dir": temp_dir
        }
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail="File upload failed")

# 处理上传文件的接口
@app.post("/process-files/")
async def process_files(temp_dir: str, save_results: List[dict]):
    try:
        # 检查临时目录是否存在
        if not os.path.exists(temp_dir) :
            raise HTTPException(400, "临时目录不存在或已过期")
        return await handle_file(temp_dir, save_results)
    except Exception as e:
        logger.error(f"File processing failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="File processing failed")
    finally:
        # 清理临时目录
        if os.path.exists(temp_dir) and temp_dir.startswith("/tmp"):
            shutil.rmtree(temp_dir, ignore_errors=True)

async def handle_file(temp_dir: str, save_results: List[dict]):
    # 筛选出处理成功的文件
    successful_files = [
        res['filename'] for res in save_results 
        if res.get('status') == 'success'
    ]
    
    if not successful_files:
        logger.warning("No files were successfully processed")
        return {"status": "failure", "data": [], "message": "No valid files to process"}
    
    failed_files = []
    all_images = []
    # 构建文件路径并加载内容
    for filename in successful_files:

        try:
            file_path = os.path.join(temp_dir, filename)
            # 打开 PDF 文件并获取总页数
            pdf_document = fitz.open(file_path)
            total_pages = len(pdf_document)

            # 创建任务列表
            tasks = []
            for page_number in range(1, total_pages + 1):
                task = asyncio.create_task(pdf_page_to_base64(file_path, page_number))
                tasks.append(task)

            # 并行执行所有任务
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 过滤成功的结果
            all_images.extend([result for result in results if result is not None])

        except Exception as e:
            logger.error(f"Error loading file {filename}: {str(e)}")
            failed_files.append({"filename": filename, "error": str(e)})
    
    if not all_images:
        logger.warning("No documents were successfully loaded")
        return {"status": "failure", "data": [], "message": "Failed to load document contents"}
    
    # 提取关键信息
    try:
        key_developments = extract_key_developments(all_images)
        return {
            "results": key_developments,
            "processed_files": successful_files,
            "failed_files": failed_files,
            "total_processed": len(all_images)
        }
    except Exception as e:
        logger.error(f"Data extraction failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to extract information from documents"
        )
    
async def pdf_page_to_base64(pdf_path: str, page_number: int):
    """
    异步函数：将 PDF 文件的指定页面转换为 Base64 编码的图片字符串。
    """
    loop = asyncio.get_event_loop()

    try:
        # 使用 run_in_executor 将阻塞的 PDF 处理操作放到线程池中执行
        pdf_document = await loop.run_in_executor(None, fitz.open, pdf_path)
        if page_number < 1 or page_number > len(pdf_document):
            raise ValueError(f"页码 {page_number} 超出范围。总页数: {len(pdf_document)}")

        page = await loop.run_in_executor(None, pdf_document.load_page, page_number - 1)
        pix = await loop.run_in_executor(None, lambda: page.get_pixmap(dpi=60))

        # 将 Pixmap 转换为 PIL 图像
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # 进一步压缩图片大小
        img.thumbnail((pix.width // 2, pix.height // 2))  # 将图片尺寸减半

        # 将图像保存到内存缓冲区
        buffer = io.BytesIO()
        # 使用 run_in_executor 执行 img.save 操作
        # 正确传递参数给 img.save
        save_args = (buffer, "JPEG")
        save_kwargs = {"optimize": True, "quality": 60}
        await loop.run_in_executor(None, lambda: img.save(*save_args, **save_kwargs))

        base64_string = base64.b64encode(buffer.getvalue()).decode("utf-8")

        # 检查 Base64 数据大小
        if len(base64_string) > 129024:  # 设置最大长度限制
            logger.warning(f"Page {page_number} is too large and will be skipped.")
            return None

        # 返回 Base64 编码的图片字符串
        return base64_string
    except Exception as e:
        logger.error(f"Error processing PDF page {page_number}: {str(e)}")
        return None
    
# 启动应用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)