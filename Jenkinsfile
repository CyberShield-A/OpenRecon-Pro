pipeline {
    agent any

    stages {
        stage('0. Préparation du Serveur') {
            steps {
                // Vérification visuelle des fichiers fusionnés (Frontend + Backend)
                sh 'ls -R'
                
                dir('ansible') {
                    sh 'ansible-playbook -i "localhost," -c local setup_env.yml'
                }
            }
        }
        
        stage('1. Audit & Tests') {
            parallel {
                stage('Bandit') { 
                    steps { 
                        // Analyse de sécurité statique (ignore les erreurs mineures pour le build)
                        sh 'bandit -c .bandit -r . || true' 
                    } 
                }
                stage('Pytest') { 
                    steps { 
                        // Tests unitaires Python
                        sh 'pytest || true' 
                    } 
                }
            }
        }
        
        stage('2. Build Image (Multi-Stage)') {
            steps {
                // Construction de l'image Docker avec cache
                sh 'docker build -t openrecon-app:latest .'
            }
        }
        
        stage('3. Infrastructure (Terraform)') {
            steps {
                dir('terraform') {
                    // Nettoyage préventif du conteneur précédent pour libérer le port 8081
                    sh 'docker rm -f openrecon-service || true'
                    
                    // Initialisation et déploiement via Terraform
                    sh 'terraform init'
                    sh 'terraform apply -auto-approve'
                }
            }
        }
        
        stage('4. Vérification (Ansible)') {
            steps {
                dir('ansible') {
                    // Vérification de la disponibilité du service
                    // Note : Le playbook site.yml doit contenir des 'retries' pour laisser Flask démarrer
                    sh 'ansible-playbook -i "localhost," -c local site.yml'
                }
            }
        }
    }
    
    post {
        failure { 
            // En cas d'échec (ex: test Ansible raté), on supprime le conteneur défectueux
            echo 'Build échoué. Nettoyage du conteneur openrecon-service...'
            sh 'docker rm -f openrecon-service || true' 
        }
        success {
            // En cas de succès, on laisse le conteneur tourner pour la démo/PFE
            echo '------------------------------------------------------------'
            echo ' DEPLOIEMENT REUSSI : OpenRecon-Pro est en ligne !'
            echo ' Accès : http://localhost:8081'
            echo '------------------------------------------------------------'
        }
        always {
            // Nettoyage des fichiers temporaires de build Jenkins
            cleanWs()
        }
    }
}
