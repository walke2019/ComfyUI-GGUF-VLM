"""Reusable prompts for production VLM workflows."""


CAPTION_STYLES = {
    "简洁": "用一句话概括主体、场景和最重要的视觉特征。",
    "详细": "详细描述主体、环境、构图、颜色、光照、材质、风格和可见文字。",
    "标签": "输出逗号分隔标签，覆盖主体、动作、服饰、场景、风格、质量词。",
    "电商": "面向商品运营，提炼商品类型、颜色、材质、卖点、使用场景。",
    "数据集": "面向训练数据集，输出稳定、客观、可复用的 caption 和 tags。",
}


def build_caption_prompt(style: str = "详细", language: str = "中文", domain: str = "通用") -> str:
    instruction = CAPTION_STYLES.get(style, CAPTION_STYLES["详细"])
    return (
        f"请使用{language}为这张{domain}生成 caption。"
        f"风格要求：{style}。{instruction} "
        "避免臆测不可见信息；如果图中有文字，请转写可辨认文字。"
    )


def build_ocr_prompt(language: str = "中文", output_format: str = "按行") -> str:
    return (
        f"请识别图像中的所有可见文字，使用{language}回答。"
        f"输出格式：{output_format}。保留原文顺序；不确定的字符用 [?] 标注。"
    )


def build_prompt_reverse_prompt(target: str = "Stable Diffusion", language: str = "English") -> str:
    return (
        f"Analyze the image and write a high-quality {target} generation prompt in {language}. "
        "Include subject, composition, lighting, color palette, style, camera/framing, details, "
        "and a short negative prompt when useful."
    )


def build_json_prompt(task: str, schema: str, language: str = "中文") -> str:
    return (
        f"任务：{task}。请使用{language}分析图像，并只输出 valid JSON。"
        f"JSON schema/字段要求：{schema}。"
        "不要输出 Markdown 代码块，不要输出解释文字；缺失信息用 null 或空数组。"
    )

