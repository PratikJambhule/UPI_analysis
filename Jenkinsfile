pipeline {
    agent any

    parameters {
        booleanParam(name: 'BUILD_DOCKER', defaultValue: false, description: 'Build Docker image in pipeline')
        booleanParam(name: 'DEPLOY_TO_DOCKER', defaultValue: true, description: 'Deploy latest build to local Docker after successful tests')
        string(name: 'APP_PORT', defaultValue: '8501', description: 'Host port to expose Streamlit app')
    }

    environment {
        IMAGE_NAME = 'upi-analytics-platform'
        IMAGE_TAG = "build-${BUILD_NUMBER}"
        CONTAINER_NAME = 'upi-analytics-app'
    }

    stages {
        stage('Checkout') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                            set -eux
                            cp -r /workspace/UPI_DS_Project-main/. .
                        '''
                    } else {
                        bat '''
                            xcopy /E /I /Y C:\\workspace\\UPI_DS_Project-main\\* .
                        '''
                    }
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                            set -eux
                            PYTHON_BIN=$(command -v python3 || command -v python)
                            $PYTHON_BIN -m venv .venv
                            . .venv/bin/activate
                            python -m pip install --upgrade pip
                            pip install -r requirements.txt
                        '''
                    } else {
                        bat '''
                            python -m venv .venv
                            call .venv\\Scripts\\activate
                            python -m pip install --upgrade pip
                            pip install -r requirements.txt
                        '''
                    }
                }
            }
        }

        stage('Run Tests') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                            set -eux
                            mkdir -p reports
                            . .venv/bin/activate
                            pytest tests/ -v --tb=short --junitxml=reports/junit.xml
                        '''
                    } else {
                        bat '''
                            if not exist reports mkdir reports
                            call .venv\\Scripts\\activate
                            pytest tests\\ -v --tb=short --junitxml=reports\\junit.xml
                        '''
                    }
                }
            }
        }

        stage('Build Docker Image') {
            when {
                expression { return params.BUILD_DOCKER }
            }
            steps {
                script {
                    if (isUnix()) {
                        sh 'docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest .'
                    } else {
                        bat 'docker build -t %IMAGE_NAME%:%IMAGE_TAG% -t %IMAGE_NAME%:latest .'
                    }
                }
            }
        }

        stage('Deploy To Docker') {
            when {
                expression { return params.DEPLOY_TO_DOCKER }
            }
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                            set +e
                            docker rm -f ${CONTAINER_NAME}
                            set -e
                            docker run -d --name ${CONTAINER_NAME} -p ${APP_PORT}:8501 ${IMAGE_NAME}:latest
                        '''
                    } else {
                        bat '''
                            docker rm -f %CONTAINER_NAME%
                            docker run -d --name %CONTAINER_NAME% -p %APP_PORT%:8501 %IMAGE_NAME%:latest
                        '''
                    }
                }
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'reports/junit.xml'
        }
        success {
            echo 'CI/CD pipeline completed successfully.'
        }
        failure {
            echo 'Pipeline failed. Inspect stage logs for details.'
        }
    }
}