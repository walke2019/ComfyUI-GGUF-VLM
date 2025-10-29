# Nexa SDK 使用指南

## 📋 概述

ComfyUI-GGUF-FX 提供两种文本生成方式：

1. **Text Generation 节点** - 使用本地 GGUF 文件（llama-cpp-python）
2. **Nexa SDK Text Generation 节点** - 使用 Nexa SDK 服务

## 🔷 Nexa SDK Text Generation 节点

### 特点
- ✅ 通过 Nexa SDK 服务管理模型
- ✅ 支持远程模型下载
- ✅ 统一的模型管理（`nexa pull`, `nexa list`, `nexa remove`）
- ✅ 自动显示已下载的模型

### 限制
- ❌ 不支持任意本地 GGUF 文件
- ❌ 需要 Nexa SDK 服务运行
- ❌ 模型必须通过 `nexa pull` 下载

## 📥 下载模型

### 方法 1：使用 Nexa SDK 格式

```bash
# 格式: author/repo-name:quant
nexa pull mradermacher/Huihui-Qwen3-4B-Instruct-2507-abliterated-GGUF:Q8_0 --model-type llm
```

### 方法 2：从 HuggingFace URL 转换

**HuggingFace URL**:
```
https://huggingface.co/mradermacher/Huihui-Qwen3-4B-Instruct-2507-abliterated-GGUF/resolve/main/Huihui-Qwen3-4B-Instruct-2507-abliterated.Q8_0.gguf
```

**提取信息**:
- Author: `mradermacher`
- Repo: `Huihui-Qwen3-4B-Instruct-2507-abliterated-GGUF`
- Quant: `Q8_0` (从文件名提取)

**Nexa 命令**:
```bash
nexa pull mradermacher/Huihui-Qwen3-4B-Instruct-2507-abliterated-GGUF:Q8_0 --model-type llm
```

## 📋 管理模型

### 查看已下载的模型
```bash
nexa list
```

### 删除模型
```bash
nexa remove <model-name>
```

### 清理所有模型
```bash
nexa clean
```

## 🚀 在 ComfyUI 中使用

### 1. 确保 Nexa SDK 服务运行

```bash
# 检查服务状态
curl http://127.0.0.1:11434/v1/models

# 如果服务未运行，启动它
nexa serve
```

### 2. 添加节点

1. **Nexa Model Selector** - 配置 Nexa SDK 服务
   - Base URL: `http://127.0.0.1:11434`（默认）

2. **Nexa SDK Text Generation** - 生成文本
   - 连接到 Model Selector
   - 从下拉菜单选择已下载的模型
   - 或输入自定义模型 ID

### 3. 模型列表

下拉菜单会自动显示：
```
- Custom (输入自定义模型 ID)

[已下载的模型 - 从 API 获取]
- DavidAU/Qwen3-8B-64k-Josiefied-Uncensored-HORROR-Max-GGUF:Q6_K
- mradermacher/Huihui-Qwen3-4B-Instruct-2507-abliterated-GGUF:Q8_0

--- Preset Models (需要 nexa pull) ---
- [参考模型列表]
```

## 🆚 Text Generation vs Nexa SDK

### 使用 Text Generation 节点（推荐用于本地文件）

**优点**:
- ✅ 支持任意 GGUF 文件
- ✅ 不需要额外服务
- ✅ 直接从 `/workspace/ComfyUI/models/LLM/GGUF/` 加载
- ✅ 更简单、更快

**适用场景**:
- 已有 GGUF 文件
- 不想使用 Nexa SDK 服务
- 需要快速测试

### 使用 Nexa SDK 节点

**优点**:
- ✅ 统一的模型管理
- ✅ 支持远程下载
- ✅ 标准化的模型格式

**适用场景**:
- 使用 Nexa SDK 生态
- 需要远程模型管理
- 团队协作（统一模型版本）

## 🐛 故障排除

### 问题 1: 400 Bad Request

**原因**: 模型未通过 `nexa pull` 下载

**解决**:
```bash
nexa pull <model-name> --model-type llm
```

### 问题 2: 模型列表为空

**原因**: Nexa SDK 服务未运行或无模型

**解决**:
```bash
# 检查服务
curl http://127.0.0.1:11434/v1/models

# 下载模型
nexa pull DavidAU/Qwen3-8B-64k-Josiefied-Uncensored-HORROR-Max-GGUF:Q6_K --model-type llm
```

### 问题 3: 出现 0B 模型

**原因**: 缓存中有无效条目

**解决**:
```bash
# 清理脚本
rm -rf ~/.cache/nexa.ai/nexa_sdk/models/local
rm -rf ~/.cache/nexa.ai/nexa_sdk/models/workspace
find ~/.cache/nexa.ai/nexa_sdk/models -name "*.lock" -delete

# 验证
nexa list
```

## 📚 推荐模型

### Abliterated (无审查) 模型

```bash
# 4B 模型（快速）
nexa pull mradermacher/Huihui-Qwen3-4B-Instruct-2507-abliterated-GGUF:Q8_0 --model-type llm

# 8B 模型（平衡）
nexa pull DavidAU/Qwen3-8B-64k-Josiefied-Uncensored-HORROR-Max-GGUF:Q6_K --model-type llm
```

## 🔗 相关链接

- [Nexa SDK 文档](https://docs.nexaai.com/)
- [HuggingFace Models](https://huggingface.co/models?search=abliterated)
- [ComfyUI-GGUF-FX GitHub](https://github.com/your-repo)

## 💡 提示

1. **首次使用**: 建议先用 Text Generation 节点测试本地 GGUF 文件
2. **模型大小**: Q8_0 质量最好，Q4_K_M 速度最快
3. **内存**: 8B 模型需要约 8-10GB RAM/VRAM
4. **下载时间**: 大模型下载可能需要几分钟，请耐心等待
