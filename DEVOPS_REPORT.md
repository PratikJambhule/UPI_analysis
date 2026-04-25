# DevOps Implementation Report

## Project
UPI Analytics Platform (Streamlit-based web application)

## Assignment Requirement Mapping
Requirement: Develop web application and apply CI/CD using 3-4 technologies (must include testing tool and Jenkins or Ansible)

Implemented technologies:
1. Streamlit - Web application framework
2. pytest - Automated testing tool
3. Jenkins - CI/CD orchestration tool
4. Docker - Container build and deployment

This satisfies the mandatory condition (Testing tool + Jenkins) and uses 4 technologies.

## CI/CD Pipeline Overview
Pipeline definition: Jenkinsfile at repository root.

Stages:
1. Checkout
- Pulls latest source code from SCM.

2. Install Dependencies
- Creates Python virtual environment.
- Installs project dependencies from requirements.txt.

3. Run Tests
- Runs pytest test suite.
- Exports JUnit XML report to reports/junit.xml.
- Jenkins publishes test report in post actions.

4. Build Docker Image
- Builds upi-analytics-platform image.
- Tags image as build-{BUILD_NUMBER} and latest.

5. Deploy To Docker
- Removes old container if present.
- Starts new container on selected host port (default 8501).

## Pipeline Flow Diagram
SCM Push/Trigger -> Jenkins Checkout -> Python Setup -> pytest Gate -> Docker Build -> Docker Deploy -> Running App

## Commands Used
Local validation commands:
- make test
- make docker-build
- make docker-run
- make docker-stop

## Screenshots to Include Before Submission
Add screenshots in your final uploaded report/document:
1. Jenkins job configuration page
2. Jenkins pipeline stage view (all green)
3. Jenkins test report showing pytest results
4. Docker image list and running container
5. Running web application in browser (http://localhost:8501)

Suggested naming:
- screenshot_01_jenkins_job_config.png
- screenshot_02_pipeline_success.png
- screenshot_03_pytest_report.png
- screenshot_04_docker_running.png
- screenshot_05_app_homepage.png

## Evidence Checklist
- Web app runs successfully in browser
- Test stage passes in Jenkins
- Docker image builds in pipeline
- Deployment stage starts container
- Pipeline explanation documented

## Notes
- Existing GitHub Actions workflow remains available, but assignment compliance is achieved through Jenkins + pytest + Docker.
- Git is used only for source control convenience, not counted as one of the technologies.
