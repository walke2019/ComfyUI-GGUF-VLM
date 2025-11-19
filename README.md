# ComfyUI-GGUF-VLM

ComfyUI 的多模态模型推理插件,专注于 Qwen 系列视觉语言模型,支持多种推理后端。

## ✨ 核心功能

### 主要侧重

**🎯 视觉语言模型 (VLM)**
- **Qwen2.5-VL** / **Qwen3-VL** - 主要支持的视觉模型
- LLaVA、MiniCPM-V 等其他视觉模型
- 单图分析、多图对比、视频分析

**💬 文本生成模型**
- Qwen3、LLaMA3、DeepSeek-R1、Mistral 等
- 支持思维模式 (Thinking Mode)

### 推理方式

- ✅ **GGUF 模式** - 使用 llama-cpp-python 进行量化模型推理
- ✅ **Transformers 模式** - 使用 HuggingFace Transformers 加载完整模型
- ✅ **远程 API 模式** - 通过 Ollama、Nexa SDK、OpenAI 兼容 API 调用

### 主要特性

- ✅ **多推理后端** - GGUF、Transformers、远程 API 灵活切换
- ✅ **Qwen-VL 优化** - 针对 Qwen 视觉模型的参数优化
- ✅ **多图分析** - 最多同时分析 6 张图像
- ✅ **设备优化** - CUDA、MPS、CPU 自动检测
- ✅ **Ollama 集成** - 无缝对接 Ollama 服务

## 🤖 支持的模型

### 🎯 主要支持 (推荐)

**视觉模型:**
- **Qwen2.5-VL** (GGUF / Transformers)
- **Qwen3-VL** (GGUF / Transformers)

**文本模型:**
- Qwen3、Qwen2.5 (GGUF / Ollama)
- LLaMA-3.x (GGUF / Ollama)

### 🔧 其他支持

**视觉模型:** LLaVA、MiniCPM-V、Phi-3-Vision、InternVL 等

**文本模型:** Mistral、DeepSeek-R1、Phi-3、Gemma、Yi 等

> 💡 **推理方式:**
> - GGUF 格式 → llama-cpp-python 本地推理
> - Transformers → HuggingFace 模型加载
> - Ollama/Nexa → 远程 API 调用

## 📦 安装

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/walke2019/ComfyUI-GGUF-VLM.git
cd ComfyUI-GGUF-VLM
pip install -r requirements.txt

# 可选: 安装 Nexa SDK 支持
pip install nexaai
```

## 🚀 快速开始

### 本地 GGUF 模式

1. 将 GGUF 模型文件放到 `ComfyUI/models/LLM/GGUF/` 目录
2. 在 ComfyUI 中添加节点:
   - **Text Model Loader** - 加载模型
   - **Text Generation** - 生成文本

### 远程 API 模式

1. 启动 API 服务 (Nexa/Ollama):
   ```bash
   nexa serve  # 或 ollama serve
   ```

2. 在 ComfyUI 中添加节点:
   - **Remote API Config** - 配置 API 地址
   - **Remote Text Generation** - 生成文本

## 📋 可用节点

### 文本生成节点
- **Text Model Loader** - 加载本地 GGUF 模型
- **Text Generation** - 文本生成
- **Remote API Config** - 远程 API 配置
- **Remote Text Generation** - 远程文本生成

### 视觉分析节点
- **Vision Model Loader (GGUF)** - 加载 GGUF 视觉模型
- **Vision Model Loader (Transformers)** - 加载 Transformers 模型
- **Vision Analysis** - 单图分析
- **Multi-Image Analysis** - 多图对比分析

### 🆕 工具节点
- **Memory Manager (GGUF)** - 显存/内存管理工具
  - 清理已加载的模型
  - 强制垃圾回收
  - 清理GPU缓存
  - 显示显存使用情况

### 工具节点
- **System Prompt Config** - 系统提示词配置
- **Model Manager** - 模型管理器

## 💭 思维模式

支持 DeepSeek-R1、Qwen3-Thinking 等模型的思维过程提取。

启用 `enable_thinking` 参数后,会自动提取并分离思维过程和最终答案。

## 📁 项目结构

```
ComfyUI-GGUF-VLM/
├── config/          # 配置文件
├── core/            # 核心推理引擎
│   └── inference/   # 多后端推理实现
├── nodes/           # ComfyUI 节点定义
├── utils/           # 工具函数
└── web/             # 前端扩展
```

## 🔄 更新日志

### v1.1.0 (2025-11-19) - 社区贡献版
- ✅ **Windows路径修复** - 采纳 @niceqwer55555 的改进方案
- ✅ **显存管理** - 新增Memory Manager节点
- ✅ **Qwen3模型支持** - 改进模型过滤逻辑
- ✅ **Gemma3支持** - 添加Gemma3模型匹配规则
- ✅ **错误处理增强** - 更详细的调试信息
- 📖 详见 [CHANGELOG.md](CHANGELOG.md) 和 [COMMUNITY_CONTRIBUTIONS.md](COMMUNITY_CONTRIBUTIONS.md)

### v2.3.0
- ✅ 前端扩展 - 动态模型刷新
- ✅ 统一 API 引擎 - 支持多种 API 后端
- ✅ 标准化节点定义 - 统一参数配置
- ✅ 增强缓存管理 - 优化内存使用

## 📝 依赖

主要依赖通过 `requirements.txt` 自动安装:
- llama-cpp-python (GGUF 推理)
- transformers (Transformers 推理)
- torch (深度学习框架)
- nexaai (可选,用于 Nexa SDK)

## 🤝 社区贡献

感谢所有为项目做出贡献的开发者！

### 最近采纳的贡献
- [@niceqwer55555](https://github.com/niceqwer55555) - Windows路径修复、显存管理建议
- [@youforgetsomething](https://github.com/youforgetsomething) - Qwen3模型过滤问题反馈
- [@huansizhiying](https://github.com/huansizhiying) - Gemma3支持请求
- [@LiangWei88](https://github.com/LiangWei88) - 错误处理改进建议

📖 查看完整贡献记录: [COMMUNITY_CONTRIBUTIONS.md](COMMUNITY_CONTRIBUTIONS.md)

### 如何贡献
1. 在GitHub上创建Issue描述问题或建议
2. 提供代码示例或修复方案（如果可能）
3. 我们会审查并采纳有价值的贡献
4. 采纳后会在文档中记录并致谢

## 📄 许可证

MIT License

## 🔗 相关链接

- **Nexa SDK**: https://github.com/NexaAI/nexa-sdk
- **ComfyUI**: https://github.com/comfyanonymous/ComfyUI

