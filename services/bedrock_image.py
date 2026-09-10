import base64
import json
import os

import boto3


AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
AWS_PROFILE = os.getenv("AWS_PROFILE", "practica-bedrock")

STABLE_DIFFUSION_MODEL_ID = "stability.sd3-5-large-v1:0"


def create_bedrock_client():
    session = boto3.Session(profile_name=AWS_PROFILE)

    return session.client(
        "bedrock-runtime",
        region_name=AWS_REGION
    )


def generate_image(
    prompt: str,
    aspect_ratio: str = "1:1",
    output_format: str = "png",
    seed: int = 0,
    negative_prompt: str = ""
) -> bytes:
    bedrock = create_bedrock_client()

    request_body = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "output_format": output_format,
        "seed": seed
    }

    if negative_prompt.strip():
        request_body["negative_prompt"] = negative_prompt

    response = bedrock.invoke_model(
        modelId=STABLE_DIFFUSION_MODEL_ID,
        body=json.dumps(request_body)
    )

    response_body = json.loads(
        response["body"].read().decode("utf-8")
    )

    finish_reasons = response_body.get("finish_reasons", [])

    if finish_reasons and finish_reasons[0] is not None:
        raise RuntimeError(
            f"La generación de imagen no se completó: "
            f"{finish_reasons[0]}"
        )

    images = response_body.get("images")

    if not images:
        raise RuntimeError(
            f"Bedrock no devolvió ninguna imagen. "
            f"Respuesta: {response_body}"
        )

    image_base64 = images[0]

    return base64.b64decode(image_base64)