# -----------------------------------------------------------------------------
# PIPELINE X - COMMAND CENTER
# -----------------------------------------------------------------------------

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
	@echo "Pipeline X started."

# Stop containers
down:
	docker-compose down --volumes --remove-orphans

# Stop and Remove Volumes (Clean Start - Nuclear Option)
# Use this if Qdrant or Postgres gets stuck/corrupted.
clean:
	@echo "Cleaning up containers and volumes..."
	docker-compose down -v
	docker system prune -f
	@echo "Environment wiped clean."

# View Logs (Follow mode)
logs:
	docker-compose logs -f

# Enter the Airflow Scheduler container (for debugging Python scripts)
shell:
	docker exec -it pipeline-x-airflow-scheduler-1 bash

.PHONY: build up down clean logs shell