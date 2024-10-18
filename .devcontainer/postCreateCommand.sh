#!/bin/bash
uv sync
pulumi login file://~/pulumi-data
pulumi stack select dev