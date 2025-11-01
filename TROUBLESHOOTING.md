# 🔧 故障排查指南

## ❓ 问题：在 ComfyUI 中看不到预设模型

### 症状
- 节点下拉菜单中没有 `[⬇️ Abliterated Models]` 开头的模型
- 只显示 "No models found"
- 或者只显示本地已有的模型

### 解决方案

#### 1. 检查插件是否正确加载

**查看 ComfyUI 启动日志**，应该看到：
```
📦 ComfyUI-GGUF-VLM loaded: XX nodes available
   💬 Text Models: Text-to-Text generation (Qwen3, LLaMA3, etc.)
   🖼️ Vision Models: Image-Text-to-Text analysis (Qwen2.5-VL, LLaVA, etc.)
   🛠️ Tools: System prompts, model management, service status
```

如果没有看到这个信息：
- 插件可能没有正确安装
- 检查是否有 Python 错误

#### 2. 检查依赖是否安装

```bash
cd /home/ComfyUI/custom_nodes/ComfyUI-GGUF-VLM
pip install -r requirements.txt
```

必需的依赖：
- `pyyaml` - 用于读取模型配置
- `huggingface_hub` - 用于下载模型
- `tqdm` - 下载进度条

#### 3. 运行诊断脚本

```bash
cd /home/ComfyUI/custom_nodes/ComfyUI-GGUF-VLM/Test
python3 debug_node_models.py
```

应该看到：
```
✅ 配置正确！

📦 可下载模型列表 (共 3 个):
⭐ [⬇️ Abliterated Models] Huihui-Qwen3-8B-abliterated-v2.Q8_0.gguf
⭐ [⬇️ Abliterated Models] Huihui-Qwen3-4B-Instruct-2507-abliterated.Q8_0.gguf
⭐ [⬇️ Abliterated Models] gemma-3-4b-abliterated.Q8_0.gguf
```

#### 4. 检查配置文件

确认 `model_registry.yaml` 存在且格式正确：

```bash
cd /home/ComfyUI/custom_nodes/ComfyUI-GGUF-VLM
cat model_registry.yaml | grep "text_generation"
```

应该看到 `business_type: text_generation`

#### 5. 重启 ComfyUI

有时需要完全重启 ComfyUI 才能加载新配置：

```bash
# 停止 ComfyUI
# 重新启动 ComfyUI
```

#### 6. 检查 Python 路径

确保 ComfyUI 使用的 Python 环境已安装依赖：

```bash
# 查看 ComfyUI 使用的 Python
which python3

# 在该 Python 环境中安装依赖
python3 -m pip install -r requirements.txt
```

## ❓ 问题：模型下载失败

### 症状
- 选择模型后运行工作流报错
- 提示 "Failed to download model"
- 下载速度很慢或超时

### 解决方案

#### 1. 检查网络连接

```bash
# 测试是否能访问 HuggingFace
ping huggingface.co

# 或使用 curl 测试
curl -I https://huggingface.co
```

#### 2. 使用镜像站（中国用户）

编辑 `~/.bashrc` 或 `~/.zshrc`：

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

然后重启终端或：
```bash
source ~/.bashrc
```

#### 3. 手动下载

如果自动下载失败，使用手动下载：

```bash
cd /home/ComfyUI/models/LLM/

# 下载模型
wget https://huggingface.co/mradermacher/Huihui-Qwen3-8B-abliterated-v2-GGUF/resolve/main/Huihui-Qwen3-8B-abliterated-v2.Q8_0.gguf
```

#### 4. 检查磁盘空间

```bash
df -h /home/ComfyUI/models/LLM/
```

确保有足够空间（至少 10GB）

## ❓ 问题：模型加载失败

### 症状
- 模型下载成功但无法加载
- 提示 "Model not found"
- 提示 llama-cpp-python 相关错误

### 解决方案

#### 1. 检查 llama-cpp-python 安装

```bash
python3 -c "import llama_cpp; print(llama_cpp.__version__)"
```

如果报错，重新安装：

```bash
# CPU 版本
pip install llama-cpp-python

# GPU 版本 (CUDA)
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
```

#### 2. 检查模型文件完整性

```bash
cd /home/ComfyUI/models/LLM/
ls -lh *.gguf

# 检查文件大小是否正确
# Huihui-Qwen3-8B: 应该约 8.5GB
# Huihui-Qwen3-4B: 应该约 4.0GB
# Gemma-3-4B: 应该约 4.0GB
```

如果文件大小不对，重新下载。

#### 3. 检查文件权限

```bash
chmod 644 /home/ComfyUI/models/LLM/*.gguf
```

## 📞 获取帮助

如果以上方法都无法解决问题：

1. **查看 ComfyUI 控制台完整错误信息**
2. **运行诊断脚本并保存输出**：
   ```bash
   cd /home/ComfyUI/custom_nodes/ComfyUI-GGUF-VLM/Test
   python3 debug_node_models.py > debug_output.txt 2>&1
   ```
3. **检查 Python 版本**：
   ```bash
   python3 --version
   ```
4. **提供以上信息到 GitHub Issues**

## 🔍 快速诊断命令

一键运行所有诊断：

```bash
cd /home/ComfyUI/custom_nodes/ComfyUI-GGUF-VLM

echo "=== Python 版本 ==="
python3 --version

echo -e "\n=== 依赖检查 ==="
python3 -c "import yaml; import huggingface_hub; import tqdm; print('✅ 所有依赖已安装')" 2>&1

echo -e "\n=== 配置文件检查 ==="
python3 Test/debug_node_models.py

echo -e "\n=== 模型目录 ==="
ls -lh /home/ComfyUI/models/LLM/*.gguf 2>/dev/null || echo "暂无本地模型"
```

保存为 `diagnose.sh` 并运行：
```bash
chmod +x diagnose.sh
./diagnose.sh
```
