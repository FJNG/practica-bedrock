from services.database import (
    initialize_database,
    create_user,
    get_users,
    create_project,
    get_projects
)

initialize_database()

create_user("Ana", "designer")
create_user("Carlos", "writer")
create_user("Fran", "approver")

users = get_users()

ana = next(user for user in users if user["name"] == "Ana")

create_project(
    "Campaña Otoño",
    ana["id"]
)

projects = get_projects()

for project in projects:
    print(project)