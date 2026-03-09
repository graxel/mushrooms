#!/bin/bash
set -e

# for uv
export PATH="$HOME/.local/bin:$PATH"

BRANCH="$GITHUB_REF_NAME"

# write .env to server
cat > .env << EOF
# === same for all envs ===
# postgres connection
PG_HOST=$PG_HOST
PG_PASS=$PG_PASS
PG_PORT=$PG_PORT
PG_USER=$PG_USER

# minio + mlflow connection
AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
MLFLOW_TRACKING_URI=$MLFLOW_TRACKING_URI
MLFLOW_S3_ENDPOINT_URL=$MLFLOW_S3_ENDPOINT_URL


# === vary by env ===
PG_DB=$PG_DB
DBT_TARGET=$DBT_TARGET

EOF
chmod 600 .env

uv sync --no-dev
uv run python prefect/flow.py

# sudo cp nginx.conf /etc/nginx/sites-available/myapp
# sudo ln -sf /etc/nginx/sites-available/myapp /etc/nginx/sites-enabled/
# sudo nginx -t && sudo systemctl reload nginx

# sudo cp service_files/*.service /etc/systemd/system/
# sudo systemctl daemon-reload
# sudo systemctl restart myapp.service