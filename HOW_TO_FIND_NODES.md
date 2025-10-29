# 如何找到统一文本生成节点

## ✅ 节点已加载

根据日志确认，统一文本节点已成功加载：
```
✅ Unified text nodes loaded
```

## 🔍 在 ComfyUI 中查找节点

### 方法 1: 搜索 "Unified"

1. 在 ComfyUI 界面中，**右键点击空白处**
2. 在搜索框中输入：`Unified`
3. 你会看到两个节点：
   - 🔷 **Unified Text Model Selector**
   - 🔷 **Unified Text Generation**

### 方法 2: 通过分类查找

1. 右键点击空白处
2. 导航到：`🤖 GGUF-Fusion` → `Text`
3. 找到：
   - 🔷 Unified Text Model Selector
   - 🔷 Unified Text Generation

### 方法 3: 搜索 "Ollama"

虽然节点名称中没有 "Ollama"，但你可以：
1. 搜索 `Unified`
2. 或搜索 `API`
3. 或搜索 `Remote`

## 📋 节点说明

### 🔷 Unified Text Model Selector

**功能**：统一的模型选择器，支持本地和远程模式

**参数**：
- **mode**: `Local (GGUF)` / `Remote (API)`
  
**Local 模式**：
- `local_model`: 选择 GGUF 文件
- `n_ctx`: 上下文窗口
- `n_gpu_layers`: GPU 层数

**Remote 模式**：
- `base_url`: API 地址（如 `http://127.0.0.1:11435`）
- `api_type`: `Ollama` / `Nexa SDK` / `OpenAI Compatible`
- `remote_model`: 模型名称

**输出**：
- `model_config`: 模型配置

### 🔷 Unified Text Generation

**功能**：统一的文本生成节点

**输入**：
- `model_config`: 从 Model Selector
- `prompt`: 提示词
- `max_tokens`, `temperature`, 等参数

**输出**：
- `context`: 生成的文本
- `thinking`: 思考过程

## 🎯 使用 Ollama 的步骤

### 1. 添加 Model Selector 节点

右键 → 搜索 `Unified` → 选择 `Unified Text Model Selector`

### 2. 配置为 Ollama 模式

在节点中设置：
- `mode`: **Remote (API)**
- `base_url`: **http://127.0.0.1:11435** (或你的 Ollama 端口)
- `api_type`: **Ollama**
- `remote_model`: 留空（自动获取）或输入模型名

### 3. 添加 Generation 节点

右键 → 搜索 `Unified` → 选择 `Unified Text Generation`

### 4. 连接节点

```
[Unified Text Model Selector]
    ↓ model_config
[Unified Text Generation]
    ↓ context
[输出节点]
```

### 5. 输入提示词并运行

在 `Unified Text Generation` 的 `prompt` 中输入你的提示词，点击运行。

## 🔧 验证节点已加载

### 方法 1: 查看日志

```bash
tail -100 /var/log/portal/comfyui.log | grep "Unified"
```

应该看到：
```
✅ Unified text nodes loaded
```

### 方法 2: API 检查

```bash
curl -s http://127.0.0.1:18188/object_info | grep -i unified
```

应该看到：
```
"UnifiedTextModelSelector"
"UnifiedTextGeneration"
```

## 💡 提示

1. **节点名称**：
   - 内部名称：`UnifiedTextModelSelector`, `UnifiedTextGeneration`
   - 显示名称：`🔷 Unified Text Model Selector`, `🔷 Unified Text Generation`

2. **搜索关键词**：
   - `Unified` ✅ 推荐
   - `API` ✅
   - `Remote` ✅
   - `Ollama` ❌ (节点名称中没有)

3. **分类路径**：
   - `🤖 GGUF-Fusion` → `Text`

## 🎬 快速开始示例

### Ollama 工作流

```
1. 添加 [Unified Text Model Selector]
   - mode: Remote (API)
   - base_url: http://127.0.0.1:11435
   - api_type: Ollama

2. 添加 [Unified Text Generation]
   - 连接 model_config
   - prompt: "用中文说你好"
   - max_tokens: 100

3. 运行工作流
```

### 本地 GGUF 工作流

```
1. 添加 [Unified Text Model Selector]
   - mode: Local (GGUF)
   - local_model: 选择你的 .gguf 文件

2. 添加 [Unified Text Generation]
   - 连接 model_config
   - prompt: "Hello"

3. 运行工作流
```

## ❓ 常见问题

### Q: 为什么搜索 "Ollama" 找不到节点？

A: 节点名称是 "Unified Text"，不包含 "Ollama"。请搜索 "Unified" 或 "API"。

### Q: 节点在哪个分类下？

A: `🤖 GGUF-Fusion` → `Text` 分类

### Q: 如何确认节点已加载？

A: 查看 ComfyUI 启动日志，应该有 `✅ Unified text nodes loaded`

### Q: 节点支持哪些 API？

A: 支持 Ollama、Nexa SDK、OpenAI Compatible 三种 API 类型

## 📚 相关文档

- [UNIFIED_API_GUIDE.md](UNIFIED_API_GUIDE.md) - 完整使用指南
- [README.md](README.md) - 项目主文档
- [NEXA_SDK_GUIDE.md](NEXA_SDK_GUIDE.md) - Nexa SDK 指南

---

**如果还是找不到节点，请检查**：
1. ComfyUI 是否已重启
2. 插件目录是否正确：`ComfyUI/custom_nodes/ComfyUI-GGUF-FX`
3. 查看启动日志是否有错误
