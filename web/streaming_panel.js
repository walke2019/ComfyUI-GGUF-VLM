/**
 * ComfyUI-GGUF-VLM Streaming UI foundation.
 * Adds prompt/output widgets to Remote Vision/Text config nodes and streams
 * /gguf-vlm/stream-chat deltas directly into the node.
 */

import { app } from "../../scripts/app.js";

const STREAMING_CONFIG_NODES = ["RemoteAPIConfig", "RemoteVisionModelConfig"];

async function streamChat(payload, onDelta) {
    const response = await fetch("/gguf-vlm/stream-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    if (!response.ok || !response.body) {
        throw new Error(`Streaming request failed: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() || "";
        for (const event of events) {
            if (!event.startsWith("data: ")) continue;
            const delta = event.slice(6);
            if (delta === "[DONE]") return;
            onDelta(delta);
        }
    }
}

app.registerExtension({
    name: "ComfyUI.GGUF-VLM.StreamingPanel",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (!STREAMING_CONFIG_NODES.includes(nodeData.name)) return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = onNodeCreated?.apply(this, arguments);

            if (!this.widgets.find((w) => w.name === "Streaming Prompt")) {
                this.addWidget(
                    "text",
                    "Streaming Prompt",
                    "Say hello in one short sentence.",
                    () => {},
                    { multiline: true }
                );
            }

            let outputWidget = this.widgets.find((w) => w.name === "Streaming Output");
            if (!outputWidget) {
                outputWidget = this.addWidget(
                    "text",
                    "Streaming Output",
                    "",
                    () => {},
                    { multiline: true }
                );
            }

            this.size = [
                Math.max(this.size?.[0] || 300, 420),
                Math.max(this.size?.[1] || 260, 420),
            ];
            app.graph?.setDirtyCanvas(true, true);

            this.addWidget("button", "▶️ Test Stream", null, async () => {
                const baseUrlWidget = this.widgets.find((w) => w.name === "base_url");
                const apiTypeWidget = this.widgets.find((w) => w.name === "api_type");
                const modelWidget = this.widgets.find((w) => w.name === "model");
                const promptWidget = this.widgets.find((w) => w.name === "Streaming Prompt");
                outputWidget = this.widgets.find((w) => w.name === "Streaming Output");

                const payload = {
                    base_url: baseUrlWidget?.value || "http://127.0.0.1:1234",
                    api_type: apiTypeWidget?.value || "openai",
                    model: modelWidget?.value || "",
                    prompt: promptWidget?.value || "Say hello in one short sentence.",
                    max_tokens: 128,
                    temperature: 0.2,
                };

                let output = "";
                outputWidget.value = "⏳ Streaming...";
                app.graph?.setDirtyCanvas(true, true);
                await streamChat(payload, (delta) => {
                    output += delta;
                    outputWidget.value = output;
                    app.graph?.setDirtyCanvas(true, true);
                });
                outputWidget.value = output || "(empty response)";
                app.graph?.setDirtyCanvas(true, true);
            });

            return result;
        };
    },
});
