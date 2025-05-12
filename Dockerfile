# 使用官方 Python 镜像
FROM python:3.13-slim
LABEL authors="yangfeng"

# 设置工作目录
WORKDIR /app

# 复制当前目录内容到容器中的 /app 目录
COPY . /app

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]