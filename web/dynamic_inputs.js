/**
 * Dynamic input helpers for v2 multi-image workflows.
 */

import { app } from "../../scripts/app.js";

const DYNAMIC_IMAGE_NODES = ["DynamicMultiImageCollector", "V2DynamicMultiImageAnalysis"];

app.registerExtension({
    name: "ComfyUI.GGUF-VLM.DynamicInputs",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (!DYNAMIC_IMAGE_NODES.includes(nodeData.name)) return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = onNodeCreated?.apply(this, arguments);

            this.addWidget("button", "➕ Add Image Input", null, () => {
                const current = (this.inputs || []).filter((input) => input.name?.startsWith("image_")).length;
                const next = current + 1;
                this.addInput(`image_${next}`, "IMAGE");
                this.size = [
                    Math.max(this.size?.[0] || 300, 360),
                    Math.max(this.size?.[1] || 180, 180 + next * 24),
                ];
                app.graph?.setDirtyCanvas(true, true);
            });

            return result;
        };
    },
});

