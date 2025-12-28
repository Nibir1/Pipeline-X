# -----------------------------------------------------------------------------
# PIPELINE X - COMMAND CENTER
# -----------------------------------------------------------------------------

# Force rebuild to ensure dependencies are fresh
build:
	docker-compose build --no-cache
	docker-compose up -d
	@echo "Pipeline X is running at http://localhost:5173"

# Standard Up (No Rebuild)
up:
	docker-compose up -d
	@echo "Pipeline X is running at http://localhost:5173"

# Stop containers
down:
	docker-compose down

# Stop and Remove Volumes (Clean Start)
clean:
	docker-compose down -v
	docker system prune -f

# View Logs
logs:
	docker-compose logs -f

.PHONY: build up down clean logs