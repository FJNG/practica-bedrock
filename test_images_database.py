from datetime import datetime

from services.database import (
    initialize_database,
    get_users,
    get_projects,
    save_image_record,
    get_images
)


initialize_database()

users = get_users()
projects = get_projects()

ana = next(user for user in users if user["name"] == "Ana")
project = projects[0]

save_image_record(
    project_id=project["id"],
    user_id=ana["id"],
    filename="data/generated/test.png",
    prompt="Un coche deportivo rojo en una carretera de montaña",
    style="Fotografía publicitaria",
    seed=12345,
    created_at=datetime.now().isoformat()
)

images = get_images()

for image in images:
    print(image)