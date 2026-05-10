terraform {
  required_providers {
    docker = {
      # Correction vitale : source officielle actuelle
      source  = "kreuzwerker/docker"
      version = "~> 3.0.1"
    }
  }
}

provider "docker" {
  # Connexion au socket Docker local de ta VM Ubuntu
  host = "unix:///var/run/docker.sock"
}

# Référence à l'image que Jenkins vient de construire
resource "docker_image" "openrecon_app" {
  name         = "openrecon-app:latest"
  keep_locally = true
}

# Déploiement du conteneur
resource "docker_container" "openrecon_service" {
  image = docker_image.openrecon_app.image_id
  name  = "openrecon-service"
  
  # Mappage des ports : 8081 (externe) -> 5000 (interne Flask)
  ports {
    internal = 5000
    external = 8081
  }

  # Limites de ressources (Bonne pratique DevOps/Cyber)
  memory = 1024 # Limite à 1 Go de RAM
  cpu_shares = 512

  # Redémarrage automatique si le service crash
  restart = "always"

  # Variable d'environnement pour Flask (double sécurité)
  env = [
    "FLASK_ENV=production",
    "PYTHONUNBUFFERED=1"
  ]
}
