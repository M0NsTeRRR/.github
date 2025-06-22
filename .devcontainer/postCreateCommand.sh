#!/bin/bash

uv sync --all-extras

# nixos fix
# see https://github.com/microsoft/vscode-remote-release/issues/11024
git config --global gpg.program "/usr/bin/gpg"

pulumi login file://~/pulumi-data
pulumi stack select dev