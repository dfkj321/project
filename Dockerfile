FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建配置目录
RUN mkdir -p config

# 配置环境变量
ENV DB_HOST=rm-7xv4m6fn2cxl3c327jo.mysql.rds.aliyuncs.com
ENV DB_USER=hucongyanRoot
ENV DB_PASSWORD=Hu123456
ENV DB_DATABASE=stock_analysis
ENV DB_PORT=3306

# 暴露端口
EXPOSE 8501

# 添加健康检查
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# 设置启动命令
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"] 