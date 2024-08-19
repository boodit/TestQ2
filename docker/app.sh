#!/bin/bash

alembic upgrade head

gunicorn src.main:app --workers 3 --worker-class uvicorn.workers.UvicornH11Worker --bind 0.0.0.0:8000