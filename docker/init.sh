#!/usr/bin/env bash

set -e

APP_PATH="${FASTAPI_CONFIG_PATH:-app.conf}"
APP_CONFIG_TEMPLATE_PATH="${APP_CONFIG_TEMPLATE_PATH:-app.conf.example}"

echo "➡️ Creating the configuration file"
if [ -e "$APP_PATH" ]; then
    echo "⚠️ Configuration file already exists. Skipping."
else
    cp "$APP_CONFIG_TEMPLATE_PATH" "$APP_PATH"

    ENCRYPTION_KEY="$(openssl rand -base64 32)"
    sed -i "s|^\(encryption_key=\).*|\1$ENCRYPTION_KEY|" "$APP_PATH"
fi

echo "Start main process"
python -m app.main
