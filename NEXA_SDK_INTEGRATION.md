# Nexa SDK 集成文档

## 概述

ComfyUI-GGUF-FX 现在支持通过 Nexa SDK 服务进行远程推理！这是第三种推理模式，与现有的 GGUF 和 Transformers 模式并存。

## 三种推理模式对比

| 模式 | 优势 | 适用场景 |
|------|------|----------|
| **GGUF** | 本地量化模型，内存占用小 | 资源受限环境 |
| **Transformers** | 完整 HuggingFace 模型，精度高 | 高性能需求 |
| **Nexa SDK** | 远程服务，无需本地加载模型 | 分布式推理、模型共享 |

## Nexa SDK 模式特点

### ✅ 优势

1. **无需本地模型加载** - 模型运行在 Nexa SDK 服务中
2. **资源共享** - 多个 ComfyUI 实例可共享同一个模型服务
3. **快速切换** - 无需等待模型加载时间
4. **支持思考模式** - 完整支持 DeepSeek-R1、Qwen3-Thinking 等模型的思考过程
5. **标准 OpenAI API** - 使用标准的 Chat Completion API

### 📋 要求

- Nexa SDK 服务运行在 `http://127.0.0.1:11434`（可配置）
- Python `requests` 库（已包含在 requirements.txt）

## 使用方法

### 1. 启动 Nexa SDK 服务

确保 Nexa SDK 服务正在运行：

```bash
# 检查服务状态
curl http://127.0.0.1:11434/v1/models

# 访问 API 文档
# 浏览器打开: http://127.0.0.1:11434/docs/ui/
```

### 2. 在 ComfyUI 中使用

#### 节点列表

1. **🔷 Nexa Service Status** - 检查服务状态和可用模型
2. **🔷 Nexa Model Selector** - 选择模型并配置
3. **🔷 Nexa Text Generation** - 文本生成

#### 基本工作流

```
[Nexa Model Selector] 
    ↓ (model_config)
[Nexa Text Generation]
    ↓ (output, thinking, raw_response)
[输出节点]
```

### 3. 节点参数说明

#### Nexa Model Selector

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `model` | 从 Nexa SDK 服务中选择模型 | - |
| `base_url` | Nexa SDK 服务地址 | `http://127.0.0.1:11434` |
| `system_prompt` | 系统提示词（可选） | - |

#### Nexa Text Generation

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `model` | 模型配置（来自 Selector） | - |
| `prompt` | 用户输入 | - |
| `max_tokens` | 最大生成 token 数 | 512 |
| `temperature` | 温度参数（0-2） | 0.7 |
| `top_p` | Top-p 采样 | 0.9 |
| `top_k` | Top-k 采样（0 禁用） | 40 |
| `repetition_penalty` | 重复惩罚 | 1.1 |
| `enable_thinking` | 启用思考模式 | False |
| `conversation_history` | 对话历史（JSON 格式） | - |

#### 输出

1. **output** - 最终生成的文本（已移除思考标签）
2. **thinking** - 提取的思考过程（如果启用）
3. **raw_response** - 完整的 API 响应（JSON 格式）

## 思考模式

### 支持的格式

Nexa SDK 模式支持以下思考标签格式：

1. `<think>...</think>` - DeepSeek-R1 格式
2. `<thinking>...</thinking>` - 通用格式
3. `[THINKING]...[/THINKING]` - 方括号格式

### 使用示例

```python
# 启用思考模式
enable_thinking = True

# 输出会自动分离
output = "最终答案"
thinking = "思考过程..."
```

### 禁用思考

设置 `enable_thinking = False` 会自动在系统提示词中添加 `no_think`，指示模型不输出思考过程。

## API 端点

Nexa SDK 使用标准的 OpenAI 兼容 API：

### 获取模型列表

```bash
GET http://127.0.0.1:11434/v1/models
```

### 聊天补全

```bash
POST http://127.0.0.1:11434/v1/chat/completions
Content-Type: application/json

{
  "model": "model-id",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello"}
  ],
  "max_tokens": 512,
  "temperature": 0.7
}
```

## 测试

运行测试脚本验证集成：

```bash
python3 /workspace/test_nexa_simple.py
```

测试内容：
1. ✅ 服务可用性检查
2. ✅ 获取模型列表
3. ✅ 文本生成
4. ✅ 聊天补全
5. ✅ 思考模式检测

## 故障排除

### 服务不可用

**问题**: `❌ Nexa SDK Service is not available`

**解决方案**:
1. 检查服务是否运行: `curl http://127.0.0.1:11434/v1/models`
2. 确认端口号正确（默认 11434）
3. 检查防火墙设置

### 没有可用模型

**问题**: `⚠️ No Models Found`

**解决方案**:
1. 确保 Nexa SDK 服务中已加载模型
2. 点击 "Refresh" 按钮刷新模型列表
3. 检查服务日志

### 请求超时

**问题**: `Request timeout`

**解决方案**:
1. 增加 `max_tokens` 参数（减少生成长度）
2. 检查模型是否过大导致推理缓慢
3. 考虑使用更小的量化模型

## 架构说明

### 文件结构

```
ComfyUI-GGUF-FX/
├── core/
│   └── inference/
│       ├── nexa_engine.py          # Nexa SDK 推理引擎
│       ├── transformers_engine.py  # Transformers 引擎
│       └── ...
├── nodes/
│   ├── nexa_text_node.py          # Nexa SDK 节点
│   ├── text_node.py               # GGUF 文本节点
│   └── ...
└── __init__.py                    # 节点注册
```

### 核心组件

1. **NexaInferenceEngine** (`core/inference/nexa_engine.py`)
   - HTTP 客户端，调用 Nexa SDK API
   - 模型列表缓存
   - 错误处理和超时控制

2. **NexaModelSelector** (`nodes/nexa_text_node.py`)
   - 动态获取可用模型
   - 配置管理

3. **NexaTextGeneration** (`nodes/nexa_text_node.py`)
   - 文本生成逻辑
   - 思考过程提取
   - 对话历史管理

## 性能优化

### 推荐配置

- **短文本生成**: `max_tokens=256`, `temperature=0.7`
- **长文本生成**: `max_tokens=2048`, `temperature=0.8`
- **代码生成**: `max_tokens=1024`, `temperature=0.2`
- **创意写作**: `max_tokens=2048`, `temperature=1.0`

### 并发处理

Nexa SDK 服务支持并发请求，多个 ComfyUI 工作流可以同时使用同一个模型服务。

## 未来计划

- [ ] 支持流式输出（Streaming）
- [ ] 支持视觉语言模型（VLM）
- [ ] 支持函数调用（Function Calling）
- [ ] 添加更多采样参数
- [ ] 性能监控和日志

## 相关链接

- [Nexa SDK GitHub](https://github.com/NexaAI/nexa-sdk)
- [ComfyUI-GGUF-FX 主页](https://github.com/your-repo)
- [OpenAI API 文档](https://platform.openai.com/docs/api-reference)

## 许可证

与主项目相同的许可证。
