# prueba claude haiku 4.5

import boto3


session = boto3.Session(profile_name="practica-bedrock")

bedrock = session.client(
    "bedrock-runtime",
    region_name="us-west-2"
)

response = bedrock.converse(
    modelId="us.anthropic.claude-haiku-4-5-20251001-v1:0",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "text": (
                        "Resume en una frase: "
                        "La inteligencia artificial generativa permite crear "
                        "contenido nuevo a partir de instrucciones en lenguaje natural."
                    )
                }
            ]
        }
    ],
    inferenceConfig={
        "maxTokens": 200
    }
)

text = response["output"]["message"]["content"][0]["text"]

print(text)