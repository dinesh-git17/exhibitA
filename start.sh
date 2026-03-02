#!/usr/bin/env bash
set -a
source /opt/exhibit-a/.env
set +a
exec /opt/exhibit-a/.venv/bin/python -m app
