## Requirements

- uv or devcontainer

Create a fine-grained GitHub token with permissions for all repositories or some specific repositories with the following permissions:

- Administration (Read/Write)
- Contents (Read/Write)
- Issues (Read/Write) for labels
- Workflows (Read/Write) for GitHub actionss

To prevents accidental deletion of Github repository, this ressource is marked as protected and require a manual deletion.

## Run

```sh
export GITHUB_TOKEN=YYYYYYYYYYYYYY
export PULUMI_CONFIG_PASSPHRASE=XXXXXXXXXXX
./pulumi.sh login --local
./pulumi.sh stack select <dev|prod>
./pulumi.sh refresh
./pulumi.sh up
```

### Delete a ressource

```sh
./pulumi.sh stack -u
./pulumi.sh state delete 'urn:XXXXXXXX'
```

# WIP

Pulumi doesn't support `uv` for now it's why we use a script for now.

It's currently not possible to set some repository settings

In `settings > actions`:  
    - `Fork pull request workflows from outside collaborators` must be set to `Require approval for all outside collaborators`  
    - In `Workflow permissions`, `Allow GitHub Actions to create and approve pull requests` must be ticked ([Github PR](https://github.com/integrations/terraform-provider-github/pull/2309))
