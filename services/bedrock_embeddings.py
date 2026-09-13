import json
import os

import boto3


AWS_REGION = os.getenv(
    "AWS_REGION",
    "us-west-2"
)

AWS_PROFILE = os.getenv(
    "AWS_PROFILE",
    "practica-bedrock"
)

TITAN_EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v1"


def create_bedrock_client():
    """
    Crea el cliente de Amazon Bedrock Runtime utilizando
    el perfil AWS configurado para la práctica.
    """

    session = boto3.Session(
        profile_name=AWS_PROFILE
    )

    return session.client(
        "bedrock-runtime",
        region_name=AWS_REGION
    )


def generate_embedding(text: str) -> list[float]:
    """
    Genera un embedding vectorial para un texto utilizando
    Amazon Titan Embeddings.

    Titan no genera texto: transforma el contenido recibido
    en un vector numérico que representa su significado semántico.
    """

    if not text or not text.strip():
        raise ValueError(
            "No se puede generar un embedding de un texto vacío."
        )

    bedrock = create_bedrock_client()

    body = {
        "inputText": text.strip()
    }

    response = bedrock.invoke_model(
        modelId=TITAN_EMBEDDING_MODEL_ID,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )

    response_body = json.loads(
        response["body"].read()
    )

    embedding = response_body.get("embedding")

    if not embedding:
        raise RuntimeError(
            "Titan no devolvió ningún embedding."
        )

    return embedding