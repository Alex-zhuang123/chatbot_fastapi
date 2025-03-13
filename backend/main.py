from fastapi import FastAPI, HTTPException, UploadFile, Depends, File
from tempfile import mkdtemp
from typing import List
import shutil
import logging
from file_service import FileService
from config import MAX_FILE_SIZE, ALLOWED_FILE_TYPES
import os
from langchain_unstructured import UnstructuredLoader
from graph import extract_key_developments

app = FastAPI()
# 配置日志
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# 固定的临时目录路径
TEMP_DIR = os.path.join(os.getcwd(), "temp_uploads")
os.makedirs(TEMP_DIR, exist_ok=True)

# 依赖注入
def get_file_service():
    return FileService(max_size=MAX_FILE_SIZE, allowed_types=ALLOWED_FILE_TYPES)

@app.post("/upload-and-process/")
async def upload_and_process(
    files: List[UploadFile] = File(...), # 接收用户上传的文件列表
    file_service: FileService = Depends(get_file_service)
):
    temp_dir = mkdtemp()
    logger.info(f"Created temporary directory: {temp_dir}")
    try:
        # 保存上传的文件到临时目录
        save_results = await file_service.save_files(files, temp_dir)
        logger.info(f"Files saved to temporary directory: {save_results}")

        
        return await handle_file(temp_dir, save_results)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


async def handle_file(temp_dir: str, save_results: List[dict]):

    # 2. 筛选出处理成功的文件
    successful_files = [
        res['filename'] for res in save_results 
        if res.get('status') == 'success'
    ]
    
    if not successful_files:
        logger.warning("No files were successfully processed")
        return {"results": [], "message": "No valid files to process"}

    # 3. 构建文件路径并加载内容
    all_docs = []
    for filename in successful_files:
        file_path = os.path.join(temp_dir, filename)
        
        # 使用 UnstructuredLoader 异步加载文档
        try:
            loader = UnstructuredLoader(
                file_path=file_path,
                strategy="hi_res",
                splitPdfPage=True
            )
            
            async for doc in loader.alazy_load():
                all_docs.append(doc.page_content)
                
        except Exception as e:
            logger.error(f"Error loading file {filename}: {str(e)}")
            continue  # 跳过加载失败的文件

    if not all_docs:
        logger.warning("No documents were successfully loaded")
        return {"results": [], "message": "Failed to load document contents"}

    # 4. 提取关键信息
    try:
        key_developments = extract_key_developments(all_docs)
        return {
            "results": key_developments,
            "processed_files": successful_files,
            "total_processed": len(all_docs)
        }
    except Exception as e:
        logger.error(f"Data extraction failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to extract information from documents"
        )
    
# 启动应用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)