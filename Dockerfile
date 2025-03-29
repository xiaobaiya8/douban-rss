FROM python:3.9-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install -r requirements.txt

# 创建配置目录
RUN mkdir -p /config

# 设置环境变量
ENV CONFIG_DIR=/config

# 复制应用代码
COPY src /app/src
COPY scripts /app/scripts
COPY templates /app/templates
COPY static /app/static

EXPOSE 9150

# 启动API服务
CMD ["python", "scripts/run_api.py"] 