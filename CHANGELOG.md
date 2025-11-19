# Changelog

## [1.1.0] - 2025-11-19

### Fixed

#### Issue #3: Windows路径问题修复 (采纳 @niceqwer55555 的改进)
- ✅ 添加了`platform`模块导入以支持跨平台检测
- ✅ **采纳社区改进**：使用`os.path.abspath()`确保路径是绝对路径
- ✅ **采纳社区改进**：添加路径有效性验证（检查文件是否存在）
- ✅ **采纳社区改进**：使用`os.sep`进行路径分隔符替换，更通用
- ✅ 修复了Windows下文件URI路径格式问题
  - Windows: `file:///C:/path/to/file`
  - Linux/Mac: `file:///path/to/file`
- ✅ 自动识别操作系统并使用正确的路径格式

**贡献者**: @niceqwer55555 提供了更完善的路径处理方案  
**影响文件**: `nodes/vision_node.py`

#### Issue #5: 文本模型加载器对Qwen3模型的支持
- ✅ 改进了模型过滤逻辑，优先使用registry信息判断模型类型
- ✅ 使用更精确的VL模型匹配模式，避免误判
  - 添加了特定的视觉模型模式列表：`qwen-vl`, `qwen2-vl`, `qwen2.5-vl`, `qwen3-vl`
  - 使用模式匹配：`-vl-`, `_vl_`, `.vl.`
- ✅ 现在Qwen3 VL模型可以正确地在视觉模型加载器中显示，而不会出现在文本模型加载器中

**影响文件**: `nodes/text_node.py`

#### Issue #2: 添加Gemma3模型支持
- ✅ 在model_registry.yaml中已包含Gemma-3-4B-Abliterated模型
- ✅ 添加了Gemma3的匹配规则，支持自动识别
- ✅ 添加了Huihui-Qwen3系列模型的匹配规则
- ✅ 改进了文本模型过滤器，确保Gemma3模型正确显示

**注意**: 如果遇到蓝屏问题，可能是以下原因：
1. llama-cpp-python版本不兼容 - 建议更新到最新版本
2. GPU驱动问题 - 尝试使用CPU模式或更新显卡驱动
3. 内存不足 - 使用Memory Manager节点及时释放显存

**影响文件**: `model_registry.yaml`

#### Issue #4: 显存释放功能
- ✅ 增强了`InferenceEngine.clear_all()`方法
  - 显式删除模型对象
  - 强制垃圾回收
  - 清理GPU缓存（如果使用CUDA）
  - 显示清理前后的显存使用情况
- ✅ 新增`MemoryManagerNode`节点
  - 提供4种清理操作：
    - `Clear All Models`: 卸载所有已加载的模型
    - `Force GC`: 强制Python垃圾回收
    - `Clear GPU Cache`: 清理GPU缓存
    - `Full Cleanup`: 执行所有清理操作
  - 显示详细的清理状态和显存释放信息
  - 可以连接到工作流中任意位置触发清理

**影响文件**: 
- `core/inference_engine.py`
- `nodes/memory_manager_node.py` (新增)
- `nodes/__init__.py`

#### Issue #6: 增强错误处理和调试信息
- ✅ 改进了`InferenceEngine.load_model()`方法
  - 添加文件存在性验证
  - 显示模型文件大小
  - 显示详细的加载参数
  - 显示mmproj文件信息
  - 区分不同类型的错误（FileNotFoundError, ImportError, 通用Exception）
  - 提供完整的traceback信息
- ✅ 改进了`VisionModelLoader.load_model()`方法
  - 模型未找到时显示搜索路径
  - 显示可用模型列表（前10个）
  - 显示模型查找过程的详细日志

**影响文件**: 
- `core/inference_engine.py`
- `nodes/vision_node.py`

### Added

- 🆕 新增`MemoryManagerNode`节点用于手动管理显存和内存
- 🆕 添加了跨平台路径处理支持

### Changed

- 📝 改进了错误消息的可读性和实用性
- 📝 增加了更多调试日志输出

### Technical Details

**跨平台路径处理**:
```python
if platform.system() == 'Windows':
    img_uri = img_path.replace('\\', '/')
    if not img_uri.startswith('file:///'):
        img_uri = f"file:///{img_uri}"
else:
    img_uri = f"file://{img_path}"
```

**显存清理**:
```python
# 显式删除模型
for model_path in list(self.loaded_models.keys()):
    del self.loaded_models[model_path]

# 强制垃圾回收
gc.collect()

# 清理GPU缓存
torch.cuda.empty_cache()
torch.cuda.synchronize()
```

**模型过滤改进**:
```python
# 优先使用registry信息
model_info = registry.find_model_by_filename(model_file)
if model_info:
    business_type = model_info.get('business_type')
    if business_type == 'text_generation':
        local_models.append(model_file)
        continue
```

## Usage Examples

### 使用Memory Manager节点

1. 在ComfyUI中添加`Memory Manager (GGUF)`节点
2. 选择清理操作：
   - `Full Cleanup`: 推荐用于工作流结束后完全清理
   - `Clear All Models`: 只卸载模型，保留其他缓存
   - `Clear GPU Cache`: 只清理GPU缓存
   - `Force GC`: 只执行垃圾回收
3. 连接到工作流中需要清理的位置
4. 执行后查看输出的状态信息

### 调试模型加载问题

现在当模型加载失败时，会看到详细的错误信息：
```
❌ Model not found: your-model.gguf

📁 Searched in directories:
   - E:\aiTools\ComfyUI\models\LLM\GGUF
   - E:\aiTools\ComfyUI\models\text_encoders

💡 Available models (5):
   1. model1.gguf
   2. model2.gguf
   ...
```

这些信息可以帮助快速定位问题。
