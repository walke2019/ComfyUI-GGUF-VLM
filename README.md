# ComfyUI-GGUF-VLM

Complete GGUF model support for ComfyUI with local and Nexa SDK inference modes.

## 🌟 Features

### Two Inference Modes

1. **Text Generation (Local)** - Direct GGUF model loading using llama-cpp-python
2. **Nexa SDK** - Managed models via Nexa SDK service

### Key Features

- ✅ **Simple configuration** - Minimal parameters, maximum functionality
- ✅ **Auto model detection** - Nexa SDK automatically lists downloaded models
- ✅ **Thinking mode support** (DeepSeek-R1, Qwen3-Thinking)
- ✅ **Stop sequences** - Prevent over-generation
- ✅ **Paragraph merging** - Clean single-paragraph output
- ✅ **Detailed logging** - Debug-friendly console output
- ✅ **Device optimization** (CUDA, MPS, CPU)

## 📦 Installation

### 1. Install ComfyUI Custom Node

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/walke2019/ComfyUI-GGUF-VLM.git
cd ComfyUI-GGUF-VLM
pip install -r requirements.txt
```

### 2. For Nexa SDK Mode (Optional)

```bash
# Install Nexa SDK
pip install nexaai

# Start Nexa service
nexa serve
```

The service will be available at `http://127.0.0.1:11434`

## 🚀 Quick Start

### Using Text Generation (Local GGUF)

**Recommended for local GGUF files**

```
[Text Model Loader]
├─ model: Select your GGUF file
└─ device: cuda/cpu/mps
    ↓
[Text Generation]
├─ max_tokens: 256  ← Recommended for single paragraph
├─ temperature: 0.7
├─ top_p: 0.8
├─ top_k: 40
├─ repetition_penalty: 1.1
├─ enable_thinking: False
└─ prompt: "Your prompt here"
    ↓
Output: context, thinking
```

**Features:**
- ✅ Direct file access
- ✅ No service required
- ✅ Fast and simple
- ✅ Stop sequences prevent over-generation
- ✅ Automatic paragraph merging

### Using Nexa SDK Mode

**Recommended for Nexa SDK ecosystem**

#### Step 1: Download Model

```bash
# Download a model using Nexa CLI
nexa pull mradermacher/Huihui-Qwen3-4B-Instruct-2507-abliterated-GGUF:Q8_0 --model-type llm

# Check downloaded models
nexa list
```

#### Step 2: Use in ComfyUI

```
[Nexa Model Selector]
├─ base_url: http://127.0.0.1:11434
├─ refresh_models: ☐
└─ system_prompt: (optional)
    ↓
[Nexa SDK Text Generation]
├─ preset_model: Select from dropdown (auto-populated)
├─ max_tokens: 256
├─ temperature: 0.7
└─ prompt: "Your prompt here"
    ↓
Output: context, thinking
```

**Features:**
- ✅ Centralized model management
- ✅ Auto-populated model list
- ✅ Supports `nexa pull` workflow

## 📋 Available Nodes

### Text Generation Nodes (Local GGUF)

#### 🔷 Text Model Loader
Load GGUF models from `/workspace/ComfyUI/models/LLM/GGUF/`

**Parameters:**
- `model`: Select from available GGUF files
- `device`: cuda/cpu/mps
- `n_ctx`: Context window (default: 8192)
- `n_gpu_layers`: GPU layers (-1 for all)

**Output:**
- `model`: Model configuration

#### 🔷 Text Generation
Generate text with loaded GGUF model

**Parameters:**
- `model`: From Text Model Loader
- `max_tokens`: Maximum tokens (1-8192, **recommended: 256**)
- `temperature`: Temperature (0.0-2.0)
- `top_p`: Top-p sampling (0.0-1.0)
- `top_k`: Top-k sampling (0-100)
- `repetition_penalty`: Repetition penalty (1.0-2.0)
- `enable_thinking`: Enable thinking mode
- `prompt`: Input prompt (**at bottom for easy editing**)

**Outputs:**
- `context`: Generated text
- `thinking`: Thinking process (if enabled)

**Features:**
- ✅ Stop sequences: `["User:", "System:", "\n\n\n", "\n\n##", "\n\nNote:", "\n\nThis "]`
- ✅ Automatic paragraph merging for single-paragraph prompts
- ✅ Detailed console logging

### Nexa SDK Nodes

#### 🔷 Nexa Model Selector
Configure Nexa SDK service

**Parameters:**
- `base_url`: Service URL (default: `http://127.0.0.1:11434`)
- `refresh_models`: Refresh model list
- `system_prompt`: System prompt (optional)

**Output:**
- `model_config`: Configuration for Text Generation

#### 🔷 Nexa SDK Text Generation
Generate text using Nexa SDK

**Parameters:**
- `model_config`: From Model Selector
- `preset_model`: Select from dropdown (auto-populated from `nexa list`)
- `custom_model`: Custom model ID (format: `author/model:quant`)
- `auto_download`: Auto-download if missing
- `max_tokens`: Maximum tokens (**recommended: 256**)
- `temperature`, `top_p`, `top_k`, `repetition_penalty`: Generation parameters
- `enable_thinking`: Enable thinking mode
- `prompt`: Input prompt (**at bottom**)

**Outputs:**
- `context`: Generated text
- `thinking`: Thinking process (if enabled)

**Preset Models:**
- `DavidAU/Qwen3-8B-64k-Josiefied-Uncensored-HORROR-Max-GGUF:Q6_K`
- `mradermacher/Huihui-Qwen3-4B-Instruct-2507-abliterated-GGUF:Q8_0`
- `prithivMLmods/Qwen3-4B-2507-abliterated-GGUF:Q8_0`

#### 🔷 Nexa Service Status
Check Nexa SDK service status

**Parameters:**
- `base_url`: Service URL
- `refresh`: Refresh model list

**Output:**
- `status`: Service status and model list

## 🎯 Best Practices

### For Single-Paragraph Output

**System Prompt:**
```
You are an expert prompt generator. Output ONLY in English.

**CRITICAL: Output EXACTLY ONE continuous paragraph. Maximum 400 words.**
```

**Parameters:**
```
max_tokens: 256  ← Key setting!
temperature: 0.7
top_p: 0.8
top_k: 20
```

**Why max_tokens=256?**
- ✅ Prevents over-generation
- ✅ Model completes task without extra commentary
- ✅ Reduces from ~2700 chars (11 paragraphs) to ~1300 chars (1 paragraph)

### For Multi-Turn Conversations

Include history directly in prompt:
```
User: Hello
Assistant: Hi! How can I help?
User: Tell me a joke
```

No need for separate conversation history parameter.

## 💭 Thinking Mode

Automatically extracts thinking process from models like DeepSeek-R1 and Qwen3-Thinking.

**Supported Tags:**
- `<think>...</think>` (DeepSeek-R1, Qwen3)
- `<thinking>...</thinking>`
- `[THINKING]...[/THINKING]`

**Usage:**
```
[Text Generation]
├─ enable_thinking: True
└─ prompt: "Explain your reasoning"
    ↓
Outputs:
├─ context: Final answer (thinking tags removed)
└─ thinking: Extracted thinking process
```

**Disable Thinking:**
- Set `enable_thinking: False`
- Or add `no_think` to system prompt

## 📊 Mode Comparison

| Feature | Text Generation (Local) | Nexa SDK |
|---------|------------------------|----------|
| **Setup** | Copy GGUF file | `nexa pull` |
| **Service** | Not required | Requires `nexa serve` |
| **Model Management** | Manual | CLI (`nexa list`, `nexa pull`) |
| **Use Case** | Local files, production | Nexa ecosystem, shared models |
| **Speed** | Fast | Fast (via service) |
| **Flexibility** | Any GGUF file | Only `nexa pull` models |

**Recommendation:**
- Use **Text Generation** for local GGUF files
- Use **Nexa SDK** if you're already using Nexa ecosystem

## 🐛 Troubleshooting

### Output Too Long (Multiple Paragraphs)

**Problem:** Model generates 11 paragraphs instead of 1

**Solution:**
1. **Reduce max_tokens** from 512 to 256
2. **Strengthen system prompt**: Add "EXACTLY ONE paragraph"
3. Stop sequences are already configured

### Nexa Service Not Available

**Problem:** `❌ Nexa SDK service is not available`

**Solution:**
1. Start service: `nexa serve`
2. Check: `curl http://127.0.0.1:11434/v1/models`
3. Verify URL in node

### Model Not in Dropdown

**Problem:** Downloaded model doesn't appear in Nexa SDK dropdown

**Solution:**
1. Check: `nexa list`
2. Click "refresh_models" in Nexa Model Selector
3. Restart ComfyUI

### 0B Entries in `nexa list`

**Problem:** `nexa list` shows 0B entries

**Solution:**
```bash
# Clean up invalid entries
rm -rf ~/.cache/nexa.ai/nexa_sdk/models/local
rm -rf ~/.cache/nexa.ai/nexa_sdk/models/workspace
find ~/.cache/nexa.ai/nexa_sdk/models -name "*.lock" -delete

# Verify
nexa list
```

## 📁 Directory Structure

```
ComfyUI-GGUF-VLM/
├── README.md                       # This file
├── requirements.txt                # Dependencies
├── __init__.py                     # Node registration
├── config/
│   └── paths.py                    # Path configuration
├── core/
│   ├── inference_engine.py        # GGUF inference engine
│   ├── model_loader.py            # Model loader
│   └── inference/
│       ├── nexa_engine.py         # Nexa SDK engine
│       └── transformers_engine.py # Transformers engine
├── nodes/
│   ├── text_node.py               # Text Generation nodes
│   ├── nexa_text_node.py          # Nexa SDK nodes
│   ├── vision_node.py             # Vision nodes
│   └── system_prompt_node.py      # System prompt config
└── utils/
    ├── device_optimizer.py        # Device optimization
    └── system_prompts.py          # System prompt presets
```

## 🔄 Recent Updates

### v2.2 (2025-10-29)
- ✅ **Simplified Nexa Model Selector** - Removed unused `models_dir` and `model_source`
- ✅ **Removed unused outputs** - Cleaner node interface
- ✅ **Moved prompt to bottom** - Better UX for long prompts
- ✅ **Removed conversation_history** - Use prompt directly
- ✅ **Stop sequences** - Prevent over-generation
- ✅ **Paragraph merging** - Clean single-paragraph output
- ✅ **Dynamic model list** - Auto-populated from Nexa SDK API
- ✅ **Detailed logging** - Debug-friendly console output

### v2.1
- ✅ Nexa SDK integration
- ✅ Preset model list
- ✅ Thinking mode support

### v2.0
- ✅ GGUF mode with llama-cpp-python
- ✅ ComfyUI /models/LLM integration

## 📝 Requirements

```txt
llama-cpp-python>=0.2.0
transformers>=4.30.0
torch>=2.0.0
Pillow>=9.0.0
requests>=2.25.0
nexaai  # Optional, for Nexa SDK mode
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

- **Nexa SDK**: https://github.com/NexaAI/nexa-sdk
- **ComfyUI**: https://github.com/comfyanonymous/ComfyUI

