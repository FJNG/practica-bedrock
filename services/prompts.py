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

    prompts = {

        "resumir": f"""
Resume el siguiente texto de forma clara y concisa.

Conserva únicamente las ideas principales.
No añadas información nueva.
Devuelve únicamente el resumen final.

Texto original:

{text}
""",

        "corregir": f"""
Corrige el siguiente texto.

Mejora únicamente:
- ortografía
- gramática
- puntuación
- claridad
- estilo

Mantén el significado original.
No añadas información nueva.
No expliques las correcciones realizadas.
Devuelve únicamente el texto corregido.

Texto original:

{text}
""",

"expandir": f"""
Amplía el siguiente texto desarrollando únicamente las ideas que ya aparecen.

Puedes explicar con más detalle el contenido existente, pero no debes:
- añadir características nuevas
- intensificar cualidades existentes
- convertir cualidades en garantías o promesas
- introducir beneficios no mencionados
- añadir materiales concretos
- añadir durabilidad, resistencia, confort superior u otras prestaciones
  si no aparecen explícitamente en el texto original
- usar expresiones promocionales no respaldadas por el texto

Mantén el mismo significado y el mismo nivel de afirmación del original.

Devuelve únicamente el texto ampliado.

Texto original:

{text}
""",
"variar": f"""
Genera tres variaciones del siguiente texto.

Cada variación debe conservar exactamente la información factual del texto original,
pero utilizar una redacción diferente.

No inventes características, beneficios ni afirmaciones comerciales.
No intensifiques cualidades existentes.
No conviertas características en garantías, promesas o relaciones causales.
Evita palabras como "garantiza", "asegura", "ideal", "perfecto",
"superior", "excepcional" o similares si no aparecen en el texto original.

Mantén el mismo nivel de afirmación del texto original.

Devuelve exactamente este formato de texto plano:

Variación 1:
texto

Variación 2:
texto

Variación 3:
texto

No utilices Markdown, símbolos de formato, encabezados con almohadillas
ni separadores.

Texto original:

{text}
"""
}

    if action not in prompts:
        raise ValueError(f"Acción de texto no válida: {action}")

    return prompts[action]


IMAGE_STYLES = {
    "Realista": "photorealistic, realistic lighting, high detail",
    "Anime": "anime style, vibrant colors, detailed illustration",
    "Pintura al óleo": "oil painting style, textured brush strokes, artistic composition",
    "Fotografía publicitaria": "professional advertising photography, commercial lighting, clean composition"
}

def build_image_prompt(prompt: str, style: str) -> str:
    style_prompt = IMAGE_STYLES.get(style, "")

    if style_prompt:
        return f"{prompt}, {style_prompt}"

    return prompt