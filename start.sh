#!/bin/sh

sleep 10
uv run alembic upgrade head
uv run fastapi run