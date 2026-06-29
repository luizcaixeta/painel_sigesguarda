SHELL := /bin/bash
.DEFAULT_GOAL := help

-include .env

GO_DIR ?= api
GO_MAIN ?= ./cmd/server

PY_DIR ?= ml_pipeline
PYTHON ?= .venv/bin/python

MIGRATIONS_DIR ?= api/migrations
steps ?= 1

SIGESGUARDA_DATABASE.SSL_MODE ?= disable
SIGESGUARDA_DB_DSN ?=postgres://$(SIGESGUARDA_DATABASE.USER):$(SIGESGUARDA_DATABASE.PASSWORD)@$(SIGESGUARDA_DATABASE.HOST):$(SIGESGUARDA_DATABASE.PORT)/$(SIGESGUARDA_DATABASE.NAME)?sslmode=$(SIGESGUARDA_DATABASE.SSL_MODE)

.PHONY: help lint test check run \
		python-lint python-test \
		sigesguarda-check-update \
		sigesguarda-download \
		ibge-download-2010 \
		ibge-download-2022 \
		ingestion \
		go-lint go-test go-tidy \
		migrations-new migrations-up migrations-down migrations-status confirm \
		bronze-load \
		bronze-load-sigesguarda \
		bronze-load-ibge2010 \
		bronze-load-ibge2022

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

sigesguarda-check-update: ## Check if a newer SIGESGUARDA file is available without downloading
	cd $(PY_DIR) && $(PYTHON) src/ingestion/download_sigesguarda.py --check-only

sigesguarda-download: ## Download latest SIGESGUARDA data if updated 
	cd $(PY_DIR) && $(PYTHON) src/ingestion/download_sigesguarda.py

ibge-download-2010: ## Download IBGE 2010 data 
	cd $(PY_DIR) && $(PYTHON) src/ingestion/download_ibge_2010.py 

ibge-download-2022: ## Download IBGE 2022 data 
	cd $(PY_DIR) && $(PYTHON) src/ingestion/download_ibge_2022.py

ingestion: sigesguarda-download ibge-download-2010 ibge-download-2022 ## Run all ingestion scripts

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

bronze-load: ## Load all bronze CSV files into PostgreSQL 
	cd $(PY_DIR) && $(PYTHON) src/ingestion/load_raw_to_postgres.py --dsn "$(SIGESGUARDA_DB_DSN)"

bronze-load-sigesguarda: ## Load SIGESGUARDA bronze CSV files 
	cd $(PY_DIR) && $(PYTHON) src/ingestion/load_raw_to_postgres.py --source sigesguarda --dsn "$(SIGESGUARDA_DB_DSN)"

bronze-load-ibge2010: ## Load IBGE 2010 bronze CSV files
	cd $(PY_DIR) && $(PYTHON) src/ingestion/load_raw_to_postgres.py --source ibge2010 --dsn "$(SIGESGUARDA_DB_DSN)"

bronze-load-ibge2022: ## Load IBGE 2022 bronze CSV files 
	cd $(PY_DIR) && $(PYTHON) src/ingestion/load_raw_to_postgres.py --source ibge2022 --dsn "$(SIGESGUARDA_DB_DSN)"
