#!/usr/bin/env bash

set -e

APP_PATH="${FASTAPI_CONFIG_PATH:-app.conf}"

echo "➡️ Creating the configuration file"
if [ -e "$APP_PATH" ]; then
    echo "⚠️ Configuration file already exists. Skipping."
else
    cp app.conf.autopilot $APP_PATH
fi

echo "Start main process"
python -m app.main
