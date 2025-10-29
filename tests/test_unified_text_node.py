#!/usr/bin/env python3
"""
测试统一文本生成节点
测试 Local GGUF、Ollama API、Nexa SDK API
"""

import sys
import os

# 添加 ComfyUI 路径
sys.path.insert(0, '/workspace/ComfyUI')
sys.path.insert(0, '/workspace/ComfyUI/custom_nodes/ComfyUI-GGUF-FX')

# 模拟 folder_paths
class FolderPaths:
    models_dir = "/workspace/ComfyUI/models"
    
sys.modules['folder_paths'] = FolderPaths()

from nodes.unified_text_node import UnifiedTextModelSelector, UnifiedTextGeneration

print("="*80)
print(" 测试统一文本生成节点")
print("="*80)

# 测试 1: Ollama API
print("\n" + "="*80)
print("测试 1: Ollama API")
print("="*80)

selector = UnifiedTextModelSelector()
config, = selector.select_model(
    mode="Remote (API)",
    base_url="http://127.0.0.1:11435",
    api_type="Ollama",
    remote_model="",
    refresh_models=False,
    system_prompt="You are a helpful assistant."
)

if config.get("service_available"):
    generator = UnifiedTextGeneration()
    context, thinking = generator.generate(
        model_config=config,
        prompt="用中文介绍一下你自己，不超过50字",
        max_tokens=100,
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        repetition_penalty=1.1,
        enable_thinking=False
    )
    
    print(f"\n📝 生成结果:")
    print(f"   {context}")
else:
    print("❌ Ollama 服务不可用")

# 测试 2: Nexa SDK API
print("\n" + "="*80)
print("测试 2: Nexa SDK API")
print("="*80)

config, = selector.select_model(
    mode="Remote (API)",
    base_url="http://127.0.0.1:11434",
    api_type="Nexa SDK",
    remote_model="",
    refresh_models=False,
    system_prompt="You are a helpful assistant."
)

if config.get("service_available"):
    generator = UnifiedTextGeneration()
    context, thinking = generator.generate(
        model_config=config,
        prompt="Say hello in Chinese",
        max_tokens=50,
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        repetition_penalty=1.1,
        enable_thinking=False
    )
    
    print(f"\n📝 生成结果:")
    print(f"   {context}")
else:
    print("❌ Nexa SDK 服务不可用")

# 测试 3: Local GGUF
print("\n" + "="*80)
print("测试 3: Local GGUF")
print("="*80)

gguf_file = "Huihui-Qwen3-4B-Instruct-2507-abliterated.Q8_0.gguf"
gguf_path = f"/workspace/ComfyUI/models/LLM/GGUF/{gguf_file}"

if os.path.exists(gguf_path):
    config, = selector.select_model(
        mode="Local (GGUF)",
        local_model=gguf_file,
        n_ctx=8192,
        n_gpu_layers=-1,
        system_prompt="You are a helpful assistant."
    )
    
    if "error" not in config:
        generator = UnifiedTextGeneration()
        context, thinking = generator.generate(
            model_config=config,
            prompt="用中文说你好",
            max_tokens=50,
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            repetition_penalty=1.1,
            enable_thinking=False
        )
        
        print(f"\n📝 生成结果:")
        print(f"   {context}")
    else:
        print(f"❌ {config['error']}")
else:
    print(f"❌ GGUF 文件不存在: {gguf_path}")

print("\n" + "="*80)
print(" 测试完成!")
print("="*80)
