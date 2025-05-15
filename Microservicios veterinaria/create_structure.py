import os

# Estructura del proyecto
structure = {
    "veterinary-appointment-system": [
        "docker-compose.yml",
        ".env",
        {
            "frontend": [
                {"static": [
                    {"css": ["styles.css"]},
                    {"js": ["main.js"]}
                ]},
                {"templates": ["index.html", "login.html", "register.html", "dashboard.html", "appointment.html"]},
                "app.py",
                "requirements.txt",
                "Dockerfile"
            ]
        },
        {
            "auth-service": [
                "app.py",
                "models.py",
                "routes.py",
                "requirements.txt",
                "Dockerfile"
            ]
        },
        {
            "appointment-service": [
                "app.py",
                "models.py",
                "routes.py",
                "requirements.txt",
                "Dockerfile"
            ]
        },
        {
            "notification-service": [
                "app.py",
                "routes.py",
                "email_service.py",
                "requirements.txt",
                "Dockerfile"
            ]
        },
        {
            "database": ["init.sql"]
        }
    ]
}


def create_structure(base_path, structure):
    for item in structure:
        if isinstance(item, dict):
            for folder_name, contents in item.items():
                folder_path = os.path.join(base_path, folder_name)
                os.makedirs(folder_path, exist_ok=True)
                create_structure(folder_path, contents)
        elif isinstance(item, str):
            os.makedirs(base_path, exist_ok=True)
            file_path = os.path.join(base_path, item)
            with open(file_path, 'w') as f:
                pass


def main():
    base_path = os.getcwd()
    project_name = "veterinary-appointment-system"
    project_path = os.path.join(base_path, project_name)
    os.makedirs(project_path, exist_ok=True)

    # Obtener la estructura del proyecto
    project_structure = structure[project_name]
    create_structure(project_path, project_structure)

    print(f"Estructura del proyecto creada en {project_path}")


if __name__ == "__main__":
    main()
