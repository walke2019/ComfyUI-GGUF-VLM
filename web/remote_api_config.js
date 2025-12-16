/**
 * ComfyUI-GGUF-VLM 前端扩展
 * 支持动态刷新模型列表
 * 适用于: RemoteAPIConfig, RemoteVisionModelConfig, VisionModelLoader
 */

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// 远程 API 节点（需要 base_url 和 api_type）
const REMOTE_API_NODES = ["RemoteAPIConfig", "RemoteVisionModelConfig"];

// 本地模型节点（刷新本地文件）
const LOCAL_MODEL_NODES = ["VisionModelLoader"];

// 注册节点扩展
app.registerExtension({
    name: "ComfyUI.GGUF-VLM.ModelRefresh",
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // 处理远程 API 节点
        if (REMOTE_API_NODES.includes(nodeData.name)) {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                const result = onNodeCreated?.apply(this, arguments);
                
                const modelWidget = this.widgets.find(w => w.name === "model");
                const modelWidgetIndex = this.widgets.findIndex(w => w.name === "model");
                
                // 添加刷新按钮
                this.addWidget("button", "🔄 Refresh Models", null, () => {
                    this.refreshModels();
                });
                
                // 将按钮移到 model 后面
                if (modelWidgetIndex !== -1 && this.widgets.length > 1) {
                    const button = this.widgets.pop();
                    this.widgets.splice(modelWidgetIndex + 1, 0, button);
                }
                
                // 远程 API 刷新方法
                this.refreshModels = async function() {
                    try {
                        const baseUrlWidget = this.widgets.find(w => w.name === "base_url");
                        const apiTypeWidget = this.widgets.find(w => w.name === "api_type");
                        const modelWidget = this.widgets.find(w => w.name === "model");
                        
                        if (!baseUrlWidget || !apiTypeWidget || !modelWidget) {
                            console.error("❌ Cannot find required widgets");
                            return;
                        }
                        
                        const baseUrl = baseUrlWidget.value.replace(/\/$/, '');
                        const apiType = apiTypeWidget.value;
                        const apiEndpoint = `/gguf-vlm/refresh-models?base_url=${encodeURIComponent(baseUrl)}&api_type=${encodeURIComponent(apiType)}`;
                        
                        const controller = new AbortController();
                        const timeoutId = setTimeout(() => controller.abort(), 10000);
                        
                        const response = await fetch(apiEndpoint, {
                            method: 'GET',
                            signal: controller.signal
                        });
                        
                        clearTimeout(timeoutId);
                        
                        if (response.ok) {
                            const data = await response.json();
                            if (data.success && data.models && data.models.length > 0) {
                                const currentModel = modelWidget.value;
                                modelWidget.options.values = data.models;
                                modelWidget.value = data.models.includes(currentModel) ? currentModel : data.models[0];
                                this.setDirtyCanvas(true, true);
                            } else {
                                const errorMsg = data.error || "No models found";
                                modelWidget.options.values = [`⚠️ ${errorMsg}`];
                                modelWidget.value = `⚠️ ${errorMsg}`;
                                this.setDirtyCanvas(true, true);
                            }
                        } else {
                            modelWidget.options.values = [`❌ API Error ${response.status}`];
                            modelWidget.value = `❌ API Error ${response.status}`;
                            this.setDirtyCanvas(true, true);
                        }
                    } catch (error) {
                        const modelWidget = this.widgets.find(w => w.name === "model");
                        if (modelWidget) {
                            modelWidget.options.values = [error.name === 'AbortError' ? "❌ Request timeout" : "❌ Request failed"];
                            modelWidget.value = modelWidget.options.values[0];
                            this.setDirtyCanvas(true, true);
                        }
                    }
                };
                
                return result;
            };
        }
        
        // 处理本地模型节点
        if (LOCAL_MODEL_NODES.includes(nodeData.name)) {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                const result = onNodeCreated?.apply(this, arguments);
                
                const modelWidget = this.widgets.find(w => w.name === "model");
                const modelWidgetIndex = this.widgets.findIndex(w => w.name === "model");
                
                // 添加刷新按钮
                this.addWidget("button", "🔄 Refresh Local Models", null, () => {
                    this.refreshLocalModels();
                });
                
                // 将按钮移到 model 后面
                if (modelWidgetIndex !== -1 && this.widgets.length > 1) {
                    const button = this.widgets.pop();
                    this.widgets.splice(modelWidgetIndex + 1, 0, button);
                }
                
                // 本地模型刷新方法
                this.refreshLocalModels = async function() {
                    try {
                        const modelWidget = this.widgets.find(w => w.name === "model");
                        if (!modelWidget) {
                            console.error("❌ Cannot find model widget");
                            return;
                        }
                        
                        const apiEndpoint = `/gguf-vlm/refresh-local-vision-models`;
                        
                        const controller = new AbortController();
                        const timeoutId = setTimeout(() => controller.abort(), 10000);
                        
                        const response = await fetch(apiEndpoint, {
                            method: 'GET',
                            signal: controller.signal
                        });
                        
                        clearTimeout(timeoutId);
                        
                        if (response.ok) {
                            const data = await response.json();
                            if (data.success && data.models && data.models.length > 0) {
                                const currentModel = modelWidget.value;
                                modelWidget.options.values = data.models;
                                modelWidget.value = data.models.includes(currentModel) ? currentModel : data.models[0];
                                this.setDirtyCanvas(true, true);
                                console.log(`✅ Refreshed ${data.models.length} local vision models`);
                            } else {
                                const errorMsg = data.error || "No models found";
                                modelWidget.options.values = [`⚠️ ${errorMsg}`];
                                modelWidget.value = `⚠️ ${errorMsg}`;
                                this.setDirtyCanvas(true, true);
                            }
                        } else {
                            modelWidget.options.values = [`❌ API Error ${response.status}`];
                            modelWidget.value = `❌ API Error ${response.status}`;
                            this.setDirtyCanvas(true, true);
                        }
                    } catch (error) {
                        const modelWidget = this.widgets.find(w => w.name === "model");
                        if (modelWidget) {
                            modelWidget.options.values = [error.name === 'AbortError' ? "❌ Request timeout" : "❌ Request failed"];
                            modelWidget.value = modelWidget.options.values[0];
                            this.setDirtyCanvas(true, true);
                        }
                    }
                };
                
                return result;
            };
        }
    }
});
