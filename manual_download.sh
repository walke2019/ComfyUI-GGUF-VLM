#!/bin/bash
# 手动下载 Transformers 模型脚本

echo "=================================="
echo "手动下载 Huihui-Qwen3-VL-4B 模型"
echo "=================================="
echo ""

# 设置变量
MODEL_DIR="/home/ComfyUI/models/LLM/Huihui-Qwen3-VL-4B-Instruct-abliterated"
REPO_ID="huihui-ai/Huihui-Qwen3-VL-4B-Instruct-abliterated"

# 删除未完成的下载
echo "🧹 清理未完成的下载..."
rm -rf "$MODEL_DIR"
mkdir -p "$MODEL_DIR"

echo ""
echo "📥 开始下载模型..."
echo "📦 Repository: $REPO_ID"
echo "📁 Destination: $MODEL_DIR"
echo ""

# 使用 huggingface-cli 下载（支持断点续传）
huggingface-cli download "$REPO_ID" \
  --local-dir "$MODEL_DIR" \
  --local-dir-use-symlinks False \
  --resume-download \
  --exclude "*.gguf" "GGUF/*" "*.bin" "*.msgpack"

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
