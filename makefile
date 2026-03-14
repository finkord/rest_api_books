
# ================================
#  Makefile for Docker image building
# ================================

COMMIT_HASH := $(shell git rev-parse --short HEAD)
BRANCH      := $(shell git rev-parse --abbrev-ref HEAD)
TAG         := $(BRANCH)_$(COMMIT_HASH)

REPOSITORY_NAME := finkord/books-api
CONTEXT_DIR := ./

IMAGE_NAME := $(REPOSITORY_NAME):$(TAG)

# ================================	
#             Commands
# ================================

# ---------------------------------------
# Makefile: Display available Make targets
# ---------------------------------------
help:
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  help            Show this message"
	@echo "  build           Build docker image with tag '$(TAG)'"
	@echo "  push            Push docker image to repository"
	@echo "  print-tag       Print generated image tag"
	@echo "  compose-up      Start docker compose"
	@echo "  compose-down    Stop docker compose"
	@echo ""

# ---------------------------------------
# Docker: Build image with versioned tag
# ---------------------------------------
build:
	docker build -t $(IMAGE_NAME) -t $(REPOSITORY_NAME):latest $(CONTEXT_DIR)

# ----------------------------------------
# Push docker image to repository
# ----------------------------------------
push:
	docker push $(IMAGE_NAME)
	docker push $(REPOSITORY_NAME):latest

# ----------------------------------------
# Docker Compose: Start and stop
# ----------------------------------------
compose-up:
	docker compose -f docker-compose.yml up -d
compose-down:
	docker compose -f docker-compose.yml down
compose-up-build:
	docker compose -f docker-compose.yml up --build -d

# ----------------------------------------
# Print generated image tag (for logging)
# ----------------------------------------
print-tag:
	@echo $(IMAGE_NAME)