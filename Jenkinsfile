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

        stage('2. Build Frontend') {
            agent {
                docker {
                    image 'node:20-slim'
                    // On passe en root pour éviter les erreurs de permission sur /.npm
                    args '-u root'
                    reuseNode true
                }
            }
            steps {
                dir('frontend') {
                    echo "📦 Build du Frontend SvelteKit..."
                    // On utilise --unsafe-perm pour garantir l'écriture des dossiers de build
                    sh 'npm install --quiet'
                    sh 'npm run build'
                }
            }
        }

        stage('3. Build Image Docker') {
            steps { 
                echo "🔨 Construction de l'image finale..."
                sh "docker build -t ${DOCKER_IMAGE} ." 
            }
        }

        stage('4. Déploiement IaC (Terraform)') {
            steps {
                dir('terraform') {
                    sh 'terraform init'
                    sh 'terraform apply -auto-approve'
                }
            }
        }

        stage('5. Vérification Ansible') {
            steps {
                dir('ansible') {
                    sh 'ansible-playbook -i localhost, -c local site.yml'
                }
            }
        }
    }
    post {
        failure {
            echo "❌ Le build a échoué. Analyse des logs du conteneur..."
            sh "docker logs ${CONTAINER_NAME} || true"
        }
    }
}
