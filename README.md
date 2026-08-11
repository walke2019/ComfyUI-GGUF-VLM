# ComfyUI-GGUF-VLM

[中文](#中文) | [English](#english)

---

<a id="中文"></a>

## 中文

ComfyUI-GGUF-VLM 是一个 **GGUF-first** 的 ComfyUI 多模态 VLM/LLM 扩展，聚焦 Qwen/GGUF、本地优先推理、LM Studio / Ollama / llama.cpp server，以及实用的 Caption、OCR、Prompt Reverse、JSON 和批量图像工作流。

> 说明：本项目不是云 API 大聚合，也不是模型 marketplace。OpenAI-compatible 是协议层，核心仍是本地/GGUF/VLM 工作流。

## 安装

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/walke2019/ComfyUI-GGUF-VLM.git
cd ComfyUI-GGUF-VLM
pip install -r requirements.txt
```

ComfyUI Portable 用户请使用 ComfyUI 自带 Python 安装依赖。

## 快速使用

### 远程模式（推荐）

```text
Remote Vision Model Config → Remote VLM Business Task ← IMAGE
```

推荐服务：

| 服务 | 默认端口 | 用途 |
|---|---:|---|
| LM Studio | 1234 | Windows / GGUF 图形化管理 |
| Ollama | 11434 | 本地模型服务 |
| llama.cpp server | 自定义 | 最新 GGUF 多模态服务 |
| OpenAI-compatible | 自定义 | 兼容协议层 |

### 本地 GGUF 模式

```text
Local Vision Model Loader (GGUF) → Local Image Analysis (GGUF) ← IMAGE
```

推荐模型目录：

```text
ComfyUI/models/LLM/GGUF/
ComfyUI/models/text_encoders/
ComfyUI/models/clip/
ComfyUI/models/clip/gguf/
```

## Nodes

### 远程 / Remote

| Node | 说明 |
|---|---|
| Remote Text Model Config | 远程文本模型配置 |
| Remote Vision Model Config | 远程视觉模型配置 |
| Text Generation | 文本生成 |
| Remote Vision Analysis | 远程视觉/纯文本分析 |

### 本地 / Local

| Node | 说明 |
|---|---|
| Local Text Model Loader (GGUF) | 本地 GGUF 文本模型加载 |
| Local Text Generation (GGUF) | 本地文本生成 |
| Local Vision Model Loader (GGUF) | 本地 GGUF 视觉模型加载 |
| Local Image Analysis (GGUF) | 本地图像/视频/纯文本分析 |
| Vision Model Loader (Transformers) | 可选 Transformers 视觉模型 |
| Multi-Image Analysis | 多图/视频帧分析 |

### 业务工作流 / Workflow

| Node | 说明 |
|---|---|
| Caption Prompt Builder | Caption / tags / dataset 提示词 |
| OCR Prompt Builder | OCR 提示词 |
| Prompt Reverse Builder | SDXL / Flux / Midjourney 反推提示词 |
| JSON Extraction Prompt Builder | 结构化 JSON 提取提示词 |
| Remote VLM Business Task | 单图 Caption/OCR/Prompt/JSON/Custom |
| Batch Remote VLM Task | IMAGE 批量 Caption/OCR/JSON/Custom |
| Dynamic Multi-Image Collector | 多图输入收集为 batch |
| Video Frame Sampler | 视频帧抽样 |
| VLM Model Advisor | 根据任务/显存/偏好推荐后端和模型 |
| JSON Result Validator | 校验 JSON 输出字段 |

## 多语言 / i18n

本项目支持 ComfyUI 官方自定义节点多语言结构：

```text
locales/en/nodeDefs.json
locales/zh/nodeDefs.json
```

当前提供英文和简体中文节点定义翻译。ComfyUI 会根据界面语言加载对应的 `nodeDefs.json`。

## 示例工作流

- `workflows/Example.json`
- `workflows/V2_Business_Example.json`

## 开发与测试

```bash
python -m unittest discover -s tests -v
python -m compileall __init__.py api_routes.py core nodes utils models config tests
```

CI 配置位于 `.github/workflows/ci.yml`。

## License

MIT

---

<a id="english"></a>

## English

ComfyUI-GGUF-VLM is a **GGUF-first** multimodal VLM/LLM extension for ComfyUI. It focuses on Qwen/GGUF, local-first inference, LM Studio / Ollama / llama.cpp server, and practical workflows such as captioning, OCR, prompt reverse, JSON extraction, and image batches.

> Note: This project is not a cloud API aggregator or a model marketplace. OpenAI-compatible is only the protocol layer; the core remains local/GGUF/VLM workflows.

## Installation

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/walke2019/ComfyUI-GGUF-VLM.git
cd ComfyUI-GGUF-VLM
pip install -r requirements.txt
```

For ComfyUI Portable, install dependencies with ComfyUI's bundled Python.

## Quick Start

### Remote Mode (recommended)

```text
Remote Vision Model Config → Remote VLM Business Task ← IMAGE
```

Recommended services:

| Service | Default Port | Use |
|---|---:|---|
| LM Studio | 1234 | Windows / GUI GGUF management |
| Ollama | 11434 | Local model service |
| llama.cpp server | custom | Latest multimodal GGUF service |
| OpenAI-compatible | custom | Protocol compatibility layer |

### Local GGUF Mode

```text
Local Vision Model Loader (GGUF) → Local Image Analysis (GGUF) ← IMAGE
```

Recommended model directories:

```text
ComfyUI/models/LLM/GGUF/
ComfyUI/models/text_encoders/
ComfyUI/models/clip/
ComfyUI/models/clip/gguf/
```

## i18n

This project uses ComfyUI's official custom node i18n structure:

```text
locales/en/nodeDefs.json
locales/zh/nodeDefs.json
```

English and Simplified Chinese node definition translations are included.

## Development

```bash
python -m unittest discover -s tests -v
python -m compileall __init__.py api_routes.py core nodes utils models config tests
```

## License

MIT
