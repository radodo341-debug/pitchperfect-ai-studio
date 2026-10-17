#!/bin/sh
set -eu
# Start the API first; checkpoint download runs asynchronously in the app so
# Render can bind its health-check port while the large model file is fetched.
exec python /app/main.py
