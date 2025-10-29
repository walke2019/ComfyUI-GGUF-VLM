# ComfyUI-GGUF-FX

Enhanced Vision-Language Model nodes for ComfyUI with dual-mode support (GGUF & Transformers) and multi-image analysis capabilities.

## 🎯 Features

### Dual Mode Support
- **GGUF Mode**: Optimized quantized models for efficient inference
- **Transformers Mode**: Full HuggingFace models with complete features

### Multi-Image Analysis
- Analyze up to 6 images simultaneously
- Compare images with 7 preset comparison types
- Custom analysis with flexible prompts

### Model Support
- **Qwen3-VL Series**: 4B/8B Instruct & Thinking models
- **Quantization**: 4-bit, 8-bit, or full precision
- **Attention**: Flash Attention 2, SDPA, or Eager

## 📦 Installation

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/yourusername/ComfyUI-GGUF-FX.git
cd ComfyUI-GGUF-FX
pip install -r requirements.txt
```

## 🚀 Quick Start

### 1. Single Image Analysis

**Workflow:**
```
[Load Image] → [Vision Model Loader (Transformers)] → [Vision Language (Transformers)] → [Output]
```

**Parameters:**
- `model`: Choose Qwen3-VL model
- `quantization`: none/4bit/8bit
- `attention`: flash_attention_2 (recommended)
- `prompt`: Your analysis prompt
- `temperature`: 0.7 (default)

### 2. Multi-Image Analysis

**Workflow:**
```
[Image 1] ─┐
[Image 2] ─┼→ [Vision Model Loader] → [Multi-Image Analysis] → [Output]
[Image 3] ─┘
```

**Use Cases:**
- Product comparison
- Design evolution analysis
- Quality inspection
- Timeline analysis

### 3. Multi-Image Comparison

**Workflow:**
```
[Images] → [Vision Model Loader] → [Multi-Image Comparison] → [Output]
```

**Comparison Types:**
- `similarities`: Find common elements
- `differences`: Identify unique aspects
- `changes`: Analyze transformations
- `relationships`: Understand connections
- `sequence`: Timeline analysis
- `quality`: Technical comparison
- `style`: Artistic analysis

## 📋 Available Nodes

### GGUF Mode
1. **Vision Model Loader (GGUF)** - Load quantized models
2. **Vision Language (GGUF)** - GGUF inference

### Transformers Mode
3. **Vision Model Loader (Transformers)** - Load full models
4. **Vision Language (Transformers)** - Single image analysis

### Multi-Image
5. **Multi-Image Analysis** - Custom multi-image analysis
6. **Multi-Image Comparison** - Preset comparison types

### Configuration
7. **System Prompt Config** - Configure system prompts

## ⚙️ Configuration

### Model Loading

Models are stored in: `/ComfyUI/models/LLM/`

**Supported Models:**
- `Qwen3-VL-4B-Instruct`
- `Qwen3-VL-4B-Thinking`
- `Qwen3-VL-8B-Instruct`
- `Qwen3-VL-8B-Thinking`
- `Qwen3-VL-4B-Instruct-FP8`
- `Qwen3-VL-8B-Instruct-FP8`
- `Huihui-Qwen3-VL-8B-Instruct-abliterated`

### Generation Parameters

**Recommended (Qwen3-VL):**
```python
temperature: 0.7
top_p: 0.8
top_k: 20
repetition_penalty: 1.0
max_tokens: 16384
```

### System Prompts

Configure via `System Prompt Config` node or use defaults:
- `default`: General assistant
- `detailed`: Detailed descriptions
- `technical`: Technical analysis
- `creative`: Creative interpretations

## 💡 Best Practices

### Image Count
- **2-3 images**: Detailed comparison
- **4-6 images**: Trend analysis
- **Single image**: Use standard Vision Language node

### Temperature Settings
- **0.1-0.3**: Technical/factual analysis
- **0.5-0.7**: Balanced descriptions
- **0.8-1.2**: Creative interpretations

### Prompt Guidelines
✅ **Good:**
- "Compare the packaging design of these products, focusing on color and typography"
- "Analyze the photography techniques and composition in these images"

❌ **Avoid:**
- "Look at these images" (too vague)
- Single-word prompts

### Memory Optimization

**VRAM Usage (8B model):**
- 1 image: ~16GB
- 2 images: ~17GB
- 3 images: ~17.5GB
- 4 images: ~18GB
- 6 images: ~19GB

**Recommendations:**
- **H100 80GB**: Handle 6 images easily
- **A100 40GB**: Up to 4 images
- **Smaller GPUs**: Use 8-bit quantization

**Optimization:**
```python
quantization: "8bit"  # Saves 50% VRAM
attention: "flash_attention_2"  # Faster inference
```

## 🏗️ Project Structure

```
ComfyUI-GGUF-FX/
├── __init__.py                 # Main plugin entry
├── README.md                   # This file
├── requirements.txt            # Dependencies
├── LICENSE                     # License
├── config/
│   ├── __init__.py
│   ├── node_definitions.py    # Unified node parameters
│   └── paths.py               # Path configuration
├── core/
│   └── inference/
│       ├── gguf_engine.py     # GGUF inference
│       └── transformers_engine.py  # Transformers inference
├── nodes/
│   ├── __init__.py
│   ├── vision_node_gguf.py    # GGUF vision nodes
│   ├── vision_node_transformers.py  # Transformers vision nodes
│   ├── multi_image_node.py    # Multi-image nodes
│   ├── system_prompt_node.py  # System prompt config
│   └── text_node.py           # Text generation nodes
└── utils/
    ├── __init__.py
    ├── system_prompts.py      # System prompt manager
    └── model_manager.py       # Model management
```

## 🔧 Technical Details

### Message Format (Qwen3-VL)

The plugin uses Qwen3-VL's native message format:

```python
messages = [
    {
        "role": "user",
        "content": [
            {"type": "image", "image": "/path/to/image.png"},
            {"type": "text", "text": "Your prompt"}
        ]
    }
]
```

**Note:** System prompts are merged into user messages for compatibility.

### Image Handling

- Images are saved to temporary files
- Paths are passed directly (not `file://` URLs)
- Automatic cleanup after inference

### Model Caching

Models remain loaded between inferences unless:
- `keep_model_loaded` is set to `False`
- Different model is requested
- Manual unload is triggered

## 🐛 Troubleshooting

### Common Issues

**1. Out of Memory**
```
Solution: Use 8-bit quantization or reduce image count
```

**2. Slow Inference**
```
Solution: Enable flash_attention_2
```

**3. Model Not Found**
```
Solution: Models auto-download to /ComfyUI/models/LLM/
Check disk space (15GB+ required per model)
```

**4. Import Errors**
```
Solution: pip install -r requirements.txt
Restart ComfyUI
```

## 📊 Performance

### Inference Speed (H100 80GB)

| Configuration | Single Image | 2 Images | 4 Images |
|--------------|--------------|----------|----------|
| FP16 + FA2   | ~2s         | ~3s      | ~5s      |
| 8-bit + FA2  | ~3s         | ~4s      | ~7s      |
| 4-bit + FA2  | ~4s         | ~6s      | ~10s     |

*Times are approximate and depend on prompt length and max_tokens*

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- [Qwen Team](https://github.com/QwenLM) for the amazing Qwen3-VL models
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) for the framework
- HuggingFace for the Transformers library

## 📞 Support

- Issues: [GitHub Issues](https://github.com/yourusername/ComfyUI-GGUF-FX/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/ComfyUI-GGUF-FX/discussions)

---

**Version:** 2.0.0  
**Last Updated:** October 2025  
**Qwen3-VL Compatible:** ✅
