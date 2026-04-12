terraform {
  required_version = ">= 1.0.0"
}

resource "null_resource" "test_connexion" {
  provisioner "local-exec" {
    command = "echo 'Terraform est opérationnel dans le pipeline Jenkins'"
  }
}
