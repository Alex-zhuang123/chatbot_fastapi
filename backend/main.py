from fastapi.responses import StreamingResponse
from typing import AsyncIterator
from schemas import AskInput, AskOutput
from file_handler import handle_file_upload, cleanup_temp_file
from graph import create_state_graph
from config import TEMP_DIR, logger
from fastapi import FastAPI, Depends, HTTPException, UploadFile
import os
from langchain.schema.messages import HumanMessage
from langchain_unstructured import UnstructuredLoader
app = FastAPI()

# 文件上传路由
@app.post("/upload/")
async def upload_file(file: UploadFile = Depends(handle_file_upload)):
    return file

# 使用 langserve 部署问答接口
@app.post("/ask/", response_model=AskOutput)
async def ask_question(input: AskInput):
    temp_file_path = os.path.join(TEMP_DIR, input.upload_file)
    if not os.path.exists(temp_file_path):
        logger.error(f"File not found: {temp_file_path}")
        raise HTTPException(status_code=404, detail="File not found")

    try:
        # 加载文档内容
        loader = UnstructuredLoader(file_path=temp_file_path, strategy="hi_res")
        docs = "\n".join(doc.page_content for doc in loader.lazy_load() if doc.page_content.strip())

        # 初始化状态图
        graph = create_state_graph()

        # 初始消息
        initial_messages = [
            HumanMessage(content=docs),
            HumanMessage(content=input.question)
        ]

        # 流式响应生成器
        async def event_generator():
            try:
                async for event in graph.stream({"messages": initial_messages}, config={"configurable": {"thread_id": "abc456"}}):
                    for value in event.values():
                        yield value["messages"][-1].content
            except Exception as e:
                logger.error(f"Error generating response: {e}")
                yield "An error occurred while processing your request."

        return StreamingResponse(event_generator(), media_type="text/plain")
    except Exception as e:
        logger.error(f"Error in ask_question: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        # 清理临时文件
        cleanup_temp_file(input.upload_file)

# 启动应用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)