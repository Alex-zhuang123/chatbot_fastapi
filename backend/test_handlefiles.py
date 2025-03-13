import os
import tempfile
import asyncio
from unittest.mock import patch
from main import handle_file

temp_dir = r"D:\chatbot_fastapi\test_files"
save_results = [{"filename": "example4.txt",  "status": "success"},]

async def test_handle_file():
    return await handle_file(temp_dir, save_results)


if __name__ == "__main__":
    asyncio.run(test_handle_file())