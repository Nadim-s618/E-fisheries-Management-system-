.PHONY: setup backend frontend migrate superuser test lint

PYTHON := .venv/bin/python

setup:
	./setup.sh

backend:
	cd backend && ../$(PYTHON) manage.py runserver

frontend:
	cd frontend && npm run dev

migrate:
	cd backend && ../$(PYTHON) manage.py migrate

superuser:
	cd backend && ../$(PYTHON) manage.py createsuperuser

test:
	cd backend && ../$(PYTHON) manage.py test

lint:
	cd frontend && npm run lint
