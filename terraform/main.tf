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

data "docker_image" "openrecon_app" {
  name = "openrecon-app:latest"
}

resource "docker_container" "openrecon_service" {
  image = data.docker_image.openrecon_app.id
  name  = "openrecon-service"
  
  # SOLUTION : Permet aux outils de scan de s'initialiser
  capabilities {
    add = ["NET_RAW", "NET_ADMIN"]
  }

  must_run = true
  restart  = "always"

  ports {
    internal = 5000
    external = 8081
  }

  env = [
    "FLASK_ENV=production",
    "PYTHONUNBUFFERED=1"
  ]
}
