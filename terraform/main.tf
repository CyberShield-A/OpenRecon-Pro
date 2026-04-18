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

resource "docker_image" "openrecon_img" {
  name = "openrecon-app:latest"
  build {
    context    = "${path.module}/.."
    dockerfile = "Dockerfile"
    no_cache   = true
  }
  triggers = {
    dir_sha1 = sha1(file("${path.module}/../gui.py"))
  }
  keep_locally = false
}

resource "docker_container" "openrecon_container" {
  name  = "openrecon-service"
  image = docker_image.openrecon_img.image_id
  ports {
    internal = 5000
    external = 8081
  }
  restart = "always"
  must_run = true
}
