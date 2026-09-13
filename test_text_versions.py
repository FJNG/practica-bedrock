from datetime import datetime

from services.database import (
    initialize_database,
    get_users,
    get_projects,
    create_text_content,
    save_text_version,
    get_text_versions
)

initialize_database()

users = get_users()
projects = get_projects()

carlos = next(
    user for user in users
    if user["name"] == "Carlos"
)

project = projects[0]

content_id = create_text_content(
    project_id=project["id"],
    title="Copy Instagram lanzamiento",
    created_by=carlos["id"]
)

save_text_version(
    content_id=content_id,
    text="Nuestro nuevo producto ya está disponible.",
    action="original",
    created_by=carlos["id"],
    created_at=datetime.now().isoformat()
)

save_text_version(
    content_id=content_id,
    text="Descubre nuestro nuevo producto, ya disponible.",
    action="corregir",
    created_by=carlos["id"],
    created_at=datetime.now().isoformat()
)

versions = get_text_versions(content_id)

for version in versions:
    print(version)