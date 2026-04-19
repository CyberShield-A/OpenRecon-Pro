pipeline {
    agent any
    options {
        skipDefaultCheckout()
        timeout(time: 1, unit: 'HOURS')
    }
    stages {
        stage('0. Préparation du Serveur') {
            steps {
                dir('ansible') {
                    // Cette étape répare automatiquement Docker/DNS en cas de problème
                    sh 'ansible-playbook -i "localhost," -c local setup_env.yml'
                }
            }
        }
        stage('1. Préparation Code') {
            steps {
                deleteDir()
                checkout scm
            }
        }
        stage('2. Audit & Tests') {
            parallel {
                stage('Bandit') { steps { sh 'bandit -c .bandit -r . || true' } }
                stage('Pytest') { steps { sh 'pytest' } }
            }
        }
        stage('3. Build Image') {
            steps {
                sh 'docker build -t openrecon-app:latest .'
            }
        }
        stage('4. Infrastructure (Terraform)') {
            steps {
                dir('terraform') {
                    sh 'docker rm -f openrecon-service || true'
                    sh 'terraform init'
                    sh 'terraform apply -auto-approve'
                }
            }
        }
        stage('5. Vérification (Ansible)') {
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
