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

# 1. Construction de l'image avec détection de changement de contenu
resource "docker_image" "openrecon_img" {
  name = "openrecon-app:latest"
  
  build {
    context    = "${path.module}/.." # Chemin absolu plus robuste
    dockerfile = "Dockerfile"
    no_cache   = true # Force Docker à ne pas tricher avec le cache
  }

  # CRUCIAL : Force Terraform à reconstruire si gui.py est modifié
  triggers = {
    dir_sha1 = sha1(file("${path.module}/../gui.py"))
  }

  keep_locally = false # Supprime l'ancienne image pour éviter les conflits
}

# 2. Gestion du conteneur
resource "docker_container" "openrecon_container" {
  name  = "openrecon-service"
  image = docker_image.openrecon_img.image_id # Dépendance directe de l'ID de l'image
  
  ports {
    internal = 5000
    external = 8081
  }

  restart = "always"
  
  # Recrée le conteneur dès que l'ID de l'image change
  must_run = true
}
