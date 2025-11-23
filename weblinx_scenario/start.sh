#!/bin/bash

# BrowserGym WebLINX 部署脚本（带环境变量加载）

echo "🚀 BrowserGym WebLINX Benchmark 部署脚本"
echo ""

# 加载 .env 文件
if [ -f .env ]; then
    echo "📝 加载 .env 文件..."
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ 环境变量已加载"
else
    echo "⚠️  未找到 .env 文件"
    echo "请创建 .env 文件并设置 OPENAI_API_KEY"
    exit 1
fi

# 检查 OPENAI_API_KEY
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ 错误: OPENAI_API_KEY 未设置"
    echo "请在 .env 文件中设置: OPENAI_API_KEY=sk-your-key"
    exit 1
fi
echo "✅ OpenAI API Key 已设置 (${OPENAI_API_KEY:0:10}...)"

# 检查依赖
echo ""
echo "📦 检查依赖..."
pip list | grep -q agentbeats || { echo "安装 agentbeats..."; pip install agentbeats; }
pip list | grep -q datasets || { echo "安装 datasets..."; pip install datasets; }
pip list | grep -q python-dotenv || { echo "安装 python-dotenv..."; pip install python-dotenv; }

echo "✅ 所有依赖已安装"

# 检查端口
echo ""
echo "🔍 检查端口占用..."
check_port() {
    if lsof -i :$1 &> /dev/null; then
        echo "⚠️  端口 $1 已被占用"
        return 1
    else
        echo "✅ 端口 $1 可用"
        return 0
    fi
}

PORTS=(9000 9001 5173 9110 9111 9114 9115)
ALL_PORTS_AVAILABLE=true
for port in "${PORTS[@]}"; do
    check_port $port || ALL_PORTS_AVAILABLE=false
done

if [ "$ALL_PORTS_AVAILABLE" = false ]; then
    echo ""
    echo "⚠️  部分端口被占用，是否继续? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "已取消"
        exit 1
    fi
fi

echo ""
echo "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" 
echo "📝 请在不同终端运行以下命令:"
echo "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "="
echo ""
echo "🔹 终端 1 (后端):"
echo "   cd $(pwd)"
echo "   export \$(cat .env | grep -v '^#' | xargs)"
echo "   agentbeats run_backend --backend_port 9000 --mcp_port 9001"
echo ""
echo "🔹 终端 2 (前端):"
echo "   agentbeats run_frontend --frontend_port 5173 --backend_url http://localhost:9000"
echo ""
echo "🔹 终端 3 (Scenario):"
echo "   cd $(pwd)"
echo "   export \$(cat .env | grep -v '^#' | xargs)"
echo "   agentbeats run_scenario scenarios/scenario4BrowserGym \\"
echo "     --backend http://localhost:9000 \\"
echo "     --frontend http://localhost:5173 \\"
echo "     --launch_mode tmux"
echo ""
echo "🌐 前端地址: http://localhost:5173"
echo "🔧 后端地址: http://localhost:9000"
echo ""