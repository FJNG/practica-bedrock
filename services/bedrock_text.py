import os

import boto3


AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
AWS_PROFILE = os.getenv("AWS_PROFILE", "practica-bedrock")

CLAUDE_MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"


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