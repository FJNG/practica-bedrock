# prueba stable diffusion
import base64
import json

import boto3


session = boto3.Session(profile_name="practica-bedrock")

bedrock = session.client(
    "bedrock-runtime",
    region_name="us-west-2"
)

request_body = {
    "prompt": (
        "A modern marketing poster showing a futuristic creative studio "
        "where a designer generates images with AI, professional advertising "
        "photography, realistic style, clean composition, vibrant lighting"
    ),
    "aspect_ratio": "1:1",
    "output_format": "png"
}

response = bedrock.invoke_model(
    modelId="stability.sd3-5-large-v1:0",
    body=json.dumps(request_body)
)

response_body = json.loads(response["body"].read())

image_base64 = response_body["images"][0]
image_bytes = base64.b64decode(image_base64)

with open("generated_image.png", "wb") as image_file:
    image_file.write(image_bytes)

print("Imagen generada correctamente: generated_image.png")