#!/bin/bash
set -euo pipefail
cd frontend
yarn install
yarn build
cd ..
rm -r backend/static/*
mkdir -p backend/static
cp -r frontend/build/* backend/static/
cd backend
poetry install --only main
poetry run alembic upgrade head
