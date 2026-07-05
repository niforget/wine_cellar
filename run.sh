#!/usr/bin/env bash
set -e

# Le superviseur HA ecrit les options de l'add-on (definies dans
# config.yaml / configurees dans l'onglet Configuration) dans
# /data/options.json. On les relit ici sans dependre de bashio,
# pour rester compatible avec une image de base simple (python:slim).
if [ -f /data/options.json ]; then
  export ANTHROPIC_API_KEY=$(python3 -c "
import json
try:
    print(json.load(open('/data/options.json')).get('anthropic_api_key') or '')
except Exception:
    print('')
")
fi

export CAVE_DB_PATH="/data/cave_a_vin.sqlite"
export CAVE_PHOTOS_DIR="/data/photos"

cd /app
exec uvicorn main:app --host 0.0.0.0 --port 8000
