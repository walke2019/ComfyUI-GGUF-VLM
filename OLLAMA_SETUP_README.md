# Ollama + GGUF 快速安装指南

## 🚀 一键安装

```bash
cd /workspace
chmod +x setup_ollama_gguf.sh
./setup_ollama_gguf.sh
```

## 📋 脚本功能

✅ **自动安装 Ollama**
- 下载并安装最新版本
- 配置到 `/workspace/ollama` 目录

✅ **导入 GGUF 模型**
- 自动扫描 ComfyUI 模型目录
- 交互式选择要导入的模型
- 自动创建 Ollama 模型

✅ **启动服务**
- 后台运行 Ollama 服务
- 默认端口: 11434
- 自动测试连接

✅ **创建管理脚本**
- `start.sh` - 启动服务
- `stop.sh` - 停止服务
- `status.sh` - 查看状态
- `test.sh` - 测试模型

✅ **可选 systemd 服务**
- 开机自启动
- 自动重启

## 📊 安装流程

```
1. 检查环境
   └─ 扫描 GGUF 模型文件

2. 安装 Ollama
   └─ 下载并安装到系统

3. 配置目录
   └─ 创建 /workspace/ollama

4. 启动服务
   └─ 后台运行，端口 11434

5. 导入模型
   └─ 选择 GGUF 文件创建模型

6. 验证测试
   └─ 测试模型生成

7. 创建管理脚本
   └─ 方便日常管理

8. 完成
   └─ 显示使用说明
```

## 🎯 使用示例

### 安装过程

```bash
$ ./setup_ollama_gguf.sh

================================
检查环境
================================
ℹ️  可用的 GGUF 模型:
  [0] Huihui-Qwen3-4B-Instruct-2507-abliterated.Q8_0.gguf (4.0G)
  [1] Qwen3-8B-64k-Josiefied-Uncensored-HORROR-Max.Q6_K.gguf (6.9G)
✅ 环境检查完成

================================
安装 Ollama
================================
ℹ️  开始安装 Ollama...
✅ Ollama 安装成功

================================
配置 Ollama 目录
================================
✅ Ollama 目录创建完成: /workspace/ollama

================================
启动 Ollama 服务
================================
✅ Ollama 服务已启动 (PID: 12345)

================================
创建 GGUF 模型
================================
请输入模型编号 (0-1): 0
ℹ️  选择的模型: Huihui-Qwen3-4B-Instruct-2507-abliterated.Q8_0.gguf
ℹ️  Ollama 模型名称: huihui-qwen3-4b-instruct-2507-abliterated-q8-0
✅ 模型创建成功

================================
安装完成
================================
🎉 Ollama + GGUF 安装完成！
```

### 日常管理

```bash
# 启动服务
/workspace/ollama/start.sh

# 停止服务
/workspace/ollama/stop.sh

# 查看状态
/workspace/ollama/status.sh

# 测试模型
/workspace/ollama/test.sh
```

### 手动操作

```bash
# 列出所有模型
ollama list

# 运行模型
ollama run huihui-qwen3-4b-instruct-2507-abliterated-q8-0

# 删除模型
ollama rm <model-name>

# 查看服务日志
tail -f /tmp/ollama.log
```

## 🔧 在 ComfyUI 中使用

### 1. 添加节点

右键 → 搜索 "Unified" → 添加：
- 🤖 Unified Text Model Selector
- 🤖 Unified Text Generation

### 2. 配置 Model Selector

```
mode: Remote (API)
base_url: http://127.0.0.1:11434
api_type: Ollama
remote_model: huihui-qwen3-4b-instruct-2507-abliterated-q8-0
```

### 3. 配置 Text Generation

```
prompt: "Write a short story about a robot"
max_tokens: 512
temperature: 0.7
```

### 4. 连接并运行

```
[Unified Text Model Selector] → [Unified Text Generation]
```

## 📁 目录结构

```
/workspace/ollama/
├── models/              # Ollama 模型存储
├── start.sh            # 启动脚本
├── stop.sh             # 停止脚本
├── status.sh           # 状态脚本
└── test.sh             # 测试脚本

/workspace/ComfyUI/models/LLM/GGUF/
└── *.gguf              # 原始 GGUF 文件

/tmp/
├── ollama.log          # 服务日志
└── Modelfile_*         # 临时 Modelfile
```

## 🔄 添加更多模型

### 方法 1: 重新运行脚本

```bash
./setup_ollama_gguf.sh
# 选择不同的 GGUF 文件
```

### 方法 2: 手动创建

```bash
# 1. 创建 Modelfile
cat > /tmp/Modelfile << EOF
FROM /workspace/ComfyUI/models/LLM/GGUF/your-model.gguf
PARAMETER temperature 0.7
PARAMETER top_p 0.9
EOF

# 2. 创建模型
ollama create your-model-name -f /tmp/Modelfile

# 3. 验证
ollama list
```

## 🐛 故障排除

### 服务无法启动

```bash
# 检查端口占用
netstat -tlnp | grep 11434

# 查看日志
cat /tmp/ollama.log

# 强制停止并重启
pkill -9 ollama
/workspace/ollama/start.sh
```

### 模型创建失败

```bash
# 检查 GGUF 文件
ls -lh /workspace/ComfyUI/models/LLM/GGUF/

# 检查文件权限
chmod 644 /workspace/ComfyUI/models/LLM/GGUF/*.gguf

# 手动测试
ollama create test-model -f /tmp/Modelfile
```

### 连接被拒绝

```bash
# 检查服务状态
/workspace/ollama/status.sh

# 测试连接
curl http://127.0.0.1:11434/api/tags

# 检查防火墙
iptables -L | grep 11434
```

## 📊 性能优化

### GPU 加速

Ollama 自动使用 GPU，无需额外配置。

检查 GPU 使用：
```bash
watch -n 1 nvidia-smi
```

### 内存管理

```bash
# 设置最大模型数量（环境变量）
export OLLAMA_MAX_LOADED_MODELS=1

# 设置 GPU 内存限制
export OLLAMA_GPU_MEMORY_FRACTION=0.8
```

### 并发请求

Ollama 支持并发请求，但受限于 GPU 显存。

## 🔐 安全建议

### 仅本地访问

默认配置仅监听 `127.0.0.1`，外部无法访问。

如需外部访问：
```bash
export OLLAMA_HOST="0.0.0.0:11434"
```

⚠️ **警告**: 外部访问需要配置防火墙和认证！

### 模型隔离

每个模型独立存储，互不影响。

## 📚 参考资料

- [Ollama 官方文档](https://github.com/ollama/ollama)
- [Ollama API 文档](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [GGUF 格式说明](https://github.com/ggerganov/llama.cpp)
- [ComfyUI-GGUF-FX](https://github.com/weekii/ComfyUI-GGUF-FX)

## ❓ 常见问题

### Q: 可以同时运行多个模型吗？

A: 可以，但受限于 GPU 显存。建议一次只运行一个大模型。

### Q: 如何更新 Ollama？

A: 重新运行安装脚本，选择重新安装。

### Q: 模型文件存储在哪里？

A: `/workspace/ollama/models/` 目录下。

### Q: 如何删除不需要的模型？

A: `ollama rm <model-name>`

### Q: 支持哪些 GGUF 量化格式？

A: 支持所有 GGUF 格式（Q2_K, Q3_K, Q4_K, Q5_K, Q6_K, Q8_0 等）

### Q: 可以使用 HuggingFace 的模型吗？

A: 可以，先下载 GGUF 文件到 ComfyUI 模型目录，然后运行脚本。

---

**快速、简单、自动化！** 🎉
