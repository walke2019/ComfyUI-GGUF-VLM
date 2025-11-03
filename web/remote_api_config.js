/**
 * ComfyUI-GGUF-VLM Remote API Config 前端扩展
 * 支持动态刷新模型列表
 */

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// 注册节点扩展
app.registerExtension({
    name: "ComfyUI.GGUF-VLM.RemoteAPIConfig",
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // 只处理 RemoteAPIConfig 节点
        if (nodeData.name === "RemoteAPIConfig") {
            
            // 添加刷新按钮到节点
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                const result = onNodeCreated?.apply(this, arguments);
                
                // 找到 model widget 的索引
                const modelWidgetIndex = this.widgets.findIndex(w => w.name === "model");
                
                // 在 model 后面插入刷新按钮
                const refreshButton = this.addWidget(
                    "button",
                    "🔄 Refresh Models",
                    null,
                    () => {
                        this.refreshModels();
                    }
                );
                
                // 如果找到了 model widget，将刷新按钮移到它后面
                if (modelWidgetIndex !== -1 && this.widgets.length > 1) {
                    // 移除刚添加的按钮
                    const button = this.widgets.pop();
                    // 插入到 model 后面
                    this.widgets.splice(modelWidgetIndex + 1, 0, button);
                }
                
                // 刷新模型列表的方法
                this.refreshModels = async function() {
                    console.log("🔄 Refreshing models...");
                    
                    try {
                        // 获取当前的 base_url 和 api_type
                        const baseUrlWidget = this.widgets.find(w => w.name === "base_url");
                        const apiTypeWidget = this.widgets.find(w => w.name === "api_type");
                        const modelWidget = this.widgets.find(w => w.name === "model");
                        
                        if (!baseUrlWidget || !apiTypeWidget || !modelWidget) {
                            console.error("❌ Cannot find required widgets");
                            return;
                        }
                        
                        const baseUrl = baseUrlWidget.value;
                        const apiType = apiTypeWidget.value;
                        
                        console.log(`📡 Fetching models from ${baseUrl} (${apiType})...`);
                        
                        // 调用后端 API 获取模型列表
                        const response = await fetch(`${baseUrl}/api/tags`, {
                            method: 'GET',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            timeout: 5000
                        });
                        
                        if (response.ok) {
                            const data = await response.json();
                            const models = data.models?.map(m => m.name) || [];
                            
                            if (models.length > 0) {
                                // 更新模型下拉列表
                                modelWidget.options.values = models;
                                modelWidget.value = models[0];
                                
                                console.log(`✅ Found ${models.length} models`);
                                
                                // 触发节点更新
                                this.setDirtyCanvas(true, true);
                            } else {
                                console.warn("⚠️  No models found");
                                modelWidget.options.values = ["No models found"];
                                modelWidget.value = "No models found";
                            }
                        } else {
                            console.error(`❌ Failed to fetch models: ${response.status}`);
                            modelWidget.options.values = ["Service unavailable"];
                            modelWidget.value = "Service unavailable";
                        }
                        
                    } catch (error) {
                        console.error("❌ Error refreshing models:", error);
                        const modelWidget = this.widgets.find(w => w.name === "model");
                        if (modelWidget) {
                            modelWidget.options.values = ["Service unavailable"];
                            modelWidget.value = "Service unavailable";
                        }
                    }
                };
                
                return result;
            };
        }
    }
});

console.log("✅ ComfyUI-GGUF-VLM Remote API Config extension loaded");
