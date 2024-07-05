## Requirements

- Python
- Poetry
Or
- Devcontainer

```sh
poetry install
poetry shell
```

Create a fine-grained GitHub token with permissions for all repositories or some specific repositories with the following permissions:

- Contents (Read/Write)
- Issues (Read/Write) for labels
- Workflows (Read/Write) for GitHub actions

## Run

```sh
pulumi login --local
pulumi stack select <dev|prod>
export GITHUB_TOKEN=YYYYYYYYYYYYYY
pulumi up
```
