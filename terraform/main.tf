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

# Au lieu de "resource", on utilise "data" pour lire l'image existante
# Cela évite que Terraform essaie de la recréer ou de la supprimer
data "docker_image" "openrecon_app" {
  name = "openrecon-app:latest"
}

resource "docker_container" "openrecon_service" {
  # On utilise l'ID récupéré par le bloc data
  image = data.docker_image.openrecon_app.id
  name  = "openrecon-service"
  
  ports {
    internal = 5000
    external = 8081
  }

  memory = 1024
  restart = "always"

  env = [
    "FLASK_ENV=production",
    "PYTHONUNBUFFERED=1"
  ]
}
