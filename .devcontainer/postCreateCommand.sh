#!/bin/bash

uv sync --all-extras

# nixos fix
# see https://github.com/microsoft/vscode-remote-release/issues/11024
git config --global gpg.program "/usr/bin/gpg"

pulumi login 's3://pulumi?region=eu-west-1&endpoint=https://nas.unicornafk.fr:30292&s3ForcePathStyle=true'

pulumi stack select dev