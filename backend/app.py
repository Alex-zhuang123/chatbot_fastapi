from fastapi import FastAPI, HTTPException, UploadFile, Depends, File
from tempfile import mkdtemp
from typing import List
import shutil
import logging
from file_service import FileService
from config import MAX_FILE_SIZE, ALLOWED_FILE_TYPES
import os
from workflow import extract_key_developments
import pymupdf as fitz

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
            shutil.rmtree(temp_dir, ignore_errors=True)

async def handle_file(temp_dir: str, save_results: List[dict]):
    # 筛选出处理成功的文件
    successful_files = [
        res['filename'] for res in save_results 
        if res.get('status') == 'success'
    ]
    
    if not successful_files:
        logger.warning("No files were successfully processed")
        return {"status": "failure", "results": [], "message": "No valid files to process"}
    
    failed_files = []
    all_images = []
    subfolder_path = os.path.join(temp_dir, "pages")
    os.makedirs(subfolder_path, exist_ok=True)


    # 构建文件路径并加载内容
    for filename in successful_files:
        images_path = convert_pdf_to_images(temp_dir,subfolder_path,filename,failed_files)
        all_images.extend(images_path)
    
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

def convert_pdf_to_images(temp_dir, subfolder_path, filename, failed_files):
    """
    将单个 PDF 文件转换为图片，并保存到指定子文件夹中。
    
    :param temp_dir: PDF 文件所在的临时目录路径
    :param subfolder_path: 图片保存的目标子文件夹路径
    :param filename: PDF 文件名
    :param failed_files: 用于记录失败文件的列表
    """
    try:
        # 构建文件路径并加载 PDF 文件
        file_path = os.path.join(temp_dir, filename)
        pdf_document = fitz.open(file_path)
        total_pages = len(pdf_document)  # 获取总页数
        images_path = []
        # 遍历每一页，转换为图片并保存
        for page_number in range(total_pages):
            page = pdf_document.load_page(page_number)  # 加载页面
            pix = page.get_pixmap(dpi=300)  # 获取页面的像素图
            
            # 构造图片保存路径
            image_filename = f"page_{page_number + 1}.png"
            image_path = os.path.join(subfolder_path, image_filename)
            
            # 保存图片
            pix.save(image_path)
            images_path.append(image_path) 
            print(f"Page {page_number + 1} of {filename} saved as {image_path}")

        if not images_path:
            logger.warning("No documents were successfully loaded")
            return {"status": "failure", "data": [], "message": "Failed to load document contents"}
        
        print(f"All pages of {filename} have been successfully converted.")
        return images_path
    
    except Exception as e:
        # 记录错误信息
        error_message = f"Error loading file {filename}: {str(e)}"
        print(error_message)
        failed_files.append({"filename": filename, "error": str(e)})

    
            
# 启动应用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)