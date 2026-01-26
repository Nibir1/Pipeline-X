# -----------------------------------------------------------------------------
# PIPELINE X - COMMAND CENTER
# -----------------------------------------------------------------------------

# --- CLOUD INFRASTRUCTURE (Azure) ---

# Initialize Terraform (Run this first)
infra-init:
	@echo "Initializing Terraform..."
	cd infra && terraform init

# Provision Azure Resources (Postgres + Data Lake)
infra-up:
	@echo "Provisioning Azure Infrastructure..."
	cd infra && terraform apply -auto-approve
	@echo "Infrastructure is ready. Update your .env file with the outputs."

# Destroy Azure Resources (Save Money)
infra-down:
	@echo "Destroying Azure Infrastructure..."
	cd infra && terraform destroy -auto-approve
	@echo "Azure resources deleted."

# --- LOCAL DEVELOPMENT (Docker) ---

# Build the image MANUALLY first to avoid Docker Compose race conditions, then start.
build:
	@echo "Building Docker Image (Sequential)..."
	docker build -t pipeline-x-airflow:latest .
	@echo "Starting Services..."
	docker-compose up -d
	@echo "------------------------------------------------"
	@echo "Pipeline X is live!"
	@echo "   - UI:       http://localhost:8501"
	@echo "   - Spark:    http://localhost:8081"
	@echo "   - Airflow:  http://localhost:8080/login/"
	@echo "   - API:      http://localhost:8000/docs"
	@echo "------------------------------------------------"

# Standard Up (Assumes image exists)
up:
	docker-compose up -d
	@echo "------------------------------------------------"
	@echo "Pipeline X is live!"
	@echo "   - UI:       http://localhost:8501"
	@echo "   - Spark:    http://localhost:8081"
	@echo "   - Airflow:  http://localhost:8080/login/"
	@echo "   - API:      http://localhost:8000/docs"
	@echo "------------------------------------------------"

# Stop containers
down:
	docker-compose down --volumes --remove-orphans

# Stop and Remove Volumes + Clean Python Cache (Nuclear Option)
# Use this if Qdrant, Postgres, or Python gets stuck.
clean:
	@echo "Cleaning up containers and volumes..."
	docker-compose down -v
	docker system prune -f
	@echo "Removing Python cache files (__pycache__)..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Environment wiped clean."

# View Logs (Follow mode)
logs:
	docker-compose logs -f

# Enter the Airflow Scheduler container (for debugging Python scripts)
shell:
	docker exec -it pipeline-x-airflow-scheduler-1 bash

.PHONY: build up down clean logs shell infra-init infra-up infra-down