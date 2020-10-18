/* Tested with Jenkins 2.262
Requires python3.7 and pip installed on agent, would use docker image with python and requests if I had more time
*/
pipeline {
    agent any
    parameters {
        string(name: 'URL', defaultValue: 'http://wp.pl', description: 'URL to download images from')
    }
    environment {
        TMP_DIR = "DownloadImages-${BUILD_NUMBER}"
    }
    stages {
        stage('Prepare environment') {
            steps {
                git url: 'https://github.com/Kondziowy/image_downloader', branch: 'main'
                sh 'python3.7 -m pip install -r requirements.txt'
            }
        }
        stage('Download images') {
            steps {
                sh "mkdir -p ${TMP_DIR}"
                // Run this in a separate directory so we're sure all files are artifacts
                sh "cd ${TMP_DIR}; python3.7 ${WORKSPACE}/image_downloader.py ${params.URL}"
            }
            post {
                always {
                    archiveArtifacts artifacts: "${TMP_DIR}/*", onlyIfSuccessful: true
                    sh "rm -rf ${TMP_DIR}"
                }
            }
        }
    }
}