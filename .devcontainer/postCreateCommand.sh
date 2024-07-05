#!/bin/bash
poetry shell
poetry install
pulumi login file://~/pulumi-data
pulumi stack select dev