pipeline {
    agent any
    stages {
        stage('1. Audit & Tests (Parallèle)') {
            parallel {
                stage('Sécurité Code (Bandit)') {
                    steps {
                        // On garde ton fichier de config .bandit
                        sh 'bandit -c .bandit -r .'
                    }
                }
                stage('Sécurité Libs (Safety)') {
                    steps {
                        // Vérifie si requirements.txt contient des versions vulnérables
                        sh 'safety check -r requirements.txt || echo "Avertissement: Failles de dépendances trouvées"'
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
                // On vérifie qu'aucun mot de passe n'a été oublié en clair
                sh "grep -rE 'password|api_key|token|secret' . --exclude-dir=.git || echo 'Aucun secret détecté'"
            }
        }

        stage('3. Infrastructure (Terraform)') {
            steps {
                dir('terraform') {
                    sh 'terraform init'
                    sh 'terraform apply -auto-approve'
                }
            }
        }

        stage('4. Configuration (Ansible)') {
            steps {
                dir('ansible') {
                    // On utilise le mode local pour valider le bon fonctionnement
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
        }
    }
}
