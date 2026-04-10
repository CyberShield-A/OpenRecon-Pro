pipeline {
    agent any
    stages {
        stage('1. Audit de Sécurité') {
            steps {
                sh 'bandit -c .bandit -r .'
            }
        }
        stage('2. Tests Unitaires') {
            steps {
                sh 'pytest'
            }
        }
        stage('3. Déploiement') {
            steps {
                echo "Infrastructure et Sécurité validées !"
            }
        }
    }
}
