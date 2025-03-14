# 基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件到镜像中
COPY . /app

# 安装依赖
RUN pip install -r requirements.txt

# 安装项目所需的其他依赖
RUN pip install fastapi uvicorn

# 暴露端口
EXPOSE 8000

# 启动应用
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "443"]