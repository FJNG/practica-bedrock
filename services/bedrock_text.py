import os
import boto3

AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
AWS_PROFILE = os.getenv("AWS_PROFILE", "practica-bedrock")

CLAUDE_MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"


SYSTEM_PROMPT = """
Eres un asistente profesional de edición de contenido comercial.

Tu objetivo es ayudar a redactar, corregir, resumir, ampliar y generar
variaciones de textos manteniendo siempre el significado y la información
proporcionada por el usuario.

Debes cumplir estas reglas:

- No inventes características de productos, precios, garantías, promociones
  ni afirmaciones comerciales que no aparezcan en el texto original.
- No añadas información factual que no haya sido proporcionada.
- No intensifiques afirmaciones del texto original.
  Por ejemplo, no conviertas "comodidad" en "comodidad excepcional",
  ni "materiales de calidad" en "garantizan durabilidad y resistencia".
- Mantén el idioma del texto de entrada.
- Sigue exactamente la tarea solicitada.
- No expliques el proceso realizado.
- No incluyas comentarios sobre tus cambios.
- No uses Markdown, encabezados, listas con símbolos, negritas ni separadores
  salvo que la tarea lo solicite expresamente.
- Devuelve únicamente el contenido solicitado.
"""

def create_bedrock_client():
    session = boto3.Session(profile_name=AWS_PROFILE)

    return session.client(
        "bedrock-runtime",
        region_name=AWS_REGION
    )


def generate_text(
    prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 500
) -> str:

    bedrock = create_bedrock_client()

    response = bedrock.converse(
        modelId=CLAUDE_MODEL_ID,

        system=[
            {
                "text": SYSTEM_PROMPT
            }
        ],

        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],

        inferenceConfig={
            "temperature": temperature,
            "maxTokens": max_tokens
        }
    )

    return response["output"]["message"]["content"][0]["text"]