#!/bin/bash
uv sync --all-extras
pulumi login file://~/pulumi-data
pulumi stack select dev