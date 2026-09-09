# El modelo no admite temperature y top-p simultáneamente

TEXT_CONFIG = {
    "resumir": {
        "temperature": 0.2,
        "max_tokens": 300
    },
    "corregir": {
        "temperature": 0.1,
        "max_tokens": 500
    },
    "expandir": {
        "temperature": 0.5,
        "max_tokens": 800
    },
    "variar": {
        "temperature": 0.8,
        "max_tokens": 800
    }
}



def build_prompt(action: str, text: str) -> str:
    action = action.lower()

    prompts = {
        "resumir": (
            "Resume el siguiente texto de forma clara y concisa, "
            "manteniendo únicamente las ideas principales y sin añadir información nueva.\n\n"
            f"Texto:\n{text}"
        ),
        "corregir": (
            "Corrige el siguiente texto mejorando gramática, ortografía y estilo. "
            "Mantén el significado original y no inventes información.\n\n"
            f"Texto:\n{text}"
        ),
        "expandir": (
            "Amplía el siguiente texto desarrollando sus ideas de forma coherente, "
            "sin introducir hechos no proporcionados por el usuario.\n\n"
            f"Texto:\n{text}"
        ),
        "variar": (
            "Genera tres variaciones creativas del siguiente texto. "
            "Mantén el significado principal, pero utiliza enfoques y tonos diferentes.\n\n"
            f"Texto:\n{text}"
        ),
    }

    if action not in prompts:
        raise ValueError(f"Acción no soportada: {action}")

    return prompts[action]

IMAGE_STYLES = {
    "Realista": "photorealistic, realistic lighting, high detail",
    "Anime": "anime style, vibrant colors, detailed illustration",
    "Pintura al óleo": "oil painting style, textured brush strokes, artistic composition",
    "Fotografía publicitaria": "professional advertising photography, commercial lighting, clean composition"
}


def build_image_prompt(prompt: str, style: str) -> str:
    style_prompt = IMAGE_STYLES.get(style, "")

    return f"{prompt}, {style_prompt}"