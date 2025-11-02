#!/bin/bash
# 手动下载 Transformers 模型脚本

echo "=================================="
echo "手动下载 Huihui-Qwen3-VL-4B 模型"
echo "=================================="
echo ""

# 检查 Git LFS
if ! command -v git-lfs &> /dev/null; then
    echo "⚠️ Git LFS 未安装，正在安装..."
    git lfs install
fi

# 设置变量
MODEL_DIR="/home/ComfyUI/models/LLM/Huihui-Qwen3-VL-4B-Instruct-abliterated"
REPO_ID="huihui-ai/Huihui-Qwen3-VL-4B-Instruct-abliterated"
REPO_URL="https://huggingface.co/$REPO_ID"

# 检查是否使用镜像
if [ -n "$HF_ENDPOINT" ]; then
    echo "🌐 使用镜像站: $HF_ENDPOINT"
    REPO_URL="${HF_ENDPOINT}/$REPO_ID"
fi

# 删除未完成的下载
echo "🧹 清理未完成的下载..."
rm -rf "$MODEL_DIR"
mkdir -p "$(dirname "$MODEL_DIR")"

echo ""
echo "📥 开始下载模型..."
echo "📦 Repository: $REPO_ID"
echo "📁 Destination: $MODEL_DIR"
echo "🔗 URL: $REPO_URL"
echo ""

# 方法1: 使用 huggingface-cli（推荐）
if command -v huggingface-cli &> /dev/null; then
    echo "✓ 使用 huggingface-cli 下载..."
    huggingface-cli download "$REPO_ID" \
      --local-dir "$MODEL_DIR" \
      --local-dir-use-symlinks False \
      --resume-download \
      --exclude "*.gguf" "GGUF/*" "*.bin" "*.msgpack"
else
    # 方法2: 使用 git clone + LFS（备用）
    echo "✓ 使用 git clone 下载（支持大文件）..."
    
    # 配置 Git LFS
    export GIT_LFS_SKIP_SMUDGE=0
    
    # Clone 仓库
    git clone "$REPO_URL" "$MODEL_DIR"
    
    cd "$MODEL_DIR"
    
    # 只拉取需要的大文件
    git lfs pull --include="*.safetensors"
    
    # 删除不需要的文件
    rm -f *.gguf *.bin *.msgpack 2>/dev/null
    rm -rf GGUF/ 2>/dev/null
    rm -rf .git/
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================="
    echo "✅ 下载完成！"
    echo "=================================="
    echo ""
    echo "📊 文件统计:"
    ls -lh "$MODEL_DIR" | grep -E "\.safetensors$|\.json$"
else
    echo ""
    echo "=================================="
    echo "❌ 下载失败"
    echo "=================================="
    echo ""
    echo "💡 建议："
    echo "1. 检查网络连接"
    echo "2. 使用镜像站: export HF_ENDPOINT=https://hf-mirror.com"
    echo "3. 重新运行此脚本"
fi
