terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0.1"
    }
  }
}

# On indique à Terraform d'utiliser le moteur Docker de ta machine hôte
provider "docker" {
  host = "unix:///var/run/docker.sock"
}

# 1. Construction de l'image Docker à partir du Dockerfile
resource "docker_image" "openrecon_img" {
  name = "openrecon-app:latest"
  build {
    context = ".." # On remonte d'un cran pour trouver le Dockerfile à la racine
    dockerfile = "Dockerfile"
  }
}

# 2. Création et lancement du conteneur
resource "docker_container" "openrecon_container" {
  image = docker_image.openrecon_img.image_id
  name  = "openrecon-service"
  
  # On mappe le port pour éviter le conflit avec Jenkins (8080)
  ports {
    internal = 5000
    external = 8081 
  }

  # Optionnel : On peut passer des variables d'environnement si besoin
  env = [
    "APP_ENV=production"
  ]
}
