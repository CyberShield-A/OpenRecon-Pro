pipeline {
    agent any
    environment {
        // Ces variables servent au log et au nettoyage en cas d'échec
        CONTAINER_NAME = "openrecon-service"
        APP_URL = "http://localhost:8081"
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
            steps { 
                // Important : Terraform utilise l'image "openrecon-app:latest"
                sh "docker build -t openrecon-app:latest ." 
            }
        }

        stage('3. Déploiement (Terraform)') {
            steps {
                dir('terraform') {
                    sh 'terraform init'
                    // C'est ICI que le conteneur est réellement lancé
                    sh 'terraform apply -auto-approve'
                }
            }
        }

        stage('4. Vérification (Ansible)') {
            steps {
                dir('ansible') {
                    // Exécute d'abord la config DNS puis le test de l'interface
                    sh 'ansible-playbook -i localhost, -c local setup_env.yml'
                    sh 'ansible-playbook -i localhost, -c local site.yml'
                }
            }
        }
    }

    post {
        success {
            echo "✅ Succès : OpenRecon-Pro est opérationnel sur ${APP_URL}"
        }
        failure {
            echo "❌ Échec détecté. Analyse des logs du conteneur..."
            sh "docker logs ${CONTAINER_NAME} || true"
        }
    }
}
