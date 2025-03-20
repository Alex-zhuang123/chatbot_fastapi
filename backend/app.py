from fastapi import FastAPI, HTTPException, UploadFile, Depends, File, applications
from fastapi.openapi.docs import get_swagger_ui_html
from tempfile import mkdtemp
from typing import List
import shutil
import logging
from file_service import FileService
from config import MAX_FILE_SIZE, ALLOWED_FILE_TYPES
import os
from workflow import extract_key_developments
import pymupdf as fitz
import base64
from PIL import Image
import io
import asyncio

def swagger_monkey_patch(*args, **kwargs):
    """
    fastapi的swagger ui默认使用国外cdn, 所以导致文档打不开, 需要对相应方法做替换
    在应用生效前, 对swagger ui html做替换
    :param args:
    :param kwargs:
    :return:
    """
    return get_swagger_ui_html(
        *args, **kwargs,
        swagger_js_url='https://cdn.staticfile.org/swagger-ui/4.15.5/swagger-ui-bundle.min.js',  # 改用国内cdn
        swagger_css_url='https://cdn.staticfile.org/swagger-ui/4.15.5/swagger-ui.min.css'
    )


applications.get_swagger_ui_html = swagger_monkey_patch


app = FastAPI()



# 配置日志
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# 字段映射表
field_mapping = {
    "编号": "id",
    "单号": "order_number",
    "等级": "level",
    "材料": "material",
    "QCR": "qcr",
    "尺寸": "size",
    "易损件": "wear_part",
    "数量": "quantity",
    "外发编号": "external_id"
}

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
    all_images_base64 = []
    async def process_file_async(filename,temp_dir):
        file_path = os.path.join(temp_dir, filename)
        try:
            if filename.lowe().endswith(('.pdf')):
                pdf_document = fitz.open(file_path)
                total_pages = len(pdf_document)
                for page_num in range(total_pages):
                    page = pdf_document.load_page(page_num)
                    pix = page.get_pixmap(dpi=800)
                    image_bytes = pix.tobytes("png")
                    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
                    all_images_base64.append(image_base64)
                    print(f"Page {page_num + 1} of {filename} converted to base64.")
            elif filename.lower().endswith((".jpg", ".jpeg", ".png")):
                img_byte_arr = io.BytesIO()
                with Image.open(file_path) as img:
                    img.save(img_byte_arr,format=img.format)
                    img_byte_arr = img_byte_arr.getvalue()
                img_base64 = base64.b64encode(img_byte_arr).decode("utf-8")
                all_images_base64.append(img_base64)
        except Exception as e:
            error_message = f"Error processing file: {filename}. Error: {str(e)}"
            print(error_message)
            failed_files.append({"filename": filename, "error": str(e)})

    # 使用 asyncio.gather 并发处理文件
    await asyncio.gather(*[process_file_async(filename, temp_dir) for filename in successful_files])
    
    # 提取关键信息
    try:
        key_developments = await extract_key_developments(all_images_base64)

        # 调用转换函数
        converted_data = convert_fields(key_developments, field_mapping)

        return {
            "results": converted_data,
            "processed_files": successful_files,
            "failed_files": failed_files,
            "total_processed": len(all_images_base64)
        }
    except Exception as e:
        logger.error(f"Data extraction failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to extract information from documents"
        )


# 转换函数
def convert_fields(data, mapping):
    if isinstance(data, dict):
        return {mapping.get(k, k): convert_fields(v, mapping) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_fields(item, mapping) for item in data]
    elif hasattr(data, "__dict__"):
        # 如果是类实例对象，提取其属性为字典
        return convert_fields(vars(data), mapping)
    else:
        return data



                


            
# 启动应用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)