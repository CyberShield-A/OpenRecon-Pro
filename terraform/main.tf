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

# 1. Construction automatique de l'image Docker à partir du Dockerfile racine
resource "docker_image" "openrecon_img" {
  name = "openrecon-app:latest"
  build {
    context    = ".." # Dossier parent car main.tf est dans terraform/
    dockerfile = "Dockerfile"
  }
}

# 2. Gestion du conteneur (Suppression et re-création automatique)
resource "docker_container" "openrecon_container" {
  name  = "openrecon-service"
  image = docker_image.openrecon_img.image_id
  
  ports {
    internal = 5000
    external = 8081 # Accessible sur http://localhost:8081
  }

  restart = "always"
  
  # On force la mise à jour si l'image change
  must_run = true
}
