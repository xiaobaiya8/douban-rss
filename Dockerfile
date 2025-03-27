FROM python:3.9-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制应用代码
COPY . .

# 创建配置目录
RUN mkdir -p /config

# 设置环境变量
ENV CONFIG_DIR=/config

EXPOSE 9150

CMD ["python", "api.py"] 