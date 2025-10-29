# Nexa SDK 集成更新 v2.0

## 🎉 新功能

### 1. ComfyUI 路径集成

**所有 GGUF 模型现在统一存放在 ComfyUI 的 `/models/LLM` 目录下！**

- ✅ 自动使用 `PathConfig.get_llm_models_path()`
- ✅ 与其他 ComfyUI 模型目录保持一致
- ✅ 支持本地 GGUF 文件管理
- ✅ 自动创建目录（如果不存在）

**默认路径**:
```
/workspace/ComfyUI/models/LLM/
```

### 2. 可配置 API 端点

**API 端点地址现在完全可配置！**

在所有 Nexa SDK 节点中，你可以自定义：
- `base_url`: Nexa SDK 服务地址
- `models_dir`: 本地模型目录

**支持的端点格式**:
```
http://127.0.0.1:11434      # 默认本地
http://localhost:11434      # localhost
http://192.168.1.100:11434  # 局域网
http://remote-server:11434  # 远程服务器
```

### 3. 双模式支持

现在支持两种模型来源：

#### 远程模式 (Remote)
- 使用 Nexa SDK 服务中已加载的模型
- 无需本地存储
- 适合快速测试和共享模型

#### 本地模式 (Local)
- 使用 `/models/LLM` 目录中的 `.gguf` 文件
- 完全本地化
- 适合离线使用和模型管理

## 📋 节点更新

### 🔷 Nexa Model Selector (更新)

**新增参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `base_url` | STRING | `http://127.0.0.1:11434` | **可配置** API 端点 |
| `models_dir` | STRING | `/workspace/ComfyUI/models/LLM` | **可配置** 本地模型目录 |
| `model_source` | CHOICE | `Remote (Nexa Service)` | 模型来源选择 |
| `refresh_models` | BOOLEAN | `False` | 刷新模型列表 |
| `system_prompt` | STRING | - | 系统提示词（可选）|

**输出**:
- `model_config`: 模型配置（传递给 Generation 节点）
- `available_models`: 可用模型列表（文本显示）

### 🔷 Nexa Text Generation (更新)

**新增功能**:
- ✅ 自动识别本地/远程模型
- ✅ 本地模型路径自动转换
- ✅ 文件存在性检查
- ✅ 详细的错误提示

**使用方式**:

**远程模型**:
```
model: "DavidAU/Qwen3-8B-64k-Josiefied-Uncensored-HORROR-Max-GGUF:Q6_K"
```

**本地模型**:
```
model: "my-model.gguf"
或
model: "my-model"  # 自动添加 .gguf 后缀
```

### 🔷 Nexa Service Status (更新)

**新增输出**:
- `status`: 服务状态摘要
- `remote_models`: 远程模型列表
- `local_models`: 本地模型列表

## 🚀 使用示例

### 示例 1: 使用远程模型

```
[Nexa Model Selector]
├─ base_url: http://127.0.0.1:11434
├─ models_dir: /workspace/ComfyUI/models/LLM
├─ model_source: Remote (Nexa Service)
└─ system_prompt: "You are a helpful assistant."
    ↓
[Nexa Text Generation]
├─ model: "DavidAU/Qwen3-8B-64k-Josiefied-Uncensored-HORROR-Max-GGUF:Q6_K"
└─ prompt: "Hello"
```

### 示例 2: 使用本地 GGUF 模型

**步骤 1**: 将 GGUF 文件放到 `/workspace/ComfyUI/models/LLM/`

```bash
cp my-model.gguf /workspace/ComfyUI/models/LLM/
```

**步骤 2**: 在 ComfyUI 中使用

```
[Nexa Model Selector]
├─ base_url: http://127.0.0.1:11434
├─ models_dir: /workspace/ComfyUI/models/LLM
├─ model_source: Local (GGUF File)
└─ refresh_models: True  # 刷新列表
    ↓
[Nexa Text Generation]
├─ model: "my-model.gguf"  # 或 "my-model"
└─ prompt: "Hello"
```

### 示例 3: 使用自定义端点

```
[Nexa Model Selector]
├─ base_url: http://192.168.1.100:8080  # 自定义端点
├─ models_dir: /custom/path/to/models   # 自定义目录
├─ model_source: Remote (Nexa Service)
└─ system_prompt: ""
```

### 示例 4: 检查服务状态

```
[Nexa Service Status]
├─ base_url: http://127.0.0.1:11434
├─ models_dir: /workspace/ComfyUI/models/LLM
└─ refresh: True
    ↓
输出:
├─ status: "✅ Service is AVAILABLE..."
├─ remote_models: "- model1\n- model2"
└─ local_models: "- local1.gguf\n- local2.gguf"
```

## 🏗️ 架构改进

### 路径管理

```python
# 引擎层自动处理路径
engine = get_nexa_engine(
    base_url="http://127.0.0.1:11434",
    models_dir="/workspace/ComfyUI/models/LLM"
)

# 本地模型自动转换
model = "my-model.gguf"
# → /workspace/ComfyUI/models/LLM/my-model.gguf
```

### 多端点支持

```python
# 支持多个不同的服务实例
engine1 = get_nexa_engine("http://127.0.0.1:11434")
engine2 = get_nexa_engine("http://localhost:8080")
# 每个端点独立管理
```

### 智能模型识别

```python
# 自动识别模型类型
if model.endswith('.gguf'):
    # 本地模型
    path = engine.get_model_path(model)
else:
    # 远程模型 ID
    path = model
```

## 📁 目录结构

```
ComfyUI/
└── models/
    └── LLM/                    # 统一的 LLM 模型目录
        ├── model1.gguf         # Nexa SDK 本地模型
        ├── model2.gguf
        └── transformers-model/ # Transformers 模型（如果有）
```

## 🔧 配置说明

### 默认配置

如果你使用默认配置，无需任何修改：

```python
base_url = "http://127.0.0.1:11434"
models_dir = "/workspace/ComfyUI/models/LLM"
```

### 自定义配置

如果需要自定义，在节点中修改：

```python
# 自定义 API 端点
base_url = "http://your-server:port"

# 自定义模型目录
models_dir = "/your/custom/path"
```

## ✅ 测试验证

运行测试脚本：

```bash
python3 /workspace/test_nexa_paths.py
```

**测试内容**:
- ✅ 路径配置
- ✅ 可配置端点
- ✅ 本地模型路径处理
- ✅ 完整集成

**测试结果**: 全部通过 ✅

## 🎯 优势

### vs 之前版本

| 特性 | v1.0 | v2.0 |
|------|------|------|
| API 端点 | 硬编码 | ✅ 可配置 |
| 模型目录 | 未指定 | ✅ ComfyUI 标准路径 |
| 本地模型 | 不支持 | ✅ 完整支持 |
| 路径管理 | 手动 | ✅ 自动化 |

### 实际好处

1. **统一管理** - 所有 LLM 模型在一个目录
2. **灵活部署** - 支持本地/远程/混合模式
3. **易于配置** - 所有参数可在节点中调整
4. **更好的兼容性** - 与 ComfyUI 生态系统集成

## 📝 迁移指南

### 从 v1.0 迁移

**无需任何修改！**

v2.0 完全向后兼容，默认配置与 v1.0 行为一致。

### 使用新功能

1. **使用本地模型**:
   - 将 `.gguf` 文件放到 `/workspace/ComfyUI/models/LLM/`
   - 在 Model Selector 中选择 "Local (GGUF File)"
   - 在 Text Generation 中输入文件名

2. **使用自定义端点**:
   - 在 Model Selector 的 `base_url` 参数中输入新地址
   - 其他配置保持不变

## 🐛 故障排除

### 本地模型找不到

**问题**: `❌ Local model not found`

**解决方案**:
1. 检查文件是否在正确目录: `/workspace/ComfyUI/models/LLM/`
2. 确认文件扩展名是 `.gguf`
3. 点击 `refresh_models` 刷新列表

### 自定义端点连接失败

**问题**: `❌ Service is not available`

**解决方案**:
1. 检查 URL 格式是否正确
2. 确认服务正在运行
3. 检查防火墙和网络设置
4. 使用 `curl` 测试连接: `curl http://your-url/v1/models`

### 路径权限问题

**问题**: 无法创建目录或写入文件

**解决方案**:
1. 检查目录权限
2. 确保 ComfyUI 有写入权限
3. 手动创建目录: `mkdir -p /workspace/ComfyUI/models/LLM`

## 🔮 未来计划

- [ ] 自动下载远程模型到本地
- [ ] 模型版本管理
- [ ] 批量模型操作
- [ ] 模型性能监控
- [ ] 缓存优化

## 📚 相关文档

- [NEXA_SDK_INTEGRATION.md](./NEXA_SDK_INTEGRATION.md) - 完整集成文档
- [NEXA_EXAMPLE.md](./NEXA_EXAMPLE.md) - 使用示例
- [Nexa SDK GitHub](https://github.com/NexaAI/nexa-sdk)

---

**更新日期**: 2025-10-29  
**版本**: v2.0  
**状态**: ✅ 已测试并验证
