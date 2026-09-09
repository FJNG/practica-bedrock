from services.bedrock_text import generate_text
from services.prompts import build_prompt


text = """
La inteligencia artificial generativa permite crear contenido nuevo
a partir de instrucciones en lenguaje natural.
"""

prompt = build_prompt("resumir", text)

result = generate_text(prompt)

print(result)