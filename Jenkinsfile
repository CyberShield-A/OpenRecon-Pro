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
                    steps { 
                        sh 'bandit -r . -f txt || true' 
                    }
                }
                stage('Pytest') {
                    steps { 
                        sh 'pytest tests/' 
                    }
                }
            }
        }

        stage('2. Build Frontend') {
            // On utilise un conteneur Node pour ne pas dépendre de l'install locale du serveur
            agent {
                docker {
                    image 'node:20-slim'
                    reuseNode true
                }
            }
            steps {
                dir('frontend') {
                    echo "📦 Build du Frontend SvelteKit via Docker..."
                    sh 'npm install'
                    sh 'npm run build'
                }
            }
        }

        stage('3. Build Image Docker') {
            steps { 
                echo "🔨 Construction de l'image OpenRecon-Pro..."
                // L'image globale contiendra le frontend buildé à l'étape précédente
                sh "docker build -t ${DOCKER_IMAGE} ." 
            }
        }

        stage('4. Déploiement IaC (Terraform)') {
            steps {
                dir('terraform') {
                    echo "🚀 Déploiement de l'infrastructure avec les privilèges réseau..."
                    sh 'terraform init'
                    sh 'terraform apply -auto-approve'
                }
            }
        }

        stage('5. Vérification Ansible') {
            steps {
                dir('ansible') {
                    echo "🔍 Vérification de la disponibilité du service..."
                    sh 'ansible-playbook -i localhost, -c local site.yml'
                }
            }
        }
    }
    
    post {
        success {
            echo "✅ Succès : OpenRecon-Pro est déployé et opérationnel sur le port 8081."
        }
        failure {
            echo "❌ Échec du Pipeline. Vérifiez les logs ci-dessus."
            // Affiche les logs du conteneur en cas d'échec du déploiement
            sh "docker logs ${CONTAINER_NAME} || true"
        }
    }
}
