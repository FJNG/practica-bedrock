import streamlit as st

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from services.bedrock_text import generate_text
from services.bedrock_image import generate_image

from services.security import (
    contains_prompt_injection,
    contains_disallowed_content,
    detect_pii,
    contains_copyright_risk
)

from services.prompts import (
    build_prompt,
    build_image_prompt,
    TEXT_CONFIG
)

from services.database import (
    initialize_database,
    get_users,
    get_projects,

    create_text_content,
    get_text_contents,
    get_text_versions,
    save_text_version,
    update_text_content_status,
    add_review_comment,
    get_review_comments,

    create_image_content,
    get_image_contents,
    get_image_versions,
    save_image_version,
    update_image_content_status,
    add_image_review_comment,
    get_image_review_comments
)

from services.knowledge_service import sync_knowledge,  get_rag_context

st.set_page_config(
    page_title="Generative AI con Amazon Bedrock",
    layout="wide"
)

initialize_database()

users = get_users()
projects = get_projects()

st.title("Generación de contenido con Amazon Bedrock")

if not users:
    st.error("No hay usuarios disponibles.")
    st.stop()

if not projects:
    st.error("No hay proyectos disponibles.")
    st.stop()


# ============================================================
# USUARIO Y PROYECTO ACTIVO
# ============================================================

if "current_user_id" not in st.session_state:
    st.session_state["current_user_id"] = users[0]["id"]


selected_user = st.selectbox(
    "Usuario activo",
    users,
    index=next(
        (
            i
            for i, user in enumerate(users)
            if user["id"] == st.session_state["current_user_id"]
        ),
        0
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
        (
            i
            for i, project in enumerate(projects)
            if project["id"] == st.session_state["current_project_id"]
        ),
        0
    ),
    format_func=lambda project: project["name"]
)

# Recuperamos conocimiento sobre el proyecto seleccionado
sync_knowledge(selected_project["id"])    

st.session_state["current_project_id"] = selected_project["id"]


st.caption(
    f'Usuario actual: {selected_user["name"]} · '
    f'Rol: {selected_user["role"]} · '
    f'Proyecto: {selected_project["name"]}'
)

role = selected_user["role"]


# ============================================================
# FUNCIONES DE INTERFAZ
# ============================================================

STATUS_LABELS = {
    "draft": "Borrador",
    "in_review": "En revisión",
    "approved": "Aprobado"
}


def latest_text_review_comment(content_id: int):
    comments = get_review_comments(content_id)
    return comments[0] if comments else None


def latest_image_review_comment(content_id: int):
    comments = get_image_review_comments(content_id)
    return comments[0] if comments else None


def show_image_version(
    version,
    width=500,
    key_prefix="image"
):
    image_path = Path(version["filename"])

    if not image_path.exists():
        st.warning(
            f'La imagen "{image_path.name}" ya no existe en el almacenamiento.'
        )
        return False

    st.image(str(image_path), width=width)

    st.write(f'**Versión:** v{version["version_number"]}')
    st.write(f'**Prompt:** {version["prompt"]}')
    st.write(f'**Estilo:** {version["style"]}')
    st.write(f'**Seed:** {version["seed"]}')
    st.write(f'**Fecha:** {version["created_at"]}')

    with open(image_path, "rb") as file:
        st.download_button(
            label="Descargar imagen",
            data=file.read(),
            file_name=image_path.name,
            mime="image/png",
            key=(
                f'{key_prefix}_download_'
                f'image_version_{version["id"]}'
            )
        )

    return True

def render_image_gallery():
    st.header("Galería de imágenes")

    contents = get_image_contents(selected_project["id"])

    if not contents:
        st.info("Este proyecto todavía no tiene propuestas visuales.")
        return

    for content in contents:
        versions = get_image_versions(content["id"])

        if not versions:
            continue

        current_version = versions[0]

        st.subheader(content["title"])
        st.caption(
            f'Estado: {STATUS_LABELS.get(content["status"], content["status"])} · '
            f'Versión actual: v{current_version["version_number"]}'
        )

        show_image_version(
            current_version,
            key_prefix=f'gallery_current_{content["id"]}'
        )

        review = latest_image_review_comment(content["id"])

        if review:
            if review["decision"] == "changes_requested":
                st.warning(
                    f'Última revisión: cambios solicitados · '
                    f'{review["comment"]}'
                )
            elif review["decision"] == "approved":
                st.success(
                    f'Última revisión: aprobada · '
                    f'{review["comment"]}'
                )

        if len(versions) > 1:
            with st.expander("Ver versiones anteriores"):
                for version in versions[1:]:
                    show_image_version(
                        version,
                        width=350,
                        key_prefix=f'gallery_history_{content["id"]}'
                    )
                    st.divider()

        st.divider()


# ============================================================
# REDACTOR
# ============================================================

if role == "writer":
    tab_text, = st.tabs([
        "Edición de texto"
    ])

    with tab_text:
        st.header("Edición de contenido")

        contents = get_text_contents(selected_project["id"])
        content_options = ["+ Nuevo contenido"] + contents

        if "current_text_content_id" not in st.session_state:
            st.session_state["current_text_content_id"] = None

        selected_index = 0

        if st.session_state["current_text_content_id"] is not None:
            for i, item in enumerate(content_options):
                if (
                    isinstance(item, dict)
                    and item["id"] == st.session_state["current_text_content_id"]
                ):
                    selected_index = i
                    break

        selected_content = st.selectbox(
            "Contenido",
            content_options,
            index=selected_index,
            format_func=lambda item:
                item if isinstance(item, str) else item["title"]
        )

        if isinstance(selected_content, dict):
            st.session_state["current_text_content_id"] = (
                selected_content["id"]
            )
        else:
            st.session_state["current_text_content_id"] = None
        # ----------------------------------------------------
        # Nuevo contenido
        # ----------------------------------------------------
        if selected_content == "+ Nuevo contenido":
            new_title = st.text_input(
                "Título del contenido",
                placeholder="Ej. Copy Instagram lanzamiento"
            )

            text = st.text_area(
                "Introduce el texto",
                height=200
            )

            # deteción de información privada
            pii_detected = detect_pii(text)

            if st.button("Crear contenido"):
                if not new_title.strip():
                    st.warning("Introduce un título.")

                elif not text.strip():
                    st.warning("Introduce un texto.")

                elif contains_prompt_injection(text):
                    st.warning(
                        "El texto contiene instrucciones potencialmente manipulativas "
                        "y no se guardará."
                    )

                elif contains_disallowed_content(text):
                    st.warning(
                        "El texto contiene contenido potencialmente inapropiado "
                        "y no se guardará."
                    )

                elif pii_detected:
                    st.warning(
                        "Se han detectado posibles datos personales: "
                        + ", ".join(pii_detected)
                        + ". El contenido no se guardará."
                    )

                elif contains_copyright_risk(text):
                    st.warning(
                        "El texto contiene una solicitud de reproducción o imitación exacta "
                        "y no se procesará."
                    )                

                else:
                    content_id = create_text_content(
                        project_id=selected_project["id"],
                        title=new_title.strip(),
                        created_by=selected_user["id"]
                    )

                    save_text_version(
                        content_id=content_id,
                        text=text,
                        action="original",
                        created_by=selected_user["id"],
                        created_at=datetime.now().isoformat()
                    )

                    st.session_state["current_text_content_id"] = content_id

                    st.success("Contenido creado correctamente.")
                    st.rerun()
        # ----------------------------------------------------
        # Contenido existente
        # ----------------------------------------------------
        else:
            versions = get_text_versions(selected_content["id"])

            if not versions:
                st.warning("Este contenido todavía no tiene versiones.")
            else:
                current_version = versions[0]
                status = selected_content["status"]

                st.caption(
                    f'Estado: {STATUS_LABELS.get(status, status)} · '
                    f'Versión actual: v{current_version["version_number"]}'
                )

                review = latest_text_review_comment(
                    selected_content["id"]
                )

                if (
                    status == "draft"
                    and review
                    and review["decision"] == "changes_requested"
                ):
                    st.warning(
                        f'El aprobador ha solicitado cambios: '
                        f'{review["comment"]}'
                    )

                text = st.text_area(
                    "Texto actual",
                    value=current_version["text"],
                    height=200,
                    disabled=status != "draft"
                )

                # -------------------------
                # BORRADOR
                # -------------------------
                if status == "draft":
                    action = st.selectbox(
                        "Acción",
                        ["resumir", "corregir", "expandir", "variar"]
                    )

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        process = st.button(
                            "Procesar con Claude y guardar versión"
                        )

                    with col2:
                        save_manual = st.button(
                            "Guardar nueva versión"
                        )

                    with col3:
                        send_review = st.button(
                            "Enviar a revisión"
                        )

                    # ------------------------------------------------
                    # Procesar con Claude
                    # ------------------------------------------------
                    if process:
                        pii_detected = detect_pii(text)

                        if not text.strip():
                            st.warning("Introduce un texto.")

                        elif contains_prompt_injection(text):
                            st.warning(
                                "El texto contiene instrucciones potencialmente manipulativas "
                                "y no se procesará."
                            )

                        elif contains_disallowed_content(text):
                            st.warning(
                                "El texto contiene contenido potencialmente inapropiado "
                                "y no se procesará."
                            )

                        elif pii_detected:
                            st.warning(
                                "Se han detectado posibles datos personales: "
                                + ", ".join(pii_detected)
                                + ". El contenido no se enviará al modelo."
                            )

                        elif contains_copyright_risk(text):
                            st.warning(
                                "El texto contiene una solicitud de reproducción o imitación exacta "
                                "y no se procesará."
                            )

                        else:
                            with st.spinner("Procesando con Claude..."):

                                # recuperar top k del servicio de contenido    
                                rag_context = get_rag_context(
                                    project_id=selected_project["id"],
                                    query=text,
                                    top_k=3
                                )

                                prompt = build_prompt(action=action, text=text, rag_context=rag_context)
                                
                                config = TEXT_CONFIG[action]

                                result = generate_text(
                                    prompt,
                                    temperature=config["temperature"],
                                    max_tokens=config["max_tokens"]
                                )

                            new_version = save_text_version(
                                content_id=selected_content["id"],
                                text=result,
                                action=action,
                                created_by=selected_user["id"],
                                created_at=datetime.now().isoformat()
                            )

                            st.success(
                                f"Nueva versión creada: v{new_version}"
                            )
                            st.rerun()

                    # ------------------------------------------------
                    # Guardado manual
                    # ------------------------------------------------
                    if save_manual:
                        pii_detected = detect_pii(text)

                        if not text.strip():
                            st.warning("El texto no puede estar vacío.")

                        elif text == current_version["text"]:
                            st.info("No hay cambios que guardar.")

                        elif contains_prompt_injection(text):
                            st.warning(
                                "El texto contiene instrucciones potencialmente manipulativas "
                                "y no se guardará."
                            )

                        elif contains_disallowed_content(text):
                            st.warning(
                                "El texto contiene contenido potencialmente inapropiado "
                                "y no se guardará."
                            )

                        elif pii_detected:
                            st.warning(
                                "Se han detectado posibles datos personales: "
                                + ", ".join(pii_detected)
                                + ". El contenido no se guardará."
                            )

                        elif contains_copyright_risk(text):
                            st.warning(
                                "El texto contiene una solicitud de reproducción o imitación exacta "
                                "y no se guardará."
                            )

                        else:
                            new_version = save_text_version(
                                content_id=selected_content["id"],
                                text=text,
                                action="edición manual",
                                created_by=selected_user["id"],
                                created_at=datetime.now().isoformat()
                            )

                            st.success(
                                f"Nueva versión creada: v{new_version}"
                            )
                            st.rerun()

                # ------------------------------------------------
                # Enviar a revisión
                # ------------------------------------------------
                if send_review:
                    pii_detected = detect_pii(text)

                    if not text.strip():
                        st.warning("El texto no puede estar vacío.")

                    elif text != current_version["text"]:
                        st.warning(
                            "Hay cambios sin guardar. Guarda primero una nueva versión "
                            "antes de enviar a revisión."
                        )

                    elif contains_prompt_injection(text):
                        st.warning(
                            "El texto contiene instrucciones potencialmente manipulativas "
                            "y no se enviará a revisión."
                        )

                    elif contains_disallowed_content(text):
                        st.warning(
                            "El texto contiene contenido potencialmente inapropiado "
                            "y no se enviará a revisión."
                        )

                    elif pii_detected:
                        st.warning(
                            "Se han detectado posibles datos personales: "
                            + ", ".join(pii_detected)
                            + ". El contenido no se enviará a revisión."
                        )

                    elif contains_copyright_risk(text):
                        st.warning(
                            "El texto contiene una solicitud de reproducción o imitación exacta "
                            "y no se enviará a revisión."
                        )

                    else:
                        update_text_content_status(
                            selected_content["id"],
                            "in_review"
                        )

                        st.success("Contenido enviado a revisión.")
                        st.rerun()
                                
                # -------------------------
                # EN REVISIÓN
                # -------------------------
                elif status == "in_review":
                    st.info(
                        "El contenido está en revisión. "
                        "Debe esperar la decisión del aprobador."
                    )

                # -------------------------
                # APROBADO
                # -------------------------
                elif status == "approved":
                    st.success("Este contenido está aprobado.")

                if len(versions) > 1:
                    with st.expander("Historial de versiones"):
                        for version in versions:
                            st.write(
                                f'**v{version["version_number"]} · '
                                f'{version["action"]} · '
                                f'{version["created_at"]}**'
                            )
                            st.write(version["text"])
                            st.divider()


# ============================================================
# DISEÑADOR
# ============================================================

elif role == "designer":
    tab_image, tab_gallery = st.tabs([
        "Generación de imágenes",
        "Galería"
    ])

    with tab_image:
        st.header("Generación de imágenes")

        image_contents = get_image_contents(
            selected_project["id"]
        )

        image_options = ["+ Nueva propuesta visual"] + image_contents

        if "current_image_content_id" not in st.session_state:
            st.session_state["current_image_content_id"] = None

        selected_index = 0

        if st.session_state["current_image_content_id"] is not None:
            for i, item in enumerate(image_options):
                if (
                    isinstance(item, dict)
                    and item["id"] == st.session_state["current_image_content_id"]
                ):
                    selected_index = i
                    break

        selected_image_content = st.selectbox(
            "Propuesta visual",
            image_options,
            index=selected_index,
            format_func=lambda item:
                item if isinstance(item, str) else item["title"]
        )

        if isinstance(selected_image_content, dict):
            st.session_state["current_image_content_id"] = (
                selected_image_content["id"]
            )
        else:
            st.session_state["current_image_content_id"] = None
        # ----------------------------------------------------
        # Nueva propuesta visual
        # ----------------------------------------------------
        if selected_image_content == "+ Nueva propuesta visual":
            image_title = st.text_input(
                "Título de la propuesta",
                placeholder="Ej. Mocasines otoño"
            )

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
                placeholder=(
                    "texto borroso, baja calidad, deformidades..."
                )
            )

            pii_detected = detect_pii(image_prompt)

            if st.button("Crear propuesta y generar v1"):
                if not image_title.strip():
                    st.warning("Introduce un título.")

                elif not image_prompt.strip():
                    st.warning("Introduce una descripción.")

                elif contains_disallowed_content(image_prompt):
                    # Moderación:
                    # Bloqueamos contenido inapropiado antes de llamar
                    # al modelo de generación de imágenes.
                    st.warning(
                        "La descripción contiene contenido potencialmente inapropiado "
                        "y no se generará la imagen."
                    )

                elif pii_detected:
                    st.warning(
                        "Se han detectado posibles datos personales: "
                        + ", ".join(pii_detected)
                        + ". La descripción no se enviará al modelo."
                    )        

                elif contains_copyright_risk(image_prompt):
                    st.warning(
                        "La descripción solicita una reproducción o imitación exacta "
                        "y no se generará la imagen."
                    )                                

                else:
                    try:
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
                            generated_dir.mkdir(
                                parents=True,
                                exist_ok=True
                            )

                            filename = f"{uuid4()}.png"
                            file_path = generated_dir / filename

                            with open(file_path, "wb") as file:
                                file.write(image_bytes)

                            content_id = create_image_content(
                                project_id=selected_project["id"],
                                title=image_title.strip(),
                                created_by=selected_user["id"]
                            )

                            version_number = save_image_version(
                                content_id=content_id,
                                filename=str(file_path),
                                prompt=image_prompt,
                                style=style,
                                seed=seed,
                                created_by=selected_user["id"],
                                created_at=datetime.now().isoformat()
                            )

                            st.session_state["current_image_content_id"] = content_id

                            st.success(
                                f"Propuesta creada con la versión v{version_number}."
                            )

                            st.rerun()

                    except RuntimeError as error:
                        if "Filter reason: prompt" in str(error):
                            st.warning(
                                "El prompt ha sido bloqueado por el "
                                "filtro de seguridad del modelo. "
                                "Prueba a reformular la descripción."
                            )
                        else:
                            st.error(str(error))

        # ----------------------------------------------------
        # Propuesta existente
        # ----------------------------------------------------
        else:
            versions = get_image_versions(
                selected_image_content["id"]
            )

            if not versions:
                st.warning(
                    "Esta propuesta todavía no tiene versiones."
                )
            else:
                current_version = versions[0]
                status = selected_image_content["status"]

                st.caption(
                    f'Estado: {STATUS_LABELS.get(status, status)} · '
                    f'Versión actual: v{current_version["version_number"]}'
                )

                show_image_version(
                    current_version,
                    key_prefix=(
                        f'designer_current_{selected_image_content["id"]}'
                    )
                )

                review = latest_image_review_comment(
                    selected_image_content["id"]
                )

                if (
                    status == "draft"
                    and review
                    and review["decision"] == "changes_requested"
                ):
                    st.warning(
                        f'El aprobador ha solicitado cambios: '
                        f'{review["comment"]}'
                    )

                # -------------------------
                # BORRADOR
                # -------------------------
                if status == "draft":
                    st.subheader("Generar una nueva versión")

                    image_prompt = st.text_area(
                        "Descripción",
                        value=current_version["prompt"],
                        height=150,
                        key=(
                            f'image_prompt_'
                            f'{selected_image_content["id"]}'
                        )
                    )

                    style_options = [
                        "Realista",
                        "Anime",
                        "Pintura al óleo",
                        "Fotografía publicitaria"
                    ]

                    current_style_index = (
                        style_options.index(current_version["style"])
                        if current_version["style"] in style_options
                        else 0
                    )

                    style = st.selectbox(
                        "Estilo",
                        style_options,
                        index=current_style_index,
                        key=(
                            f'image_style_'
                            f'{selected_image_content["id"]}'
                        )
                    )

                    aspect_ratio = st.selectbox(
                        "Formato",
                        ["1:1", "16:9", "9:16"],
                        key=(
                            f'image_ratio_'
                            f'{selected_image_content["id"]}'
                        )
                    )

                    seed = st.number_input(
                        "Seed",
                        min_value=0,
                        max_value=4294967295,
                        value=int(current_version["seed"]),
                        step=1,
                        key=(
                            f'image_seed_'
                            f'{selected_image_content["id"]}'
                        )
                    )

                    negative_prompt = st.text_input(
                        "Elementos a evitar",
                        placeholder=(
                            "texto borroso, baja calidad, "
                            "deformidades..."
                        ),
                        key=(
                            f'image_negative_'
                            f'{selected_image_content["id"]}'
                        )
                    )

                    col1, col2 = st.columns(2)

                    with col1:
                        generate_new_version = st.button(
                            "Generar nueva versión",
                            key=(
                                f'generate_image_version_'
                                f'{selected_image_content["id"]}'
                            )
                        )

                    with col2:
                        send_image_review = st.button(
                            "Enviar a revisión",
                            key=(
                                f'send_image_review_'
                                f'{selected_image_content["id"]}'
                            )
                        )


                    if generate_new_version:

                        pii_detected = detect_pii(image_prompt)

                        if not image_prompt.strip():
                            st.warning("Introduce una descripción.")

                        elif contains_disallowed_content(image_prompt):
                            st.warning(
                                "La descripción contiene contenido potencialmente inapropiado "
                                "y no se generará la imagen."
                            )

                        elif pii_detected:
                            st.warning(
                                "Se han detectado posibles datos personales: "
                                + ", ".join(pii_detected)
                                + ". La descripción no se enviará al modelo."
                            )

                        elif contains_copyright_risk(image_prompt):
                            st.warning(
                                "La descripción solicita una reproducción o imitación exacta "
                                "y no se generará la imagen."
                            )

                        else:
                            try:
                                with st.spinner(
                                    "Generando nueva versión con Stable Diffusion..."
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

                                    generated_dir = Path(
                                        "data/generated"
                                    )
                                    generated_dir.mkdir(
                                        parents=True,
                                        exist_ok=True
                                    )

                                    filename = f"{uuid4()}.png"
                                    file_path = generated_dir / filename

                                    with open(
                                        file_path,
                                        "wb"
                                    ) as file:
                                        file.write(image_bytes)

                                    version_number = save_image_version(
                                        content_id=(
                                            selected_image_content["id"]
                                        ),
                                        filename=str(file_path),
                                        prompt=image_prompt,
                                        style=style,
                                        seed=seed,
                                        created_by=selected_user["id"],
                                        created_at=(
                                            datetime.now().isoformat()
                                        )
                                    )

                                st.success(
                                    f"Nueva versión creada: "
                                    f"v{version_number}"
                                )
                                st.rerun()

                            except RuntimeError as error:
                                if "Filter reason: prompt" in str(error):
                                    st.warning(
                                        "El prompt ha sido bloqueado por "
                                        "el filtro de seguridad del modelo. "
                                        "Prueba a reformular la descripción."
                                    )
                                else:
                                    st.error(str(error))

                    if send_image_review:
                        pii_detected = detect_pii(image_prompt)

                        if not image_prompt.strip():
                            st.warning("Introduce una descripción.")

                        elif (
                            image_prompt != current_version["prompt"]
                            or style != current_version["style"]
                            or int(seed) != int(current_version["seed"])
                        ):
                            st.warning(
                                "Hay cambios sin guardar. Genera primero una nueva versión "
                                "antes de enviar a revisión."
                            )

                        elif contains_disallowed_content(image_prompt):
                            st.warning(
                                "La descripción contiene contenido potencialmente inapropiado "
                                "y no se enviará a revisión."
                            )

                        elif pii_detected:
                            st.warning(
                                "Se han detectado posibles datos personales: "
                                + ", ".join(pii_detected)
                                + ". La propuesta no se enviará a revisión."
                            )

                        elif contains_copyright_risk(image_prompt):
                            st.warning(
                                "La descripción solicita una reproducción o imitación exacta "
                                "y no se enviará a revisión."
                            )

                        else:
                            update_image_content_status(
                                selected_image_content["id"],
                                "in_review"
                            )

                            st.success(
                                "Propuesta visual enviada a revisión."
                            )
                            st.rerun()
                # -------------------------
                # EN REVISIÓN
                # -------------------------
                elif status == "in_review":
                    st.info(
                        "La propuesta visual está en revisión. "
                        "Debe esperar la decisión del aprobador."
                    )

                # -------------------------
                # APROBADO
                # -------------------------
                elif status == "approved":
                    st.success(
                        "Esta propuesta visual está aprobada."
                    )

                if len(versions) > 1:
                    with st.expander("Historial de versiones"):
                        for version in versions[1:]:
                            show_image_version(
                                version,
                                width=350,
                                key_prefix=(
                                    f'designer_history_{selected_image_content["id"]}'
                                )
                            )
                            st.divider()

    with tab_gallery:
        render_image_gallery()


# ============================================================
# APROBADOR
# ============================================================

elif role == "approver":
    tab_text_review, tab_image_review, tab_gallery = st.tabs([
        "Revisión de textos",
        "Revisión de imágenes",
        "Galería"
    ])

    # --------------------------------------------------------
    # REVISIÓN DE TEXTOS
    # --------------------------------------------------------
    with tab_text_review:
        st.header("Revisión de textos")

        contents = get_text_contents(selected_project["id"])

        review_contents = [
            content
            for content in contents
            if content["status"] == "in_review"
        ]

        if not review_contents:
            st.info("No hay textos pendientes de revisión.")
        else:
            selected_content = st.selectbox(
                "Texto pendiente",
                review_contents,
                format_func=lambda item: item["title"],
                key="review_text_content"
            )

            versions = get_text_versions(selected_content["id"])

            if not versions:
                st.warning(
                    "Este contenido todavía no tiene versiones."
                )
            else:
                current_version = versions[0]

                st.caption(
                    f'Estado: En revisión · '
                    f'Versión actual: '
                    f'v{current_version["version_number"]}'
                )

                st.text_area(
                    "Texto a revisar",
                    value=current_version["text"],
                    height=200,
                    disabled=True,
                    key=(
                        f'review_text_'
                        f'{selected_content["id"]}_'
                        f'{current_version["id"]}'
                    )
                )

                review_comment = st.text_area(
                    "Comentario de revisión",
                    placeholder=(
                        "Indica observaciones o cambios necesarios..."
                    ),
                    key=f'text_comment_{selected_content["id"]}'
                )

                col1, col2 = st.columns(2)

                with col1:
                    approve = st.button(
                        "Aprobar texto",
                        key=f'approve_text_{selected_content["id"]}'
                    )

                with col2:
                    request_changes = st.button(
                        "Solicitar cambios",
                        key=(
                            f'request_text_changes_'
                            f'{selected_content["id"]}'
                        )
                    )

                if approve:
                    add_review_comment(
                        content_id=selected_content["id"],
                        version_id=current_version["id"],
                        user_id=selected_user["id"],
                        comment=(
                            review_comment.strip()
                            or "Contenido aprobado."
                        ),
                        decision="approved",
                        created_at=datetime.now().isoformat()
                    )

                    update_text_content_status(
                        selected_content["id"],
                        "approved"
                    )

                    st.success("Texto aprobado.")
                    st.rerun()

                if request_changes:
                    if not review_comment.strip():
                        st.warning(
                            "Indica qué cambios debe realizar "
                            "el redactor."
                        )
                    else:
                        add_review_comment(
                            content_id=selected_content["id"],
                            version_id=current_version["id"],
                            user_id=selected_user["id"],
                            comment=review_comment.strip(),
                            decision="changes_requested",
                            created_at=datetime.now().isoformat()
                        )

                        update_text_content_status(
                            selected_content["id"],
                            "draft"
                        )

                        st.success(
                            "Se han solicitado cambios al redactor."
                        )
                        st.rerun()

    # --------------------------------------------------------
    # REVISIÓN DE IMÁGENES
    # --------------------------------------------------------
    with tab_image_review:
        st.header("Revisión de imágenes")

        image_contents = get_image_contents(
            selected_project["id"]
        )

        review_image_contents = [
            content
            for content in image_contents
            if content["status"] == "in_review"
        ]

        if not review_image_contents:
            st.info("No hay imágenes pendientes de revisión.")
        else:
            selected_image_content = st.selectbox(
                "Propuesta visual pendiente",
                review_image_contents,
                format_func=lambda item: item["title"],
                key="review_image_content"
            )

            versions = get_image_versions(
                selected_image_content["id"]
            )

            if not versions:
                st.warning(
                    "Esta propuesta todavía no tiene versiones."
                )
            else:
                current_version = versions[0]

                st.caption(
                    f'Estado: En revisión · '
                    f'Versión actual: '
                    f'v{current_version["version_number"]}'
                )

                show_image_version(
                    current_version,
                    key_prefix=(
                        f'approver_review_{selected_image_content["id"]}'
                    )
                )

                review_comment = st.text_area(
                    "Comentario de revisión",
                    placeholder=(
                        "Indica observaciones o cambios necesarios..."
                    ),
                    key=(
                        f'image_review_comment_'
                        f'{selected_image_content["id"]}'
                    )
                )

                col1, col2 = st.columns(2)

                with col1:
                    approve_image = st.button(
                        "Aprobar imagen",
                        key=(
                            f'approve_image_'
                            f'{selected_image_content["id"]}'
                        )
                    )

                with col2:
                    request_image_changes = st.button(
                        "Solicitar cambios",
                        key=(
                            f'request_image_changes_'
                            f'{selected_image_content["id"]}'
                        )
                    )

                if approve_image:
                    add_image_review_comment(
                        content_id=selected_image_content["id"],
                        version_id=current_version["id"],
                        user_id=selected_user["id"],
                        comment=(
                            review_comment.strip()
                            or "Imagen aprobada."
                        ),
                        decision="approved",
                        created_at=datetime.now().isoformat()
                    )

                    update_image_content_status(
                        selected_image_content["id"],
                        "approved"
                    )

                    st.success("Imagen aprobada.")
                    st.rerun()

                if request_image_changes:
                    if not review_comment.strip():
                        st.warning(
                            "Indica qué cambios debe realizar "
                            "el diseñador."
                        )
                    else:
                        add_image_review_comment(
                            content_id=selected_image_content["id"],
                            version_id=current_version["id"],
                            user_id=selected_user["id"],
                            comment=review_comment.strip(),
                            decision="changes_requested",
                            created_at=datetime.now().isoformat()
                        )

                        update_image_content_status(
                            selected_image_content["id"],
                            "draft"
                        )

                        st.success(
                            "Se han solicitado cambios al diseñador."
                        )
                        st.rerun()

    with tab_gallery:
        render_image_gallery()


# ============================================================
# ROL DESCONOCIDO
# ============================================================

else:
    st.warning(f'Rol no reconocido: "{role}"')
