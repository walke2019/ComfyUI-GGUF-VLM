#!/bin/bash

################################################################################
# Ollama + GGUF 模型快速安装脚本
# 
# 功能:
# - 安装 Ollama 到 /workspace/ollama
# - 从现有 GGUF 文件创建 Ollama 模型
# - 配置并启动 Ollama 服务
# - 测试模型是否正常工作
#
# 使用方法:
#   chmod +x setup_ollama_gguf.sh
#   ./setup_ollama_gguf.sh
################################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# 配置变量
OLLAMA_DIR="/workspace/ollama"
OLLAMA_MODELS_DIR="$OLLAMA_DIR/models"
OLLAMA_PORT="11434"
COMFYUI_MODELS_DIR="/workspace/ComfyUI/models/LLM/GGUF"

################################################################################
# 1. 检查环境
################################################################################
print_header "检查环境"

# 检查是否有 root 权限
if [ "$EUID" -ne 0 ]; then 
    print_warning "建议使用 root 权限运行此脚本"
fi

# 检查 GGUF 模型目录
if [ ! -d "$COMFYUI_MODELS_DIR" ]; then
    print_error "GGUF 模型目录不存在: $COMFYUI_MODELS_DIR"
    exit 1
fi

# 列出可用的 GGUF 模型
print_info "可用的 GGUF 模型:"
GGUF_FILES=($(find "$COMFYUI_MODELS_DIR" -name "*.gguf" -type f))
if [ ${#GGUF_FILES[@]} -eq 0 ]; then
    print_error "未找到任何 GGUF 模型文件"
    exit 1
fi

for i in "${!GGUF_FILES[@]}"; do
    filename=$(basename "${GGUF_FILES[$i]}")
    size=$(du -h "${GGUF_FILES[$i]}" | cut -f1)
    echo "  [$i] $filename ($size)"
done

print_success "环境检查完成"

################################################################################
# 2. 安装 Ollama
################################################################################
print_header "安装 Ollama"

# 检查是否已安装
if command -v ollama &> /dev/null; then
    OLLAMA_VERSION=$(ollama --version 2>&1 | head -1)
    print_info "Ollama 已安装: $OLLAMA_VERSION"
    read -p "是否重新安装? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "跳过 Ollama 安装"
    else
        print_info "重新安装 Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh
    fi
else
    print_info "开始安装 Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# 验证安装
if command -v ollama &> /dev/null; then
    print_success "Ollama 安装成功"
    ollama --version
else
    print_error "Ollama 安装失败"
    exit 1
fi

################################################################################
# 3. 配置 Ollama 目录
################################################################################
print_header "配置 Ollama 目录"

# 创建目录
mkdir -p "$OLLAMA_DIR"
mkdir -p "$OLLAMA_MODELS_DIR"

print_success "Ollama 目录创建完成: $OLLAMA_DIR"

################################################################################
# 4. 停止现有 Ollama 服务
################################################################################
print_header "停止现有服务"

if pgrep -x "ollama" > /dev/null; then
    print_info "停止现有 Ollama 服务..."
    pkill -9 ollama || true
    sleep 2
fi

print_success "现有服务已停止"

################################################################################
# 5. 启动 Ollama 服务
################################################################################
print_header "启动 Ollama 服务"

# 设置环境变量
export OLLAMA_HOST="127.0.0.1:$OLLAMA_PORT"
export OLLAMA_MODELS="$OLLAMA_MODELS_DIR"

print_info "配置:"
print_info "  端口: $OLLAMA_PORT"
print_info "  模型目录: $OLLAMA_MODELS_DIR"

# 启动服务（后台运行）
nohup ollama serve > /tmp/ollama.log 2>&1 &
OLLAMA_PID=$!

print_info "等待服务启动..."
sleep 5

# 检查服务是否运行
if ps -p $OLLAMA_PID > /dev/null; then
    print_success "Ollama 服务已启动 (PID: $OLLAMA_PID)"
else
    print_error "Ollama 服务启动失败"
    cat /tmp/ollama.log
    exit 1
fi

# 测试连接
print_info "测试服务连接..."
for i in {1..10}; do
    if curl -s http://127.0.0.1:$OLLAMA_PORT/api/tags > /dev/null 2>&1; then
        print_success "服务连接成功"
        break
    fi
    if [ $i -eq 10 ]; then
        print_error "无法连接到 Ollama 服务"
        exit 1
    fi
    sleep 1
done

################################################################################
# 6. 创建 GGUF 模型
################################################################################
print_header "创建 GGUF 模型"

echo ""
print_info "请选择要导入的 GGUF 模型:"
for i in "${!GGUF_FILES[@]}"; do
    filename=$(basename "${GGUF_FILES[$i]}")
    size=$(du -h "${GGUF_FILES[$i]}" | cut -f1)
    echo "  [$i] $filename ($size)"
done

read -p "请输入模型编号 (0-$((${#GGUF_FILES[@]}-1))): " MODEL_INDEX

if [ -z "$MODEL_INDEX" ] || [ "$MODEL_INDEX" -lt 0 ] || [ "$MODEL_INDEX" -ge ${#GGUF_FILES[@]} ]; then
    print_error "无效的模型编号"
    exit 1
fi

SELECTED_GGUF="${GGUF_FILES[$MODEL_INDEX]}"
GGUF_FILENAME=$(basename "$SELECTED_GGUF")
GGUF_BASENAME="${GGUF_FILENAME%.gguf}"

print_info "选择的模型: $GGUF_FILENAME"

# 生成模型名称（小写，替换特殊字符）
MODEL_NAME=$(echo "$GGUF_BASENAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9._-]/-/g')
print_info "Ollama 模型名称: $MODEL_NAME"

# 创建 Modelfile
MODELFILE_PATH="/tmp/Modelfile_$MODEL_NAME"
cat > "$MODELFILE_PATH" << EOF
FROM $SELECTED_GGUF

# 模型参数
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1

# 系统提示词（可选）
SYSTEM """
You are a helpful AI assistant.
"""
EOF

print_success "Modelfile 已创建: $MODELFILE_PATH"

# 创建模型
print_info "开始创建 Ollama 模型..."
print_info "这可能需要几分钟，请耐心等待..."

if ollama create "$MODEL_NAME" -f "$MODELFILE_PATH"; then
    print_success "模型创建成功: $MODEL_NAME"
else
    print_error "模型创建失败"
    exit 1
fi

################################################################################
# 7. 验证模型
################################################################################
print_header "验证模型"

print_info "列出所有模型:"
ollama list

print_info "测试模型生成..."
TEST_RESPONSE=$(ollama run "$MODEL_NAME" "Say hello in one sentence" 2>&1 | head -5)
echo "$TEST_RESPONSE"

if [ -n "$TEST_RESPONSE" ]; then
    print_success "模型测试成功"
else
    print_warning "模型测试可能失败，请检查"
fi

################################################################################
# 8. 创建管理脚本
################################################################################
print_header "创建管理脚本"

# 启动脚本
cat > "$OLLAMA_DIR/start.sh" << 'EOF'
#!/bin/bash
export OLLAMA_HOST="127.0.0.1:11434"
export OLLAMA_MODELS="/workspace/ollama/models"
nohup ollama serve > /tmp/ollama.log 2>&1 &
echo "Ollama 服务已启动"
echo "PID: $(pgrep ollama)"
echo "日志: /tmp/ollama.log"
EOF

# 停止脚本
cat > "$OLLAMA_DIR/stop.sh" << 'EOF'
#!/bin/bash
pkill ollama
echo "Ollama 服务已停止"
EOF

# 状态脚本
cat > "$OLLAMA_DIR/status.sh" << 'EOF'
#!/bin/bash
if pgrep -x "ollama" > /dev/null; then
    echo "✅ Ollama 服务运行中"
    echo "PID: $(pgrep ollama)"
    echo "端口: 11434"
    echo ""
    echo "模型列表:"
    ollama list
else
    echo "❌ Ollama 服务未运行"
fi
EOF

# 测试脚本
cat > "$OLLAMA_DIR/test.sh" << EOF
#!/bin/bash
echo "测试 Ollama 服务..."
curl -s http://127.0.0.1:11434/api/tags | python3 -m json.tool

echo ""
echo "测试模型: $MODEL_NAME"
ollama run "$MODEL_NAME" "Hello, how are you?"
EOF

chmod +x "$OLLAMA_DIR"/*.sh

print_success "管理脚本已创建:"
print_info "  启动: $OLLAMA_DIR/start.sh"
print_info "  停止: $OLLAMA_DIR/stop.sh"
print_info "  状态: $OLLAMA_DIR/status.sh"
print_info "  测试: $OLLAMA_DIR/test.sh"

################################################################################
# 9. 创建 systemd 服务（可选）
################################################################################
print_header "创建系统服务（可选）"

read -p "是否创建 systemd 服务以开机自启? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cat > /etc/systemd/system/ollama.service << EOF
[Unit]
Description=Ollama Service
After=network.target

[Service]
Type=simple
User=root
Environment="OLLAMA_HOST=127.0.0.1:11434"
Environment="OLLAMA_MODELS=/workspace/ollama/models"
ExecStart=/usr/local/bin/ollama serve
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable ollama
    print_success "systemd 服务已创建并启用"
    print_info "使用 'systemctl start/stop/status ollama' 管理服务"
else
    print_info "跳过 systemd 服务创建"
fi

################################################################################
# 10. 总结
################################################################################
print_header "安装完成"

echo ""
print_success "🎉 Ollama + GGUF 安装完成！"
echo ""

print_info "📊 安装信息:"
echo "  Ollama 目录: $OLLAMA_DIR"
echo "  模型目录: $OLLAMA_MODELS_DIR"
echo "  服务端口: $OLLAMA_PORT"
echo "  服务地址: http://127.0.0.1:$OLLAMA_PORT"
echo "  模型名称: $MODEL_NAME"
echo "  日志文件: /tmp/ollama.log"

echo ""
print_info "🚀 快速开始:"
echo "  1. 测试服务: curl http://127.0.0.1:$OLLAMA_PORT/api/tags"
echo "  2. 运行模型: ollama run $MODEL_NAME"
echo "  3. 查看状态: $OLLAMA_DIR/status.sh"

echo ""
print_info "🔧 在 ComfyUI 中使用:"
echo "  1. 添加 'Unified Text Model Selector' 节点"
echo "  2. 设置参数:"
echo "     - mode: Remote (API)"
echo "     - base_url: http://127.0.0.1:$OLLAMA_PORT"
echo "     - api_type: Ollama"
echo "     - remote_model: $MODEL_NAME"
echo "  3. 连接 'Unified Text Generation' 节点"
echo "  4. 运行生成"

echo ""
print_info "📚 管理命令:"
echo "  启动服务: $OLLAMA_DIR/start.sh"
echo "  停止服务: $OLLAMA_DIR/stop.sh"
echo "  查看状态: $OLLAMA_DIR/status.sh"
echo "  测试模型: $OLLAMA_DIR/test.sh"

echo ""
print_info "📝 添加更多模型:"
echo "  1. 将 GGUF 文件放到: $COMFYUI_MODELS_DIR"
echo "  2. 重新运行此脚本"
echo "  或手动创建:"
echo "     ollama create <model-name> -f <Modelfile>"

echo ""
print_success "✨ 安装完成！享受使用 Ollama！"
