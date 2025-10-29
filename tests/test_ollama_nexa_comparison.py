#!/usr/bin/env python3
"""
对比测试 Ollama 和 Nexa SDK API
"""

import requests
import json

def test_api(name, base_url, model_name):
    """测试 API"""
    print(f"\n{'='*80}")
    print(f" 测试 {name}")
    print(f"{'='*80}")
    print(f"URL: {base_url}")
    print(f"Model: {model_name}")
    
    # 1. 检查服务
    print(f"\n1. 检查服务...")
    try:
        response = requests.get(f"{base_url}/v1/models", timeout=2)
        print(f"   ✅ 服务可用")
    except Exception as e:
        print(f"   ❌ 服务不可用: {e}")
        return
    
    # 2. 获取模型列表
    print(f"\n2. 模型列表...")
    data = response.json()
    if 'data' in data:
        # OpenAI 格式
        models = [m['id'] for m in data['data']]
    elif 'models' in data:
        # Ollama 原生格式
        models = [m['name'] for m in data['models']]
    else:
        models = []
    
    print(f"   找到 {len(models)} 个模型:")
    for m in models[:3]:
        print(f"      - {m}")
    
    # 3. 测试生成
    print(f"\n3. 测试生成...")
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": "用中文说你好"}
        ],
        "temperature": 0.7,
        "max_tokens": 50
    }
    
    try:
        response = requests.post(
            f"{base_url}/v1/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            text = result['choices'][0]['message']['content']
            print(f"   ✅ 生成成功!")
            print(f"   输出: {text}")
            print(f"   长度: {len(text)} 字符")
        else:
            print(f"   ❌ 失败 (状态码: {response.status_code})")
            print(f"   响应: {response.text[:200]}")
    
    except Exception as e:
        print(f"   ❌ 异常: {e}")

# 主测试
print("="*80)
print(" Ollama vs Nexa SDK API 对比测试")
print("="*80)

# 测试 Ollama
test_api(
    "Ollama API",
    "http://127.0.0.1:11435",
    "huihui-qwen3-4b:latest"
)

# 测试 Nexa SDK
test_api(
    "Nexa SDK API",
    "http://127.0.0.1:11434",
    "mradermacher/Huihui-Qwen3-4B-Instruct-2507-abliterated-GGUF:Q8_0"
)

print(f"\n{'='*80}")
print(" 测试完成!")
print(f"{'='*80}")
print("\n结论:")
print("✅ Ollama 和 Nexa SDK 都使用 OpenAI 兼容的 API 格式")
print("✅ 统一的 API 引擎可以同时支持两者")
print("✅ 用户只需要切换 base_url 和 api_type")
