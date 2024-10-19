#!/bin/bash

# Source : https://github.com/bensi94
# https://github.com/pulumi/pulumi/issues/17031#issuecomment-2389822519

DIST="dist"

if [ ! -d "DIST" ]; then
    mkdir "$DIST"
fi

function create_virtualenv() {
  rm -rf dist/.venv
  uv run python -m venv dist/.venv
  source dist/.venv/bin/activate
  pip install -r dist/requirements.txt
}

NEW_REQUIREMENTS=$(uv export --no-hashes)

if [ -f "dist/requirements.txt" ]; then
  NEW_REQUIREMENTS_CHECKSUM=$(cksum <<< "$NEW_REQUIREMENTS" | cut -f 1 -d ' ')
  OLD_REQUIREMENTS_CHECKSUM=$(cksum <<< cat dist/requirements.txt | cut -f 1 -d ' ')

  if [ "$NEW_REQUIREMENTS_CHECKSUM" != "$OLD_REQUIREMENTS_CHECKSUM" ]; then
    echo "$NEW_REQUIREMENTS" > dist/requirements.txt
    create_virtualenv
  else
    source dist/.venv/bin/activate
  fi
else
    echo "$NEW_REQUIREMENTS" > dist/requirements.txt
    create_virtualenv
fi

pulumi "$@"