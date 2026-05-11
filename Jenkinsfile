pipeline {
    agent any
    environment {
        DOCKER_IMAGE = "openrecon-app:latest"
        CONTAINER_NAME = "openrecon-service"
    }
    stages {
        stage('1. Audit & Tests') {
            parallel {
                stage('Bandit') {
                    steps { sh 'bandit -r . -f txt || true' }
                }
                stage('Pytest') {
                    steps { sh 'pytest tests/' }
                }
            }
        }
        stage('2. Build Image') {
            steps { sh "docker build -t ${DOCKER_IMAGE} ." }
        }
        stage('3. Infrastructure') {
            steps {
                dir('terraform') {
                    sh 'terraform init'
                    sh 'terraform apply -auto-approve'
                }
            }
        }
        stage('4. Vérification') {
            steps {
                dir('ansible') {
                    sh 'ansible-playbook -i localhost, -c local site.yml'
                }
            }
        }
    }
    post {
        failure {
            echo "ERREUR : Récupération des logs du conteneur..."
            sh "docker logs ${CONTAINER_NAME} || true"
            sh "docker rm -f ${CONTAINER_NAME} || true"
        }
    }
}
