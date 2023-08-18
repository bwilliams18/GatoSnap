#!/bin/bash
set -euo pipefail
cd frontend
yarn build
cd ..
rm -r backend/static/*
mkdir -p backend/static
cp -r frontend/build/* backend/static/
cd backend
poetry run alembic upgrade head
