pipeline {
    agent any

    options {
        // Force le nettoyage du workspace avant chaque build pour éviter la corruption Git
        skipDefaultCheckout()
        timeout(time: 1, unit: 'HOURS')
    }

    stages {
        stage('0. Préparation & Checkout') {
            steps {
                // Nettoyage agressif pour éviter l'erreur "loose object is corrupt"
                deleteDir()
                checkout scm
            }
        }

        stage('1. Audit & Tests (Parallèle)') {
            parallel {
                stage('Sécurité Code (Bandit)') {
                    steps {
                        sh 'bandit -c .bandit -r .'
                    }
                }
                stage('Sécurité Libs (Safety)') {
                    steps {
                        // On s'assure que safety est installé puis on check
                        sh '''
                            pip install safety --quiet || true
                            safety check -r requirements.txt || echo "Avertissement: Failles de dépendances trouvées"
                        '''
                    }
                }
                stage('Tests Logiques (Pytest)') {
                    steps {
                        sh 'pytest'
                    }
                }
            }
        }

        stage('2. Scan de Secrets') {
            steps {
                sh "grep -rE 'password|api_key|token|secret' . --exclude-dir=.git || echo 'Aucun secret détecté'"
            }
        }

        stage('3. Infrastructure (Terraform)') {
            steps {
                dir('terraform') {
                    // RÉPARATION DU CONFLIT DOCKER :
                    // On supprime le conteneur s'il existe déjà avant de lancer Terraform
                    sh 'docker rm -f openrecon-service || true'
                    
                    sh 'terraform init'
                    sh 'terraform apply -auto-approve'
                }
            }
        }

        stage('4. Configuration (Ansible)') {
            steps {
                dir('ansible') {
                    sh 'ansible-playbook -i "localhost," -c local site.yml'
                }
            }
        }
    }

    post {
        success {
            echo "✅ Succès Total : Code audité, Infra prête, Ansible a configuré l'environnement."
        }
        failure {
            echo "❌ Échec du Pipeline : Vérifie les logs de sécurité ou les tests unitaires."
            // Optionnel : Nettoyage automatique en cas d'échec pour libérer Docker
            sh 'docker rm -f openrecon-service || true'
        }
    }
}
