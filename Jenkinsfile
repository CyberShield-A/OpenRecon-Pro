pipeline {
    agent any
    
    stages {
        stage('0. Préparation du Serveur') {
            steps {
                // --- DEBUG : Cette commande va afficher tous les fichiers trouvés par Jenkins ---
                sh 'ls -R'
                // -----------------------------------------------------------------------------
                
                dir('ansible') {
                    sh 'ansible-playbook -i "localhost," -c local setup_env.yml'
                }
            }
        }
        
        stage('1. Audit & Tests') {
            parallel {
                stage('Bandit') { 
                    steps { 
                        sh 'bandit -c .bandit -r . || true' 
                    } 
                }
                stage('Pytest') { 
                    steps { 
                        sh 'pytest' 
                    } 
                }
            }
        }
        
        stage('2. Build Image') {
            steps {
                sh 'docker build -t openrecon-app:latest .'
            }
        }
        
        stage('3. Infrastructure (Terraform)') {
            steps {
                dir('terraform') {
                    sh 'docker rm -f openrecon-service || true'
                    sh 'terraform init'
                    sh 'terraform apply -auto-approve'
                }
            }
        }
        
        stage('4. Vérification (Ansible)') {
            steps {
                dir('ansible') {
                    sh 'ansible-playbook -i "localhost," -c local site.yml'
                }
            }
        }
    }
    
    post {
        failure { 
            sh 'docker rm -f openrecon-service || true' 
        }
    }
}
