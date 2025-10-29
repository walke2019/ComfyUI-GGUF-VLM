# Nexa SDK 使用示例

## 快速开始

### 1. 检查服务状态

首先使用 **Nexa Service Status** 节点检查服务是否可用：

```
输入:
- base_url: http://127.0.0.1:11434
- refresh: False

输出:
- status: "✅ Nexa SDK Service is available..."
- models: "- DavidAU/Qwen3-8B-64k-Josiefied-Uncensored-HORROR-Max-GGUF:Q6_K"
```

### 2. 基本文本生成

```
[Nexa Model Selector]
├─ model: DavidAU/Qwen3-8B-64k-Josiefied-Uncensored-HORROR-Max-GGUF:Q6_K
├─ base_url: http://127.0.0.1:11434
└─ system_prompt: "You are a helpful assistant."
    ↓
[Nexa Text Generation]
├─ prompt: "用中文介绍一下量子计算"
├─ max_tokens: 512
├─ temperature: 0.7
└─ enable_thinking: False
    ↓
输出: "量子计算是一种利用量子力学原理..."
```

### 3. 启用思考模式

对于支持思考的模型（如 DeepSeek-R1、Qwen3-Thinking）：

```
[Nexa Model Selector]
├─ model: DavidAU/Qwen3-8B-64k-Josiefied-Uncensored-HORROR-Max-GGUF:Q6_K
├─ base_url: http://127.0.0.1:11434
└─ system_prompt: ""  # 不添加 no_think
    ↓
[Nexa Text Generation]
├─ prompt: "解释相对论的基本原理"
├─ max_tokens: 1024
├─ temperature: 0.7
└─ enable_thinking: True  # 启用思考模式
    ↓
输出:
├─ output: "相对论包括狭义相对论和广义相对论..."
├─ thinking: "<think>首先需要理解时空的概念...</think>"
└─ raw_response: "{完整的 API 响应 JSON}"
```

### 4. 对话历史

使用 JSON 格式传递对话历史：

```json
[
  {"role": "user", "content": "什么是人工智能？"},
  {"role": "assistant", "content": "人工智能是..."},
  {"role": "user", "content": "它有哪些应用？"}
]
```

在 `conversation_history` 参数中粘贴上述 JSON。

## 实际应用场景

### 场景 1: 文档摘要

```
系统提示词: "You are a professional document summarizer."
用户输入: "请总结以下文档：[文档内容]"
参数:
- max_tokens: 512
- temperature: 0.3  # 较低温度，更准确
- top_p: 0.9
```

### 场景 2: 创意写作

```
系统提示词: "You are a creative writer."
用户输入: "写一个关于未来城市的科幻故事"
参数:
- max_tokens: 2048
- temperature: 1.0  # 较高温度，更有创意
- top_p: 0.95
```

### 场景 3: 代码生成

```
系统提示词: "You are an expert programmer."
用户输入: "用 Python 实现一个快速排序算法"
参数:
- max_tokens: 1024
- temperature: 0.2  # 低温度，更精确
- top_p: 0.9
```

### 场景 4: 问答系统

```
系统提示词: "You are a knowledgeable assistant. Answer questions accurately and concisely."
用户输入: "量子纠缠是什么？"
参数:
- max_tokens: 512
- temperature: 0.5
- enable_thinking: True  # 显示推理过程
```

## 高级技巧

### 1. 控制输出长度

```python
# 短回答
max_tokens = 128

# 中等长度
max_tokens = 512

# 长文本
max_tokens = 2048
```

### 2. 调整创意性

```python
# 保守/准确
temperature = 0.2

# 平衡
temperature = 0.7

# 创意/随机
temperature = 1.2
```

### 3. 多轮对话

使用 `conversation_history` 维护上下文：

```json
[
  {"role": "system", "content": "You are a helpful assistant."},
  {"role": "user", "content": "我想学习 Python"},
  {"role": "assistant", "content": "很好！Python 是一门..."},
  {"role": "user", "content": "从哪里开始？"}
]
```

### 4. 思考过程分析

启用 `enable_thinking` 后，可以：

1. 查看模型的推理步骤
2. 理解答案的生成逻辑
3. 调试复杂问题

输出示例：

```
thinking: "
<think>
首先分析问题...
考虑几种可能的方案...
选择最优解...
</think>
"

output: "最终答案是..."
```

## 性能优化建议

### 1. 批量处理

如果需要处理多个请求，可以：
- 使用相同的模型配置
- 避免频繁切换模型
- 利用 Nexa SDK 的并发能力

### 2. 缓存策略

对于重复的查询：
- 使用相同的 `temperature=0` 获得确定性输出
- 在应用层缓存结果

### 3. 超时处理

对于长文本生成：
- 增加 `max_tokens`
- 监控生成时间
- 设置合理的超时时间（当前默认 120 秒）

## 常见问题

### Q: 如何切换模型？

A: 在 **Nexa Model Selector** 节点中选择不同的模型即可，无需重启。

### Q: 思考模式不工作？

A: 确保：
1. `enable_thinking = True`
2. 系统提示词中没有 `no_think`
3. 模型支持思考输出（如 DeepSeek-R1）

### Q: 如何提高响应速度？

A: 
1. 减少 `max_tokens`
2. 使用更小的量化模型（如 Q4_K_M）
3. 降低 `temperature`

### Q: 支持流式输出吗？

A: 当前版本不支持，未来计划添加。

## 调试技巧

### 1. 查看原始响应

使用 `raw_response` 输出查看完整的 API 响应：

```json
{
  "id": "",
  "choices": [...],
  "usage": {
    "prompt_tokens": 9,
    "completion_tokens": 134,
    "total_tokens": 143
  }
}
```

### 2. 检查 token 使用

从 `raw_response` 中提取 `usage` 信息，了解：
- 输入 token 数
- 输出 token 数
- 总 token 数

### 3. 错误处理

如果生成失败，检查：
1. 服务是否可用
2. 模型是否正确
3. 参数是否合法
4. 网络连接

## 更多资源

- [Nexa SDK 文档](https://github.com/NexaAI/nexa-sdk)
- [OpenAI API 参考](https://platform.openai.com/docs/api-reference)
- [ComfyUI 官方文档](https://github.com/comfyanonymous/ComfyUI)
