#!/usr/bin/env bash

set -e
set -x

export PYTHONPATH=$(pwd)

python app/db/backend_pre_start.py

alembic -c alembic.ini upgrade head

python app/db/initial_data.py