#!/bin/bash
# AI 资讯机器人 - 快速启动脚本
# 运行此脚本即可启动 AI 资讯采集和推送

echo "============================================================"
echo "🤖 AI 资讯机器人 - 启动中..."
echo "============================================================"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3，请先安装 Python"
    exit 1
fi

echo "✓ Python 环境检查通过"

# 检查依赖
echo ""
echo "📦 检查依赖包..."

python3 -c "import feedparser, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  依赖包未安装，正在安装..."
    pip3 install -q feedparser requests python-dateutil beautifulsoup4 lxml
    if [ $? -eq 0 ]; then
        echo "✓ 依赖包安装完成"
    else
        echo "❌ 依赖包安装失败，请手动运行: pip3 install feedparser requests"
        exit 1
    fi
else
    echo "✓ 依赖包检查通过"
fi

# 启动程序
echo ""
echo "============================================================"
echo "🚀 开始运行..."
echo "============================================================"
echo ""

python3 main.py

echo ""
echo "============================================================"
echo "🎉 运行完成！"
echo "============================================================"
