SHELL := /bin/bash
.DEFAULT_GOAL := help

-include .env

GO_DIR ?= api
GO_MAIN ?= ./cmd/server

PY_DIR ?= ml_pipeline
PYTHON ?= python3

MIGRATIONS_DIR ?= api/migrations
steps ?= 1

SIGESGUARDA_DATABASE.SSL_MODE ?= disable
SIGESGUARDA_DB_DSN ?=postgres://$(SIGESGUARDA_DATABASE.USER):$(SIGESGUARDA_DATABASE.PASSWORD)@$(SIGESGUARDA_DATABASE.HOST):$(SIGESGUARDA_DATABASE.PORT)/$(SIGESGUARDA_DATABASE.NAME)?sslmode=$(SIGESGUARDA_DATABASE.SSL_MODE)

.PHONY: help lint test check run \
		python-lint python-test \
		go-lint go-test go-tidy \
		migrations-new migrations-up migrations-down migrations-status confirm

help: ## Show available commands
	@awk 'BEGIN {FS = ":.*##"; printf "Available commands:\n"} /^[a-zA-Z0-9_.-]+:.*##/ {printf "  %-22s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

lint: python-lint go-lint ## Run Python and Go linters

test: python-test go-test ## Run Python and Go tests

check: lint test ## Run lint and tests

run: ## Run Go API
	cd $(GO_DIR) && go run $(GO_MAIN)

python-lint: ## Run Python lint checks
	cd $(PY_DIR) && $(PYTHON) -m ruff check .
	cd $(PY_DIR) && $(PYTHON) -m ruff format --check .

python-test: ## Run Python tests
	cd $(PY_DIR) && $(PYTHON) -m pytest

go-lint: ## Run Go lint checks
	cd $(GO_DIR) && go vet ./...
	cd $(GO_DIR) && golangci-lint run ./...

go-test: ## Run Go tests
	cd $(GO_DIR) && go test ./...

go-tidy: ## Format Go files and tidy dependencies
	cd $(GO_DIR) && go fmt ./...
	cd $(GO_DIR) && go mod tidy
	cd $(GO_DIR) && go mod verify

confirm:
	@printf 'Are you sure? [y/N] '; \
	read ans; \
	[ "$${ans:-N}" = y ]

migrations-new: ## Create migration. Usage: make migrations-new name=create_table
	@test -n "$(name)" || (echo "Usage: make migrations-new name=migration_name" && exit 1)
	tern new -m $(MIGRATIONS_DIR) $(name)

migrations-up: confirm ## Apply all pending migrations
	tern migrate -m $(MIGRATIONS_DIR) --conn-string "$(SIGESGUARDA_DB_DSN)"

migrations-down: confirm ## Roll back migrations. Usage: make migrations-down steps=1
	tern migrate -m $(MIGRATIONS_DIR) --conn-string "$(SIGESGUARDA_DB_DSN)" -d -$(steps)

migrations-status: ## Show migration status
	tern status -m $(MIGRATIONS_DIR) --conn-string "$(SIGESGUARDA_DB_DSN)"
