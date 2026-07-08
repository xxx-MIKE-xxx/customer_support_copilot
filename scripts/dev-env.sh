#!/usr/bin/env bash

# Find the repo root based on this script's location
export REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")/.." && pwd)"

# Useful project variables
export APP_ENV="development"
export PYTHONPATH="$REPO_ROOT:$PYTHONPATH"
export DATA_PATH="$REPO_ROOT/data"

# Activate Python virtual environment if it exists
if [ -f "$REPO_ROOT/venv/bin/activate" ]; then
  source "$REPO_ROOT/venv/bin/activate"
else
  echo "No venv found at $REPO_ROOT/venv"
  echo "Create one with: python3 -m venv venv"
fi

#change kagglehub download destination to data/ folder
export KAGGLEHUB_CACHE=$REPO_ROOT/data/raw

echo "Development environment loaded"
echo "REPO_ROOT=$REPO_ROOT"
echo "APP_ENV=$APP_ENV"
echo "Python: $(which python)"
echo "Kagglehub cache path: $KAGGLEHUB_CACHE"