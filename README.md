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

- Administration (Read/Write)
- Contents (Read/Write)
- Issues (Read/Write) for labels
- Workflows (Read/Write) for GitHub actions

To prevents accidental deletion of Github repository, this ressource is marked as protected and require a manual deletion.

## Run

```sh
export GITHUB_TOKEN=YYYYYYYYYYYYYY
export PULUMI_CONFIG_PASSPHRASE=XXXXXXXXXXX
pulumi login --local
pulumi stack select <dev|prod>
pulumi up
```

### Refresh state
```sh
pulumi refresh
```

### Delete a ressource
```sh
pulumi state delete urn:XXXXXXXX
```