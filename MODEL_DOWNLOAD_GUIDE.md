# 📥 模型下载指南

## ✅ 预设模型说明

插件已经预设了以下 **Abliterated (破限制)** 模型，**支持自动下载**：

### 💬 文本生成模型

| 模型 | 变体 | 大小 | 特点 |
|------|------|------|------|
| **Huihui-Qwen3-8B-Abliterated-v2** | Q8_0 ⭐ | 8.5GB | 旗舰模型，最强性能 |
| **Huihui-Qwen3-4B-Instruct-2507** | Q8_0 ⭐ | 4.0GB | 专门优化，指令微调 |
| **Gemma-3-4B-Abliterated** | Q8_0 ⭐ | 4.0GB | Google 架构，创意写作 |

⭐ = 推荐配置（全部 Q8_0 高质量版本）

## 🚀 使用方法

### 在 ComfyUI 中自动下载

1. **添加节点**: `💬 Text Model Loader (Local)`

2. **在 model 下拉菜单中**，你会看到带 `[⬇️]` 前缀的可下载模型：
   ```
   [⬇️ Abliterated Models] Huihui-Qwen3-8B-abliterated-v2.Q8_0.gguf
   [⬇️ Abliterated Models] Huihui-Qwen3-4B-Instruct-2507-abliterated.Q8_0.gguf
   [⬇️ Abliterated Models] gemma-3-4b-abliterated.Q8_0.gguf
   ```

3. **选择任意模型** → **运行工作流** → **自动下载到** `ComfyUI/models/LLM/`

4. **下载完成后**，模型会自动出现在本地模型列表中

### 手动下载（可选）

如果自动下载失败，可以手动下载：

```bash
# 进入模型目录
cd ComfyUI/models/LLM/

# 下载 Huihui-Qwen3-8B (旗舰)
wget https://huggingface.co/mradermacher/Huihui-Qwen3-8B-abliterated-v2-GGUF/resolve/main/Huihui-Qwen3-8B-abliterated-v2.Q8_0.gguf

# 或下载 Huihui-Qwen3-4B (轻量)
wget https://huggingface.co/mradermacher/Huihui-Qwen3-4B-Instruct-2507-abliterated-GGUF/resolve/main/Huihui-Qwen3-4B-Instruct-2507-abliterated.Q8_0.gguf

# 或下载 Gemma-3-4B (Google)
wget https://huggingface.co/mradermacher/gemma-3-4b-abliterated-GGUF/resolve/main/gemma-3-4b-abliterated.Q8_0.gguf
```

## 🖼️ 视觉模型

插件也预设了视觉语言模型：

| 模型 | 变体 | 大小 | 特点 |
|------|------|------|------|
| **Qwen2.5-VL-7B-NSFW** | Q4_K_M ⭐ | 4.36GB | 图像/视频描述，NSFW |
| **Qwen2-VL-7B-Abliterated** | Q4_K_M ⭐ | 4.36GB | 图像/视频理解，破限制 |

使用方法相同，在 `🖼️ Vision Model Loader (GGUF)` 节点中选择。

## ❓ 常见问题

### Q: 为什么看不到预设模型？

**A:** 
- 确保 ComfyUI 正确加载了插件
- 检查控制台是否有错误信息
- 运行 `pip install -r requirements.txt` 安装依赖
- 重启 ComfyUI

### Q: 下载速度慢怎么办？

**A:**
- 使用 HuggingFace 镜像站
- 使用手动下载方法
- 配置代理

### Q: 模型存储在哪里？

**A:** 默认路径：`ComfyUI/models/LLM/`

## 📝 配置文件

模型配置文件位置：`model_registry.yaml`

可以编辑此文件添加更多预设模型。

## 🎯 推荐配置

- **轻量**: Gemma-3-4B-Abliterated (Q8_0) - 4.0GB
- **平衡**: Huihui-Qwen3-4B-Instruct-2507 (Q8_0) - 4.0GB  
- **旗舰**: Huihui-Qwen3-8B-Abliterated-v2 (Q8_0) - 8.5GB

---

💡 **提示**: 在节点下拉菜单中选择带 `[⬇️]` 前缀的模型即可自动下载！
