#!/bin/bash

echo "🚀 启动 Bedrock Chatbot 前端应用..."

cd frontend

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

# 启动前端应用
echo "🌟 启动 Streamlit 前端应用..."
streamlit run app.py --server.port 8502