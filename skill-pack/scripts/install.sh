#!/bin/bash
# AgentHansa Money Machine - 安装脚本
# 用法: bash install.sh

set -e

INSTALL_DIR="$HOME/.hermes/agenthansa"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 AgentHansa Money Machine 安装器"
echo "=================================="

# 创建目录
echo "📁 创建目录..."
mkdir -p "$INSTALL_DIR"/{memory,logs}

# 复制脚本
echo "📄 复制脚本..."
for f in "$SCRIPT_DIR"/*.py "$SCRIPT_DIR"/*.sh; do
    [ -f "$f" ] && cp "$f" "$INSTALL_DIR/" && echo "  ✓ $(basename "$f")"
done

# 安装依赖
echo "📦 安装Python依赖..."
pip install requests python-dotenv 2>/dev/null || {
    echo "⚠️ pip安装失败，请手动运行: pip install requests python-dotenv"
}

# 创建配置文件模板
if [ ! -f "$INSTALL_DIR/.env.agenthansa" ]; then
    echo "⚙️ 创建配置文件模板..."
    cat > "$INSTALL_DIR/.env.agenthansa" << 'EOF'
# ===== AgentHansa 配置 =====
# 必填：你的AgentHansa API Key
AGENTHANSA_API_KEY=your_api_key_here

# 可选：Telegram通知（强烈建议配置）
AGENTHANSA_TELEGRAM_TOKEN=
AGENTHANSA_TELEGRAM_CHAT_ID=

# 可选：LLM Provider Keys（用于自动提交quest）
# 免费Sonnet（推荐主力）
FREE_SONNET_KEY=
FREE_SONNET_BASE=https://newapi.lzgzxs.xyz/v1
FREE_SONNET_MODEL=claude-sonnet-4-5-20250929

# 免费Haiku（红包用）
FREE_HAIKU_KEY=
FREE_HAIKU_BASE=https://newapi.lzgzxs.xyz/v1
FREE_HAIKU_MODEL=claude-haiku-4-5-20251001
EOF
    echo "  ✓ 配置文件已创建: $INSTALL_DIR/.env.agenthansa"
    echo ""
    echo "⚠️  请编辑配置文件，填入你的API Key:"
    echo "   nano $INSTALL_DIR/.env.agenthansa"
else
    echo "  ✓ 配置文件已存在，跳过"
fi

# 设置权限
chmod +x "$INSTALL_DIR"/*.sh 2>/dev/null

echo ""
echo "✅ 安装完成！"
echo ""
echo "下一步:"
echo "  1. 编辑配置: nano $INSTALL_DIR/.env.agenthansa"
echo "  2. 填入你的AgentHansa API Key"
echo "  3. 启动系统: cd $INSTALL_DIR && bash ctl.sh start"
echo "  4. 查看状态: bash ctl.sh status"
echo ""
echo "💡 提示: API Key在 https://www.agenthansa.com 获取"
