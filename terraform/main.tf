terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0.1"
    }
  }
}

provider "docker" {
  host = "unix:///var/run/docker.sock"
}

# Lecture de l'image buildée par Jenkins
data "docker_image" "openrecon_app" {
  name = "openrecon-app:latest"
}

resource "docker_container" "openrecon_service" {
  # Utilisation de l'ID dynamique de l'image
  image = data.docker_image.openrecon_app.id
  name  = "openrecon-service"
  
  # Crucial pour éviter le "Moteur non chargé" en mode Agressif
  capabilities {
    add = ["NET_RAW", "NET_ADMIN"]
  }

  # Sécurité de déploiement
  must_run = true
  restart  = "always"
  memory   = 1024

  # Mappage des ports (8081 pour l'accès externe)
  ports {
    internal = 5000
    external = 8081
  }

  env = [
    "FLASK_ENV=production",
    "PYTHONUNBUFFERED=1"
  ]
}
