import streamlit as st

from services.bedrock_text import generate_text
from services.bedrock_image import generate_image
from services.prompts import build_prompt, build_image_prompt, TEXT_CONFIG

from services.database import initialize_database, get_users, get_projects, save_image_record, get_images

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from services.database import save_image_record


st.set_page_config(
    page_title="Generative AI con Amazon Bedrock",
    layout="wide"
)

initialize_database()

users = get_users()
projects = get_projects()

if "current_user_id" not in st.session_state:
    st.session_state["current_user_id"] = users[0]["id"]

st.title("Generación de contenido con Amazon Bedrock")


selected_user = st.selectbox(
    "Usuario activo",
    users,
    index=next(
        i
        for i, user in enumerate(users)
        if user["id"] == st.session_state["current_user_id"]
    ),
    format_func=lambda user: f'{user["name"]} ({user["role"]})'
)

st.session_state["current_user_id"] = selected_user["id"]

if "current_project_id" not in st.session_state:
    st.session_state["current_project_id"] = projects[0]["id"]

selected_project = st.selectbox(
    "Proyecto activo",
    projects,
    index=next(
        i
        for i, project in enumerate(projects)
        if project["id"] == st.session_state["current_project_id"]
    ),
    format_func=lambda project: project["name"]
)

st.session_state["current_project_id"] = selected_project["id"]


st.caption(
    f'Usuario actual: {selected_user["name"]} · '
    f'Rol: {selected_user["role"]} · '
    f'Proyecto: {selected_project["name"]}'
)


tab_text, tab_image, tab_gallery = st.tabs(
    [
        "Edición de texto",
        "Generación de imágenes",
        "Galería"
    ]
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

                generated_dir = Path("data/generated")
                generated_dir.mkdir(parents=True, exist_ok=True)

                filename = f"{uuid4()}.png"
                file_path = generated_dir / filename

                with open(file_path, "wb") as file:
                    file.write(image_bytes)

                save_image_record(
                    project_id=selected_project["id"],
                    user_id=selected_user["id"],
                    filename=str(file_path),
                    prompt=image_prompt,
                    style=style,
                    seed=seed,
                    created_at=datetime.now().isoformat()
                )                

            st.subheader("Imagen generada")
            st.image(image_bytes)

with tab_gallery:
    st.header("Galería de imágenes")

    images = get_images()

    project_images = [
        image
        for image in images
        if image["project_id"] == selected_project["id"]
    ]

    if not project_images:
        st.info("Este proyecto todavía no tiene imágenes.")
    else:
        for image in project_images:

            image_path = Path(image["filename"])

            if not image_path.exists():
                st.warning(
                    f'La imagen "{image_path.name}" ya no existe en el almacenamiento.'
                )
                continue

            st.image(
                image["filename"],
                width=500
            )

            st.write(f'**Prompt:** {image["prompt"]}')
            st.write(f'**Estilo:** {image["style"]}')
            st.write(f'**Seed:** {image["seed"]}')
            st.write(f'**Fecha:** {image["created_at"]}')


            with open(image_path, "rb") as file:
                st.download_button(
                    label="Descargar imagen",
                    data=file.read(),
                    file_name=image_path.name,
                    mime="image/png",
                    key=f'download_{image["id"]}'
                )

            
            st.divider()            