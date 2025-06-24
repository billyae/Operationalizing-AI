#!/bin/bash

echo "🚀 启动 Bedrock Chatbot 后端服务..."

cd backend

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "🔧 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📦 安装依赖..."
pip install -r requirements.txt

# 启动后端服务
echo "🌟 启动 Flask 后端服务在 http://localhost:5001"
python app.py 