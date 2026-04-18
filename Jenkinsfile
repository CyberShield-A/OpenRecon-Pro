pipeline {
    agent any
    options {
        skipDefaultCheckout()
        timeout(time: 1, unit: 'HOURS')
    }
    stages {
        stage('0. Préparation') {
            steps {
                deleteDir()
                checkout scm
            }
        }
        stage('1. Audit & Tests') {
            parallel {
                stage('Bandit') { steps { sh 'bandit -c .bandit -r . || true' } }
                stage('Pytest') { steps { sh 'pytest' } }
            }
        }
        stage('2. Infrastructure (Terraform)') {
            steps {
                dir('terraform') {
                    // Nettoyage forcé pour éviter les conflits de nom
                    sh 'docker rm -f openrecon-service || true'
                    sh 'terraform init'
                    sh 'terraform apply -auto-approve'
                }
            }
        }
        stage('3. Configuration (Ansible)') {
            steps {
                dir('ansible') {
                    sh 'ansible-playbook -i "localhost," -c local site.yml'
                }
            }
        }
    }
    post {
        failure { sh 'docker rm -f openrecon-service || true' }
    }
}
