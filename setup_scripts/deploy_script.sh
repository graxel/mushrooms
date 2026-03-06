#!/bin/bash
set -e

BRANCH="$GITHUB_REF_NAME"

# write .env to server
cat > .env << EOF
PG_HOST=$PG_HOST
PG_PASS=$PG_PASS
PG_PORT=$PG_PORT
PG_USER=$PG_USER
EOF
chmod 600 .env

uv sync
# uv run python migrate.py

# sudo cp nginx.conf /etc/nginx/sites-available/myapp
# sudo ln -sf /etc/nginx/sites-available/myapp /etc/nginx/sites-enabled/
# sudo nginx -t && sudo systemctl reload nginx

# sudo cp service_files/*.service /etc/systemd/system/
# sudo systemctl daemon-reload
# sudo systemctl restart myapp.service