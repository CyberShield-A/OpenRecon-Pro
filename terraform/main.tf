# Indispensable pour que Terraform sache quelle image utiliser
resource "docker_image" "openrecon_img" {
  name         = "openrecon-app:latest"
  keep_locally = true
}

resource "docker_container" "openrecon_container" {
  name  = "openrecon-service"
  image = docker_image.openrecon_img.image_id
  
  ports {
    internal = 5000 
    external = 8081 
  }

  memory = 1024 

  restart  = "always"
  must_run = true
}
