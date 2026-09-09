import streamlit as st

from services.bedrock_text import generate_text
from services.bedrock_image import generate_image
from services.prompts import build_prompt, build_image_prompt, TEXT_CONFIG


st.set_page_config(
    page_title="Generative AI con Amazon Bedrock",
    layout="wide"
)

st.title("Generación de contenido con Amazon Bedrock")

tab_text, tab_image = st.tabs(
    ["Edición de texto", "Generación de imágenes"]
)


with tab_text:
    st.header("Edición de contenido")

    text = st.text_area(
        "Introduce el texto",
        height=200
    )

    action = st.selectbox(
        "Acción",
        ["resumir", "corregir", "expandir", "variar"]
    )

    if st.button("Procesar texto"):
        if not text.strip():
            st.warning("Introduce un texto.")
        else:
            with st.spinner("Procesando con Claude..."):
                prompt = build_prompt(action, text)
                config = TEXT_CONFIG[action]

                result = generate_text(
                    prompt,
                    temperature=config["temperature"],
                    max_tokens=config["max_tokens"]
                )

            st.subheader("Resultado")
            st.write(result)


with tab_image:
    st.header("Generación de imágenes")

    image_prompt = st.text_area(
        "Describe la imagen que quieres generar",
        height=150
    )

    style = st.selectbox(
        "Estilo",
        [
            "Realista",
            "Anime",
            "Pintura al óleo",
            "Fotografía publicitaria"
        ]
    )

    aspect_ratio = st.selectbox(
        "Formato",
        ["1:1", "16:9", "9:16"]
    )

    seed = st.number_input(
        "Seed",
        min_value=0,
        max_value=4294967295,
        value=0,
        step=1
    )

    negative_prompt = st.text_input(
        "Elementos a evitar",
        placeholder="texto borroso, baja calidad, deformidades..."
    )

    if st.button("Generar imagen"):
        if not image_prompt.strip():
            st.warning("Introduce una descripción.")
        else:
            with st.spinner(
                "Generando imagen con Stable Diffusion. "
                "Este proceso puede tardar varios minutos..."
            ):
                final_prompt = build_image_prompt(
                    image_prompt,
                    style
                )

                image_bytes = generate_image(
                    prompt=final_prompt,
                    aspect_ratio=aspect_ratio,
                    seed=seed,
                    negative_prompt=negative_prompt
                )

            st.subheader("Imagen generada")
            st.image(image_bytes)